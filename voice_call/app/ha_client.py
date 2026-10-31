import os
import time
import requests
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings

_STATES_CACHE = None
_CACHE_TIMESTAMP = 0.0
_HOST_IP_CACHE: Optional[str] = None


class HAClient:
    def _get_api_targets(self) -> List[Tuple[str, str]]:
        """Trả về danh sách (base_url, token) để kết nối HA Core."""
        targets = []
        # 1. Supervisor API nội bộ (chuẩn Add-on)
        sup_token = settings.supervisor_token
        if sup_token:
            targets.append(("http://supervisor/core", sup_token))

        # 2. Custom Token nếu người dùng cấu hình trong Options của Add-on
        custom_tok = settings.custom_token
        if custom_tok:
            targets.append(("http://supervisor/core", custom_tok))
            targets.append(("http://172.30.32.1:8123", custom_tok))

        # 3. Fallback direct host
        if sup_token:
            targets.append(("http://172.30.32.1:8123", sup_token))

        return targets

    def get_ha_ip(self) -> str:
        """Lấy IP LAN của Home Assistant từ Supervisor."""
        global _HOST_IP_CACHE
        if _HOST_IP_CACHE:
            return _HOST_IP_CACHE

        token = settings.supervisor_token or settings.custom_token
        if token:
            try:
                r = requests.get(
                    "http://supervisor/network/info",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=3
                )
                if r.status_code == 200:
                    interfaces = r.json().get("data", {}).get("interfaces", [])
                    for iface in interfaces:
                        if iface.get("primary") and iface.get("ipv4", {}).get("address"):
                            addr = iface["ipv4"]["address"][0].split("/")[0]
                            _HOST_IP_CACHE = addr
                            return addr
            except Exception:
                pass

        return "homeassistant.local"

    def get_speakers(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        global _STATES_CACHE, _CACHE_TIMESTAMP
        now = time.time()
        if not force_refresh and _STATES_CACHE and (now - _CACHE_TIMESTAMP < 5.0):
            return _STATES_CACHE

        targets = self._get_api_targets()
        print(f"[HA_CLIENT] Đang lấy danh sách loa qua {len(targets)} cổng kết nối...")

        last_error = ""
        for base_url, token in targets:
            url = f"{base_url}/api/states"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            try:
                print(f"[HA_CLIENT] Gửi yêu cầu tới {url} (Token len: {len(token)})...")
                r = requests.get(url, headers=headers, timeout=8)
                print(f"[HA_CLIENT] Phản hồi từ {base_url}: HTTP {r.status_code}")

                if r.status_code == 200:
                    all_states = r.json()
                    speakers = []
                    for s in all_states:
                        eid = s.get("entity_id", "")
                        if not eid.startswith("media_player."):
                            continue
                        attrs = s.get("attributes", {})
                        name = attrs.get("friendly_name", eid)
                        state = s.get("state", "unknown")
                        is_cast = (
                            "google" in eid.lower() or
                            "cast" in eid.lower() or
                            "google" in name.lower() or
                            "harman" in name.lower() or
                            attrs.get("icon") == "hass:google" or
                            attrs.get("app_name") == "Default Media Receiver"
                        )
                        speakers.append({
                            "entity_id": eid,
                            "friendly_name": name,
                            "state": state,
                            "is_available": state != "unavailable",
                            "is_cast": is_cast,
                            "volume_level": attrs.get("volume_level")
                        })

                    speakers.sort(key=lambda x: (
                        0 if x["is_available"] else 1,
                        0 if x["is_cast"] else 1,
                        x["friendly_name"].lower()
                    ))
                    print(f"[HA_CLIENT] Tìm thấy thành công {len(speakers)} thiết bị media_player.")
                    _STATES_CACHE = speakers
                    _CACHE_TIMESTAMP = now
                    return speakers
                else:
                    last_error = f"HTTP {r.status_code}: {r.text[:150]}"
                    print(f"[HA_CLIENT ERROR] {last_error}")
            except Exception as e:
                last_error = str(e)
                print(f"[HA_CLIENT EXCEPTION] {e}")

        print(f"[HA_CLIENT] Không lấy được loa: {last_error}")
        return _STATES_CACHE or []

    def set_volume(self, entity_id: str, volume: float) -> bool:
        volume = max(0.05, min(float(volume), 1.0))
        for base_url, token in self._get_api_targets():
            try:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                r = requests.post(
                    f"{base_url}/api/services/media_player/volume_set",
                    headers=headers,
                    json={"entity_id": entity_id, "volume_level": volume},
                    timeout=5
                )
                if r.status_code == 200:
                    return True
            except Exception:
                pass
        return False

    def play_media(self, entity_id: str, session_id: str, fallback_host: Optional[str] = None) -> Tuple[bool, str]:
        # 1. Thử media-source URL
        media_source_url = f"media-source://media_source/local/voice_call/{session_id}.mp3"
        for base_url, token in self._get_api_targets():
            try:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                r = requests.post(
                    f"{base_url}/api/services/media_player/play_media",
                    headers=headers,
                    json={
                        "entity_id": entity_id,
                        "media_content_id": media_source_url,
                        "media_content_type": "audio/mpeg"
                    },
                    timeout=6
                )
                if r.status_code == 200:
                    return True, "Đã phát qua media-source."
            except Exception:
                pass

        # 2. Thử HTTP URL cổng 8098
        host_ip = fallback_host or self.get_ha_ip()
        http_url = f"http://{host_ip}:{settings.media_port}/audio/{session_id}.mp3"

        for base_url, token in self._get_api_targets():
            try:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                r = requests.post(
                    f"{base_url}/api/services/media_player/play_media",
                    headers=headers,
                    json={
                        "entity_id": entity_id,
                        "media_content_id": http_url,
                        "media_content_type": "audio/mpeg"
                    },
                    timeout=6
                )
                if r.status_code == 200:
                    return True, "Đã phát qua HTTP stream."
            except Exception:
                pass

        return False, "Không thể phát âm thanh qua loa"

    def stop_media(self, entity_id: str) -> Tuple[bool, str]:
        for base_url, token in self._get_api_targets():
            try:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                r = requests.post(
                    f"{base_url}/api/services/media_player/media_stop",
                    headers=headers,
                    json={"entity_id": entity_id},
                    timeout=5
                )
                if r.status_code == 200:
                    return True, "Đã dừng phát loa."
            except Exception:
                pass
        return False, "Không thể dừng loa"


ha_client = HAClient()
