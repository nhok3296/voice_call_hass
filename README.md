# Home Assistant Add-ons: Voice Call 📞

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Add--on-blue.svg)](https://www.home-assistant.io/)
[![Platform](https://img.shields.io/badge/Platform-amd64%20%7C%20aarch64%20%7C%20armv7-green.svg)](https://github.com/)

**Voice Call** là Add-on đàm thoại một chạm (Push-to-Talk) thông minh dành cho Home Assistant, cho phép bạn gọi và phát giọng nói qua các loa Google Cast (Google Home, Google Home Mini, Harman Kardon...) trực tiếp từ thanh Menu (Sidebar) của ứng dụng Home Assistant trên điện thoại.

---

## Tính Năng Nổi Bật

- 🎙️ **Đàm thoại một chạm (Push-to-Talk)**: Nhấn giữ để nói, thả tay để phát qua loa trong nhà.
- 📱 **Tích hợp sâu Home Assistant (Ingress)**: Xuất hiện trực tiếp trên Sidebar của App Home Assistant trên Android & iOS.
- 🔒 **Bảo mật và tiện lợi**: Kế thừa trực tiếp quyền HTTPS và Microphone từ Home Assistant, không cần cài chứng chỉ CA thủ công.
- ⚡ **Tự động nhận diện thiết bị**: Tự động lọc và hiển thị tất cả các loa Google Cast sẵn có trong nhà.
- 📻 **Chất lượng âm thanh tối ưu**: Chuyển đổi định dạng sang MP3 Mono tối ưu cho giọng nói rõ ràng và truyền tải tức thì.
- 🧹 **Tự động quản lý bộ nhớ**: Tự động dọn dẹp các file ghi âm cũ theo thời gian cấu hình.

---

## Hướng Dẫn Cài Đặt Cho Đại Chúng

### Cách 1: Thêm Repository vào Add-on Store (Khuyên dùng)
1. Trong Home Assistant, vào **Cài đặt (Settings)** > **Tiện ích mở rộng (Add-ons)** > Chọn **Cửa hàng Add-on (Add-on Store)**.
2. Nhấn vào dấu **3 chấm (`⋮`)** ở góc trên cùng bên phải > Chọn **Kho lưu trữ (Repositories)**.
3. Dán đường dẫn kho lưu trữ này vào và nhấn **Thêm (Add)**.
4. Tìm kiếm **Voice Call** trong danh sách > Nhấn **Cài đặt (Install)**.
5. Bật tùy chọn **Khởi động cùng hệ thống (Start on boot)** và **Hiển thị ở thanh bên (Show in sidebar)**.
6. Nhấn **Khởi chạy (Start)**.

### Cách 2: Cài đặt Cục bộ (Local Add-on)
1. Tải thư mục `voice_call` vào thư mục `/addons` của Home Assistant.
2. Vào **Add-on Store** > Chọn dấu 3 chấm > **Kiểm tra cập nhật (Check for updates)**.
3. Mục **Local add-ons** sẽ xuất hiện **Voice Call** > Nhấn **Cài đặt (Install)**.

---

## Cách Sử Dụng
1. Mở App Home Assistant trên điện thoại hoặc trình duyệt web.
2. Bấm vào mục **Voice Call** 📞 trên thanh Menu bên trái.
3. Chọn loa nhận cuộc gọi và chỉnh âm lượng mong muốn.
4. Nhấn giữ nút tròn Micro ở giữa để nói, sau khi nói xong chỉ cần thả tay ra là loa trong nhà sẽ phát ngay!
