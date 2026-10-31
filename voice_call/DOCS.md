# Tài liệu hướng dẫn sử dụng Add-on: Voice Call

## Giới thiệu
**Voice Call** là Add-on đàm thoại một chạm (Push-to-Talk) tích hợp trực tiếp vào thanh Menu của Home Assistant. Cho phép bạn nói chuyện qua loa Google Cast (Google Home, Google Home Mini, Harman Kardon...) từ điện thoại Android, iPhone hoặc máy tính.

---

## Tính năng
- **Tích hợp Ingress**: Hiện ngay trên thanh menu bên trái của Home Assistant.
- **Không cần cấu hình chứng chỉ SSL**: Kế thừa trực tiếp quyền bảo mật HTTPS và Micro của app Home Assistant.
- **Không cần nhập Token**: Sử dụng trực tiếp API nội bộ thông qua Supervisor.
- **Hỗ trợ mọi dòng loa Google Cast**: Tự động nhận diện loa trong nhà.
- **Tự động dọn dẹp**: Tự động xóa các bản ghi âm cũ sau khoảng thời gian cấu hình.

---

## Cấu hình (Tùy chọn)
Trong tab **Cấu hình (Configuration)** của Add-on:
- `audio_bitrate`: Chất lượng âm thanh MP3 (Mặc định `96k`).
- `max_record_seconds`: Thời gian ghi âm tối đa mỗi lần (Mặc định `120` giây).
- `retention_hours`: Thời gian lưu trữ file trước khi tự xóa (Mặc định `2` giờ).
- `default_volume`: Âm lượng phát loa mặc định (Mặc định `0.65` = 65%).

---

## Cách sử dụng
1. Bấm vào biểu tượng **Voice Call** 📞 ở menu bên trái.
2. Chọn loa muốn phát.
3. Chỉnh âm lượng mong muốn.
4. Nhấn giữ nút Micro để nói chuyện.
5. Thả nút ra là loa sẽ phát âm thanh ngay lập tức!

