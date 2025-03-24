# Kết nối Socket.IO

Socket.IO là một thư viện JavaScript cho phép giao tiếp hai chiều thời gian thực giữa máy khách và máy chủ. Thư viện này hoạt động trên mọi nền tảng, trình duyệt hoặc thiết bị, và tập trung vào sự đáng tin cậy và tốc độ.

## Thông tin kết nối

| Thông số | Giá trị |
|---------|---------|
| Server URL | `ws://{{ request.host.split(':')[0] }}:5000/socket.io/` |
| Transport | WebSocket (mặc định), HTTP Long Polling (dự phòng) |
| Path | `/socket.io/` |

## Kết nối với ESP8266/ESP32

Để kết nối thiết bị ESP8266/ESP32 với máy chủ Socket.IO, bạn cần sử dụng thư viện WebSockets và SocketIOclient:

### Cài đặt thư viện

Trong Arduino IDE:
1. Mở **Sketch > Include Library > Manage Libraries**
2. Tìm kiếm "WebSockets" của Markus Sattler và cài đặt (đã bao gồm SocketIOclient)
3. Tìm kiếm "ArduinoJson" của Benoit Blanchon và cài đặt

### Khởi tạo kết nối

```cpp
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <SocketIOclient.h>
#include <ArduinoJson.h>

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

void setup() {
  Serial.begin(115200);
  
  // Kết nối WiFi
  WiFi.begin("YOUR_WIFI_SSID", "YOUR_WIFI_PASSWORD");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  
  // Đặt hàm callback xử lý sự kiện Socket.IO
  socketIO.onEvent(socketIOEvent);
  
  // Kết nối tới máy chủ Socket.IO
  socketIO.begin("your_server_ip", 5000, "/socket.io/?EIO=4");
}

void loop() {
  // Cần gọi hàm loop() liên tục để xử lý các sự kiện Socket.IO
  socketIO.loop();
}
```

### Đăng ký thiết bị

Sau khi kết nối thành công, bạn nên đăng ký thiết bị với server để cung cấp thông tin về khả năng của thiết bị:

```cpp
void registerDevice() {
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = "YOUR_API_KEY";
  payload["device"] = "esp32_device";
  payload["action"] = "register";
  payload["capabilities"] = "temperature,humidity,pressure,light";
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "device_register" với dữ liệu
  socketIO.sendEVENT("device_register", output.c_str());
  
  Serial.println("Sent device registration");
}

// Gọi hàm đăng ký sau khi kết nối thành công
void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_CONNECT:
      Serial.println("Socket.IO Client Connected");
      // Đăng ký thiết bị ngay sau khi kết nối thành công
      registerDevice();
      break;
    // Xử lý các sự kiện khác...
  }
}
```

### Xử lý sự kiện Socket.IO

```cpp
void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("Socket.IO Client Disconnected");
      break;
    case sIOtype_CONNECT:
      Serial.println("Socket.IO Client Connected");
      // Đăng ký nhận các sự kiện sau khi kết nối thành công
      registerDevice();
      break;
    case sIOtype_EVENT:
      Serial.print("Socket.IO Got Event: ");
      Serial.println((char*)payload);
      
      // Xử lý các sự kiện nhận được
      handleIncomingEvent(payload, length);
      break;
    case sIOtype_ACK:
      Serial.print("Socket.IO Got ACK: ");
      Serial.println(length);
      hexdump(payload, length);
      break;
    case sIOtype_ERROR:
      Serial.print("Socket.IO Error: ");
      Serial.println(length);
      hexdump(payload, length);
      break;
    case sIOtype_BINARY_EVENT:
      Serial.print("Socket.IO Binary Event: ");
      Serial.println(length);
      hexdump(payload, length);
      break;
    case sIOtype_BINARY_ACK:
      Serial.print("Socket.IO Binary ACK: ");
      Serial.println(length);
      hexdump(payload, length);
      break;
  }
}

// Hàm xử lý các sự kiện nhận được
void handleIncomingEvent(uint8_t * payload, size_t length) {
  // Kiểm tra nếu payload bắt đầu với ["response" hoặc ["error"
  String payloadStr = (char*)payload;
  
  if (payloadStr.indexOf("\"response\"") > 0) {
    Serial.println("Received success response");
    // Xử lý thành công
  } 
  else if (payloadStr.indexOf("\"error\"") > 0) {
    Serial.println("Received error response");
    // Xử lý lỗi
  }
  // Xử lý các lệnh từ server
  else if (payloadStr.indexOf("\"command\"") > 0) {
    Serial.println("Received command from server");
    // Phân tích và thực thi lệnh từ server
    parseCommand(payloadStr);
  }
}

// Hàm phân tích lệnh từ server
void parseCommand(String payload) {
  // Phân tích JSON bằng ArduinoJson
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, payload.substring(payload.indexOf('[')+1, payload.lastIndexOf(']')));
  
  // Kiểm tra xem có phải là lệnh
  JsonObject obj = doc[1]; // Lấy phần payload của sự kiện
  
  if (obj.containsKey("command")) {
    String cmd = obj["command"].as<String>();
    
    if (cmd == "restart") {
      Serial.println("Executing restart command...");
      ESP.restart();
    }
    else if (cmd == "status") {
      Serial.println("Sending status information...");
      // Gửi thông tin trạng thái
      sendStatusInfo();
    }
    // Thêm các lệnh khác tại đây
  }
}

// Hàm in ra debug hexdump
void hexdump(const void *mem, uint32_t len) {
  const uint8_t *src = (const uint8_t *) mem;
  Serial.print("HEXDUMP: ");
  for(uint32_t i = 0; i < len; i++) {
    Serial.printf("%02x ", *src);
    src++;
  }
  Serial.println();
}
```

