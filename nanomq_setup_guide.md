# Hướng dẫn cài đặt và sử dụng NanoMQ

## Giới thiệu

NanoMQ là một MQTT broker nhẹ, hiệu suất cao và có thể mở rộng, phù hợp cho các ứng dụng IoT và edge computing. Tài liệu này hướng dẫn cách cài đặt và cấu hình NanoMQ cho IoT Data Server.

## Các bước cài đặt

### 1. Thiết lập cấu trúc thư mục

Cấu trúc thư mục cho NanoMQ đã được tạo tự động:
```
nanomq/
├── etc/            # Thư mục cấu hình
│   └── nanomq.conf # File cấu hình chính
├── data/           # Dữ liệu lưu trữ
└── log/            # Log files
```

### 2. Khởi động NanoMQ với Docker Compose

Để khởi động NanoMQ, chạy lệnh sau trong thư mục gốc của dự án:

```bash
docker-compose up -d
```

Điều này sẽ khởi động NanoMQ trong chế độ nền. Để xem logs:

```bash
docker-compose logs -f nanomq
```

### 3. Kiểm tra trạng thái NanoMQ

Để kiểm tra xem NanoMQ đã hoạt động chưa:

```bash
docker-compose ps
```

## Cấu hình NanoMQ

### Cấu hình cơ bản

File cấu hình chính của NanoMQ nằm tại `nanomq/etc/nanomq.conf`. Cấu hình cơ bản đã được thiết lập với:

- MQTT Broker chạy trên cổng 1883
- WebSocket trên cổng 8083
- MQTT over TLS trên cổng 8883 (đã tắt mặc định)
- HTTP API trên cổng 8081

### Cấu hình xác thực

Mặc định, NanoMQ được cấu hình để cho phép kết nối ẩn danh. Để bật xác thực người dùng trong môi trường sản xuất:

1. Chỉnh sửa file `nanomq/etc/nanomq.conf`:
   ```
   auth.allow_anonymous=false
   auth.user=username1:password1,username2:password2
   ```

2. Cập nhật biến môi trường trong file `.env`:
   ```
   MQTT_USERNAME=username1
   MQTT_PASSWORD=password1
   ```

3. Khởi động lại NanoMQ:
   ```bash
   docker-compose restart nanomq
   ```

### Cấu hình TLS (Bảo mật)

Để bật TLS cho kết nối MQTT an toàn:

1. Tạo thư mục cho chứng chỉ:
   ```bash
   mkdir -p nanomq/etc/certs
   ```

2. Tạo chứng chỉ tự ký (hoặc sử dụng chứng chỉ của bạn):
   ```bash
   openssl genrsa -out nanomq/etc/certs/server.key 2048
   openssl req -new -x509 -key nanomq/etc/certs/server.key -out nanomq/etc/certs/server.crt -days 3650
   ```

3. Cập nhật cấu hình trong `nanomq/etc/nanomq.conf`:
   ```
   tls.enable=true
   tls.key_file=/etc/nanomq/certs/server.key
   tls.cert_file=/etc/nanomq/certs/server.crt
   ```

4. Khởi động lại NanoMQ:
   ```bash
   docker-compose restart nanomq
   ```

## Kết nối với NanoMQ

### Thông số kết nối

| Parameter | Value |
|-----------|-------|
| Broker Host | Địa chỉ IP máy chủ hoặc `localhost` |
| Broker Port | `1883` (MQTT), `8083` (WebSocket), hoặc `8883` (MQTT over TLS) |

### Ví dụ kết nối với Python

```python
import paho.mqtt.client as mqtt

# Callback khi kết nối thành công
def on_connect(client, userdata, flags, rc):
    print(f"Đã kết nối với mã kết quả {rc}")
    # Đăng ký nhận thông báo
    client.subscribe("my_device/temperature")

# Callback khi nhận được thông báo
def on_message(client, userdata, msg):
    print(f"Nhận thông báo từ {msg.topic}: {msg.payload.decode()}")

# Tạo client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Cấu hình xác thực (nếu cần)
# client.username_pw_set("username", "password")

# Kết nối đến broker
client.connect("localhost", 1883, 60)

# Gửi dữ liệu
client.publish("my_device/temperature", '{"temperature": 25.5, "api_key": "your_api_key"}')

# Bắt đầu vòng lặp
client.loop_forever()
```

## Giám sát và quản lý

### Sử dụng HTTP API

NanoMQ cung cấp HTTP API trên cổng 8081 để giám sát và quản lý:

- Kiểm tra trạng thái: `http://localhost:8081/api/v1/status`
- Xem danh sách clients: `http://localhost:8081/api/v1/clients`
- Xem các chủ đề: `http://localhost:8081/api/v1/topics`

## Khắc phục sự cố

### Lỗi kết nối

1. Kiểm tra xem NanoMQ có đang chạy không:
   ```bash
   docker-compose ps
   ```

2. Kiểm tra log:
   ```bash
   docker-compose logs nanomq
   ```

3. Kiểm tra cấu hình mạng:
   ```bash
   docker-compose exec nanomq netstat -tulpn
   ```

### Restart NanoMQ

Nếu bạn cần khởi động lại NanoMQ:
```bash
docker-compose restart nanomq
```

### Reset toàn bộ dữ liệu

Nếu bạn cần xóa dữ liệu và cài đặt lại:
```bash
docker-compose down
rm -rf nanomq/data/*
docker-compose up -d
```
