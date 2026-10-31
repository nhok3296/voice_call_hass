#!/usr/bin/env sh
set -e

echo "=========================================================="
echo "          VOICE CALL - SMART HOME VOICE TALK              "
echo "=========================================================="

# Đảm bảo thư mục lưu trữ media tồn tại
mkdir -p /media/voice_call || true
mkdir -p /data/recordings || true

echo "Khởi chạy Voice Call Add-on..."
exec python3 -m app.main_addon