### Gửi dữ liệu cảm biến theo cấu trúc chuẩn

Để gửi dữ liệu từ cảm biến lên server, sử dụng cấu trúc dữ liệu chuẩn với mảng measurements:

```cpp
void sendSensorData() {
  // Đọc dữ liệu từ cảm biến
  float temperature = 25.3; // Đọc từ cảm biến thực tế
  float humidity = 65.2;    // Đọc từ cảm biến thực tế
  
  // Lấy thời gian hiện tại
  unsigned long timestamp = millis();
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = "YOUR_API_KEY";
  payload["device"] = "esp32_device";
  payload["topic"] = "sensors"; // Topic chung cho tất cả cảm biến
  
  JsonObject data = payload.createNestedObject("payload");
  
  // Tạo mảng measurements
  JsonArray measurements = data.createNestedArray("measurements");
  
  // Thêm dữ liệu nhiệt độ
  JsonObject temp = measurements.createNestedObject();
  temp["value"] = temperature;
  temp["unit"] = "celsius";
  temp["type"] = "temperature";
  temp["timestamp"] = timestamp;
  
  // Thêm dữ liệu độ ẩm
  JsonObject hum = measurements.createNestedObject();
  hum["value"] = humidity;
  hum["unit"] = "percent";
  hum["type"] = "humidity";
  hum["timestamp"] = timestamp;
  
  // Thêm thông tin bổ sung
  data["source"] = "esp32_device";
  data["device_time"] = timestamp;
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "telemetry" với dữ liệu
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.println("Sent sensor data");
}
```

## Kiểm tra kết nối

Để kiểm tra xem thiết bị ESP đã kết nối thành công với máy chủ Socket.IO:

1. Khi kết nối thành công, bạn sẽ nhận được sự kiện `sIOtype_CONNECT`
2. Sau đó, bạn có thể gửi dữ liệu đến máy chủ

## Xử lý kết nối lại tự động

Socket.IO Client tự động xử lý việc kết nối lại nếu mất kết nối. Tuy nhiên, bạn có thể cấu hình thêm để tăng độ tin cậy:

```cpp
// Đặt thời gian ping (heartbeat)
socketIO.setReconnectInterval(5000); // Kết nối lại sau mỗi 5 giây nếu bị ngắt kết nối
```

## Giải quyết sự cố kết nối

Nếu bạn gặp vấn đề khi kết nối thiết bị ESP với máy chủ Socket.IO:

1. **Kiểm tra WiFi**: Đảm bảo thiết bị đã kết nối WiFi thành công
2. **Kiểm tra địa chỉ IP và cổng**: Xác nhận địa chỉ IP máy chủ và cổng là chính xác
3. **Kiểm tra tường lửa**: Đảm bảo cổng 5000 được mở nếu kết nối từ bên ngoài
4. **Bật chế độ debug**:
   ```cpp
   // Bật chế độ debug cho WebSockets
   #define WEBSOCKETS_DEBUG 1
   ```
5. **Kiểm tra phiên bản Socket.IO**: Đảm bảo URL kết nối phù hợp với phiên bản Socket.IO trên máy chủ 