# Socket.IO API

Socket.IO cung cấp phương thức kết nối hai chiều, thời gian thực giữa thiết bị ESP và máy chủ, cho phép trao đổi dữ liệu nhanh hơn và hiệu quả hơn so với HTTP REST API.

## Kết nối Socket.IO

Để kết nối với Socket.IO server, sử dụng các thông số sau:

| Tham số | Giá trị |
|---------|---------|
| Server URL | `ws://{{ request.host.split(':')[0] }}:5000/socket.io/` |
| Transport | WebSocket |

## Gửi dữ liệu Telemetry

Để gửi dữ liệu từ ESP8266/ESP32 lên máy chủ qua Socket.IO:

1. Kết nối với máy chủ Socket.IO
2. Gửi sự kiện `telemetry` với dữ liệu theo định dạng JSON

### Định dạng Payload

Server hỗ trợ hai định dạng gửi dữ liệu:

#### 1. Định dạng chuẩn với mảng measurements (Khuyến nghị)

```json
{
  "api_key": "YOUR_API_KEY",
  "device": "device_name",
  "topic": "topic_name",
  "payload": {
    "measurements": [
      {
        "value": 25.3,
        "unit": "celsius",
        "type": "temperature",
        "timestamp": 1742593818.614071
      },
      {
        "value": 65.2,
        "unit": "percent",
        "type": "humidity",
        "timestamp": 1742593818.614071
      }
    ],
    "source": "esp32_device",
    "device_time": 1742593818.614071
  }
}
```

#### 2. Định dạng đơn giản (Hỗ trợ khả năng tương thích)

```json
{
  "api_key": "YOUR_API_KEY",
  "device": "device_name",
  "topic": "topic_name",
  "payload": {
    "value": 25.3,
    "unit": "celsius",
    "timestamp": 1742593818.614071,
    ... other data fields ...
  }
}
```

### Các trường bắt buộc

| Trường | Mô tả |
|--------|-------|
| `api_key` | API key của client để xác thực |
| `device` | Tên thiết bị gửi dữ liệu |
| `topic` | Tên chủ đề (topic) |
| `payload` | Dữ liệu cảm biến/thiết bị dạng JSON |

### Cấu trúc measurement chuẩn

| Trường | Mô tả | Ví dụ |
|--------|-------|-------|
| `value` | Giá trị đo được | `25.3` |
| `unit` | Đơn vị đo | `"celsius"`, `"percent"`, `"hPa"`, `"lux"` |
| `type` | Loại dữ liệu | `"temperature"`, `"humidity"`, `"pressure"`, `"light"` |
| `timestamp` | Thời điểm đo (Unix timestamp) | `1742593818.614071` |

### Phương thức gửi dữ liệu

Server hỗ trợ hai phương thức gửi dữ liệu từ thiết bị:

1. **Phương thức gộp**: Gửi tất cả dữ liệu cảm biến trong một payload (mảng measurements) lên một topic (ví dụ: "sensors")
2. **Phương thức riêng biệt**: Gửi từng loại dữ liệu lên các topic riêng biệt (ví dụ: "temperature", "humidity", v.v.)

### Sự kiện phản hồi

Sau khi gửi dữ liệu, máy chủ sẽ trả về một trong hai sự kiện sau:

- Sự kiện `response` khi thành công:
  ```json
  {
    "status": "success",
    "message": "Dữ liệu đã được lưu trữ thành công"
  }
  ```

- Sự kiện `error` khi có lỗi:
  ```json
  {
    "status": "error",
    "message": "Thông báo lỗi cụ thể"
  }
  ```

## Ví dụ với ESP8266/ESP32

Dưới đây là ví dụ sử dụng thư viện WebSockets và ArduinoJson cho ESP8266/ESP32:

