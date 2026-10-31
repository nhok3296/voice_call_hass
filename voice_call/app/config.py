import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Đọc cấu hình từ Home Assistant Add-on
OPTIONS_PATH = Path("/data/options.json")


def get_addon_options():
    if OPTIONS_PATH.exists():
        try:
            return json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


# Thư mục lưu file ghi âm
MEDIA_DIR = Path("/media/voice_call")
if not MEDIA_DIR.exists():
    try:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        MEDIA_DIR = BASE_DIR / "storage" / "recordings"
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)

WEB_DIR = BASE_DIR / "web"


class Settings:
    @property
    def ha_url(self) -> str:
        return "http://supervisor/core"

    @property
    def supervisor_token(self) -> str:
        return os.getenv("SUPERVISOR_TOKEN", "")

    @property
    def custom_token(self) -> str:
        return get_addon_options().get("ha_token", "").strip()

    @property
    def ingress_port(self) -> int:
        return int(os.getenv("INGRESS_PORT", "8099"))

    @property
    def media_port(self) -> int:
        return int(os.getenv("MEDIA_PORT", "8098"))

    @property
    def audio_bitrate(self) -> str:
        return get_addon_options().get("audio_bitrate", "96k")

    @property
    def max_record_seconds(self) -> int:
        return int(get_addon_options().get("max_record_seconds", 120))

    @property
    def retention_hours(self) -> int:
        return int(get_addon_options().get("retention_hours", 2))

    @property
    def default_volume(self) -> float:
        return float(get_addon_options().get("default_volume", 0.65))


settings = Settings()
