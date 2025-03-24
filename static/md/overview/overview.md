# Tổng quan

IoT Data Server cung cấp ba phương thức để gửi dữ liệu từ thiết bị IoT tới máy chủ:

1. **MQTT Protocol** - Giao thức nhẹ, tiết kiệm năng lượng, phù hợp với các thiết bị IoT
2. **HTTP REST API** - Dễ sử dụng, tương thích rộng rãi với nhiều nền tảng
3. **Socket.IO API** - Giao tiếp hai chiều real-time, lý tưởng cho ứng dụng cần phản hồi nhanh và tương tác trực tiếp với thiết bị ESP

Tất cả các phương thức đều yêu cầu API key để xác thực yêu cầu. API key được tạo khi bạn đăng ký client mới trong hệ thống và phải được đính kèm trong mọi yêu cầu.

> **Lưu ý:** Trong môi trường sản xuất, hãy đảm bảo giao tiếp qua HTTPS, WSS hoặc sử dụng MQTT với TLS để bảo vệ API key của bạn.

## So sánh các phương thức kết nối

| Tính năng | MQTT | HTTP REST API | Socket.IO |
|-----------|------|--------------|-----------|
| Tiết kiệm băng thông | ✅ Cao | ❌ Thấp | ✅ Trung bình |
| Tiết kiệm pin | ✅ Cao | ❌ Thấp | ✅ Trung bình |
| Kết nối liên tục | ✅ Có | ❌ Không | ✅ Có |
| Giao tiếp hai chiều | ✅ Có | ❌ Không | ✅ Có |
| Độ phức tạp triển khai | ⚠️ Trung bình | ✅ Đơn giản | ⚠️ Trung bình |
| Hoạt động qua tường lửa | ⚠️ Có thể bị chặn | ✅ Thường được cho phép | ✅ Thay thế xuống HTTP nếu bị chặn |
| Phù hợp nhất với | Thiết bị IoT pin thấp, cần tối ưu hóa | Tích hợp đơn giản, gửi dữ liệu không thường xuyên | Ứng dụng cần phản hồi thời gian thực, ESP8266/ESP32 |