```cpp
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <SocketIOclient.h>
#include <ArduinoJson.h>

// Thông tin WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Thông tin Socket.IO server
const char* socketIOHost = "your_server_ip";
const uint16_t socketIOPort = 5000;
const char* socketIOUrl = "/socket.io/?EIO=4";

// Thông tin thiết bị
const char* apiKey = "YOUR_API_KEY";
const char* deviceName = "esp8266_device";
const char* topicName = "sensors";

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

// Hàm xử lý sự kiện Socket.IO
void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("[Socket.IO] Disconnected");
      break;
    case sIOtype_CONNECT:
      Serial.println("[Socket.IO] Connected");
      break;
    case sIOtype_EVENT:
      // Xử lý các sự kiện nhận được
      Serial.print("[Socket.IO] Event: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_ACK:
      Serial.print("[Socket.IO] ACK: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_ERROR:
      Serial.print("[Socket.IO] Error: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_BINARY_EVENT:
      Serial.println("[Socket.IO] Binary Event");
      break;
    case sIOtype_BINARY_ACK:
      Serial.println("[Socket.IO] Binary ACK");
      break;
  }
}

void setup() {
  Serial.begin(115200);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Kết nối Socket.IO server
  socketIO.begin(socketIOHost, socketIOPort, socketIOUrl);
  socketIO.onEvent(socketIOEvent);
}

void sendSensorData() {
  // Đọc dữ liệu cảm biến (ví dụ với cảm biến nhiệt độ và độ ẩm)
  float temperature = 25.5; // Thay bằng giá trị đọc từ cảm biến thực tế
  float humidity = 65.2;    // Thay bằng giá trị đọc từ cảm biến thực tế
  
  // Thời gian hiện tại
  unsigned long timestamp = millis();
  
  // Tạo JSON payload với cấu trúc chuẩn
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = topicName;
  
  JsonObject data = payload.createNestedObject("payload");
  
  // Tạo mảng measurements
  JsonArray measurements = data.createNestedArray("measurements");
  
  // Thêm đo nhiệt độ
  JsonObject temp = measurements.createNestedObject();
  temp["value"] = temperature;
  temp["unit"] = "celsius";
  temp["type"] = "temperature";
  temp["timestamp"] = timestamp;
  
  // Thêm đo độ ẩm
  JsonObject hum = measurements.createNestedObject();
  hum["value"] = humidity;
  hum["unit"] = "percent";
  hum["type"] = "humidity";
  hum["timestamp"] = timestamp;
  
  // Thêm thông tin bổ sung
  data["source"] = deviceName;
  data["device_time"] = timestamp;
  
  // Chuyển JSON thành string
  String output;
  serializeJson(doc, output);
  
  // Gửi event "telemetry" với dữ liệu
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.println("Sent sensor data via Socket.IO");
}

unsigned long previousMillis = 0;
const long interval = 5000; // Gửi dữ liệu mỗi 5 giây

void loop() {
  socketIO.loop();
  
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Gửi dữ liệu nếu đã kết nối WiFi
    if (WiFi.status() == WL_CONNECTED) {
      sendSensorData();
    }
  }
}
```

### Yêu cầu thư viện

Để sử dụng ví dụ trên, bạn cần cài đặt các thư viện sau:

1. **WebSockets** bởi Markus Sattler (tìm trong Quản lý thư viện của Arduino IDE)
2. **SocketIOclient** (đi kèm với thư viện WebSockets)
3. **ArduinoJson** bởi Benoit Blanchon

## So sánh với các phương thức khác

| Tính năng | Socket.IO | MQTT | HTTP REST API |
|-----------|-----------|------|--------------|
| Hai chiều | ✓ | ✓ | ✗ |
| Sử dụng ít tài nguyên | ✓ | ✓ | ✗ |
| Hỗ trợ QoS | ✗ | ✓ | ✗ |
| Dễ triển khai | ✓ | ✓ | ✓ |
| Tương thích tường lửa | ✓ | ✗ | ✓ |
| Kết nối liên tục | ✓ | ✓ | ✗ |

## Lưu ý

- Socket.IO tự động xử lý kết nối lại nếu mất kết nối
- Đảm bảo bộ nhớ ESP đủ để xử lý các thư viện WebSockets và ArduinoJson
- Đối với các mạng có tường lửa hạn chế, Socket.IO có thể dự phòng xuống HTTP Long Polling 