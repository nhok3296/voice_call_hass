import uuid
import threading
from pathlib import Path
from typing import Annotated, Optional
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, MEDIA_DIR, WEB_DIR
from app.ha_client import ha_client
from app.audio_service import convert_audio_to_mp3, cleanup_old_recordings

# 1. Ingress Web App (Port 8099)
app = FastAPI(title="Voice Call", description="Smart Home Voice Communication Add-on")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[REQ] {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"[RES] {request.method} {request.url.path} -> {response.status_code}")
    return response


# Static files
app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(WEB_DIR / "js")), name="js")


@app.get("/", response_class=HTMLResponse)
@app.get("/{full_path:path}/", response_class=HTMLResponse)
def index_page():
    return HTMLResponse((WEB_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/health")
def health():
    ha_ok, ha_msg = ha_client.test_connection()
    return {
        "ok": True,
        "name": "Voice Call",
        "home_assistant": {"connected": ha_ok, "message": ha_msg},
        "media_dir": str(MEDIA_DIR)
    }


# Luôn trả về 200 JSON để Cloudflare không bao giờ chặn bằng trang lỗi HTML
@app.get("/api/speakers")
@app.get("/{prefix:path}/api/speakers")
def get_speakers():
    try:
        speakers = ha_client.get_speakers(force_refresh=True)
        return {"ok": True, "speakers": speakers}
    except Exception as e:
        print(f"[API ERROR] get_speakers: {e}")
        return {"ok": False, "speakers": [], "error": str(e)}


@app.post("/api/talk")
@app.post("/{prefix:path}/api/talk")
async def talk(
    request: Request,
    speaker: Annotated[str, Form(...)],
    audio: UploadFile = File(...),
    volume: Annotated[float, Form()] = 0.65,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not speaker.startswith("media_player."):
        raise HTTPException(400, "Entity ID loa không hợp lệ.")

    session_id = uuid.uuid4().hex
    raw_path = MEDIA_DIR / f"{session_id}.raw"
    mp3_path = MEDIA_DIR / f"{session_id}.mp3"

    try:
        # Ghi file tạm
        with raw_path.open("wb") as out:
            while True:
                chunk = await audio.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)

        # Chuyển đổi sang MP3
        ok, err = await convert_audio_to_mp3(raw_path, mp3_path)
        if not ok:
            raise HTTPException(422, f"Lỗi chuyển đổi âm thanh: {err}")

        # Chỉnh âm lượng loa
        ha_client.set_volume(speaker, volume)

        # Lấy host IP từ header request nếu có
        host_header = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
        fallback_host = host_header.split(":")[0] if host_header else None

        # Ra lệnh HA phát âm thanh
        play_ok, play_msg = ha_client.play_media(speaker, session_id, fallback_host=fallback_host)
        if not play_ok:
            raise HTTPException(502, f"Không thể phát loa: {play_msg}")

        # Lên lịch dọn dẹp file cũ
        background_tasks.add_task(cleanup_old_recordings)

        return {
            "ok": True,
            "message": "Đã phát qua loa thành công.",
            "session_id": session_id,
            "speaker": speaker
        }
    finally:
        raw_path.unlink(missing_ok=True)
        await audio.close()


@app.post("/api/speakers/{speaker_id}/stop")
@app.post("/{prefix:path}/api/speakers/{speaker_id}/stop")
def stop_speaker(speaker_id: str):
    ha_client.stop_media(speaker_id)
    return {"ok": True, "message": "Đã dừng loa."}


# 2. HTTP Media Server cho Google Cast (Port 8098)
media_app = FastAPI(title="Voice Call Media Relay")


@media_app.get("/audio/{filename}")
def serve_audio(filename: str):
    clean_name = Path(filename).name
    file_path = MEDIA_DIR / clean_name
    if not file_path.is_file() or not clean_name.endswith(".mp3"):
        raise HTTPException(404, "Không tìm thấy file âm thanh")
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        headers={"Accept-Ranges": "bytes", "Access-Control-Allow-Origin": "*"}
    )


def start_media_server():
    uvicorn.run(media_app, host="0.0.0.0", port=settings.media_port, log_level="warning")


def main():
    threading.Thread(target=start_media_server, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=settings.ingress_port, log_level="info")


if __name__ == "__main__":
    main()
