import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple
from app.config import settings, MEDIA_DIR


async def convert_audio_to_mp3(input_path: Path, output_path: Path) -> Tuple[bool, str]:
    """Chuyển đổi file WebM/Ogg từ trình duyệt sang MP3 Mono tối ưu cho Google Cast."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-vn", "-ac", "1",
        "-ar", "24000",
        "-b:a", settings.audio_bitrate,
        "-t", str(settings.max_record_seconds),
        str(output_path)
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=settings.max_record_seconds + 20)
        if proc.returncode != 0 or not output_path.exists():
            return False, stderr_data.decode("utf-8", errors="replace")[-300:] or "Lỗi xử lý FFmpeg"
        return True, ""
    except Exception as e:
        return False, str(e)


def cleanup_old_recordings():
    """Tự động xóa các file ghi âm cũ sau khoảng thời gian cấu hình."""
    cutoff = datetime.now(timezone.utc).timestamp() - (settings.retention_hours * 3600)
    for f in MEDIA_DIR.glob("*.mp3"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except OSError:
            pass

