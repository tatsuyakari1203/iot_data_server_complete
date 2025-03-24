# Ví dụ Socket.IO cho ESP8266/ESP32

Dưới đây là các ví dụ hoàn chỉnh để giúp bạn kết nối thiết bị ESP8266 hoặc ESP32 với máy chủ IoT Data Server qua Socket.IO.

## Ví dụ cơ bản với ESP8266

Ví dụ này gửi dữ liệu nhiệt độ giả lập mỗi 5 giây:

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
const char* socketIOHost = "192.168.1.100"; // Thay đổi thành địa chỉ IP máy chủ của bạn
const uint16_t socketIOPort = 5000;
const char* socketIOUrl = "/socket.io/?EIO=4";

// Thông tin thiết bị
const char* apiKey = "YOUR_API_KEY"; // Thay đổi bằng API key của bạn
const char* deviceName = "esp8266_sensor";
const char* topicName = "temperature";

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("Socket.IO Client Disconnected");
      break;
    case sIOtype_CONNECT:
      Serial.println("Socket.IO Client Connected");
      break;
    case sIOtype_EVENT:
      Serial.print("Socket.IO Got Event: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_ACK:
      Serial.print("Socket.IO Got ACK: ");
      Serial.println(length);
      break;
    case sIOtype_ERROR:
      Serial.print("Socket.IO Error: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_BINARY_EVENT:
      Serial.print("Socket.IO Binary Event: ");
      Serial.println(length);
      break;
    case sIOtype_BINARY_ACK:
      Serial.print("Socket.IO Binary ACK: ");
      Serial.println(length);
      break;
  }
}

void setup() {
  Serial.begin(115200);
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi ");
  Serial.print(ssid);
  Serial.print(" ");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Kết nối Socket.IO server
  socketIO.begin(socketIOHost, socketIOPort, socketIOUrl);
  socketIO.onEvent(socketIOEvent);
  
  Serial.println("Connecting to Socket.IO server...");
}

void sendSensorData() {
  // Đọc dữ liệu cảm biến (trong ví dụ này là nhiệt độ giả lập)
  float temperature = random(2000, 3000) / 100.0; // Nhiệt độ ngẫu nhiên từ 20°C đến 30°C
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = topicName;
  
  JsonObject data = payload.createNestedObject("payload");
  data["value"] = temperature;
  data["unit"] = "celsius";
  data["timestamp"] = millis();
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "telemetry" với dữ liệu
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.print("Sent temperature: ");
  Serial.print(temperature);
  Serial.println("°C via Socket.IO");
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

## Ví dụ với ESP32 và DHT22

Ví dụ này sử dụng ESP32 để đọc dữ liệu nhiệt độ và độ ẩm từ cảm biến DHT22 thực tế:

```cpp
#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <SocketIOclient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// Cấu hình cảm biến DHT
#define DHTPIN 4      // Chân GPIO kết nối với DHT22
#define DHTTYPE DHT22 // Loại cảm biến (DHT22)
DHT dht(DHTPIN, DHTTYPE);

// Thông tin WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Thông tin Socket.IO server
const char* socketIOHost = "192.168.1.100"; // Thay đổi thành địa chỉ IP máy chủ của bạn
const uint16_t socketIOPort = 5000;
const char* socketIOUrl = "/socket.io/?EIO=4";

// Thông tin thiết bị
const char* apiKey = "YOUR_API_KEY"; // Thay đổi bằng API key của bạn
const char* deviceName = "esp32_dht22";

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("Socket.IO Client Disconnected");
      break;
    case sIOtype_CONNECT:
      Serial.println("Socket.IO Client Connected");
      break;
    case sIOtype_EVENT:
      Serial.print("Socket.IO Got Event: ");
      Serial.println((char*)payload);
      
      // Xử lý phản hồi từ máy chủ
      handleResponse(payload);
      break;
    case sIOtype_ACK:
      Serial.print("Socket.IO Got ACK: ");
      Serial.println(length);
      break;
    case sIOtype_ERROR:
      Serial.print("Socket.IO Error: ");
      Serial.println((char*)payload);
      break;
    case sIOtype_BINARY_EVENT:
      Serial.print("Socket.IO Binary Event: ");
      Serial.println(length);
      break;
    case sIOtype_BINARY_ACK:
      Serial.print("Socket.IO Binary ACK: ");
      Serial.println(length);
      break;
  }
}

// Xử lý phản hồi từ máy chủ
void handleResponse(uint8_t * payload) {
  String payloadStr = (char*)payload;
  
  if (payloadStr.indexOf("\"response\"") > 0) {
    Serial.println("Server confirmed data was stored successfully");
  } 
  else if (payloadStr.indexOf("\"error\"") > 0) {
    Serial.println("Server reported an error with the data");
  }
}

void setup() {
  Serial.begin(115200);
  
  // Khởi tạo cảm biến DHT
  dht.begin();
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Kết nối Socket.IO server
  socketIO.begin(socketIOHost, socketIOPort, socketIOUrl);
  socketIO.onEvent(socketIOEvent);
  
  Serial.println("Connecting to Socket.IO server...");
}

void sendTemperatureData() {
  // Đọc nhiệt độ từ cảm biến DHT22
  float temperature = dht.readTemperature();
  
  // Kiểm tra xem có đọc được giá trị không
  if (isnan(temperature)) {
    Serial.println("Failed to read temperature from DHT sensor!");
    return;
  }
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = "temperature";
  
  JsonObject data = payload.createNestedObject("payload");
  data["value"] = temperature;
  data["unit"] = "celsius";
  data["timestamp"] = millis();
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "telemetry" với dữ liệu nhiệt độ
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.print("Sent temperature: ");
  Serial.print(temperature);
  Serial.println("°C via Socket.IO");
}

void sendHumidityData() {
  // Đọc độ ẩm từ cảm biến DHT22
  float humidity = dht.readHumidity();
  
  // Kiểm tra xem có đọc được giá trị không
  if (isnan(humidity)) {
    Serial.println("Failed to read humidity from DHT sensor!");
    return;
  }
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = "humidity";
  
  JsonObject data = payload.createNestedObject("payload");
  data["value"] = humidity;
  data["unit"] = "percent";
  data["timestamp"] = millis();
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "telemetry" với dữ liệu độ ẩm
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.print("Sent humidity: ");
  Serial.print(humidity);
  Serial.println("% via Socket.IO");
}

unsigned long previousMillis = 0;
const long interval = 10000; // Gửi dữ liệu mỗi 10 giây

void loop() {
  socketIO.loop();
  
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Gửi dữ liệu nếu đã kết nối WiFi
    if (WiFi.status() == WL_CONNECTED) {
      sendTemperatureData();
      delay(1000); // Chờ 1 giây
      sendHumidityData();
    }
  }
}
```

## Trạng thái kết nối và xử lý ngắt kết nối

Ví dụ này thêm xử lý tình trạng kết nối và kết nối lại tự động:

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
const char* socketIOHost = "192.168.1.100"; // Thay đổi thành địa chỉ IP máy chủ của bạn
const uint16_t socketIOPort = 5000;
const char* socketIOUrl = "/socket.io/?EIO=4";

// Thông tin thiết bị
const char* apiKey = "YOUR_API_KEY"; // Thay đổi bằng API key của bạn
const char* deviceName = "esp8266_sensor";
const char* topicName = "status";

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

// Biến trạng thái
bool socketConnected = false;
int failedAttempts = 0;
unsigned long lastReconnectAttempt = 0;

void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("Socket.IO Client Disconnected");
      socketConnected = false;
      break;
    case sIOtype_CONNECT:
      Serial.println("Socket.IO Client Connected");
      socketConnected = true;
      failedAttempts = 0;
      
      // Gửi thông báo trạng thái kết nối sau khi kết nối thành công
      sendStatusData("online");
      break;
    case sIOtype_EVENT:
      Serial.print("Socket.IO Got Event: ");
      Serial.println((char*)payload);
      break;
  }
}

void setup() {
  Serial.begin(115200);
  
  // Kết nối WiFi
  connectWiFi();

  // Kết nối Socket.IO server
  connectSocketIO();
}

void connectWiFi() {
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  // Chờ kết nối, tối đa 20 giây
  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && 
         millis() - startAttemptTime < 20000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("Connected! IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("Failed to connect to WiFi. Restarting...");
    ESP.restart();
  }
}

void connectSocketIO() {
  socketIO.begin(socketIOHost, socketIOPort, socketIOUrl);
  socketIO.onEvent(socketIOEvent);
  socketIO.setReconnectInterval(5000); // Kết nối lại sau 5 giây nếu mất kết nối
  
  Serial.println("Connecting to Socket.IO server...");
}

void sendStatusData(String status) {
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = topicName;
  
  JsonObject data = payload.createNestedObject("payload");
  data["status"] = status;
  data["ip"] = WiFi.localIP().toString();
  data["rssi"] = WiFi.RSSI(); // Cường độ tín hiệu WiFi
  data["uptime"] = millis() / 1000; // Thời gian hoạt động (giây)
  
  // Chuyển đổi thành chuỗi JSON
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện "telemetry" với dữ liệu
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.print("Sent status: ");
  Serial.println(status);
}

void checkConnections() {
  // Kiểm tra WiFi, kết nối lại nếu cần
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    connectWiFi();
  }
  
  // Kiểm tra nếu Socket.IO chưa kết nối và đã đủ thời gian thử lại
  if (!socketConnected && millis() - lastReconnectAttempt > 30000) {
    lastReconnectAttempt = millis();
    failedAttempts++;
    
    Serial.println("Attempting to reconnect to Socket.IO server...");
    connectSocketIO();
    
    // Khởi động lại ESP nếu không thể kết nối sau nhiều lần thử
    if (failedAttempts > 5) {
      Serial.println("Failed to connect to Socket.IO after 5 attempts. Restarting...");
      ESP.restart();
    }
  }
}

unsigned long previousStatusMillis = 0;
const long statusInterval = 60000; // Gửi trạng thái mỗi 60 giây

void loop() {
  socketIO.loop();
  
  // Kiểm tra kết nối
  checkConnections();
  
  // Gửi cập nhật trạng thái định kỳ
  unsigned long currentMillis = millis();
  if (socketConnected && currentMillis - previousStatusMillis >= statusInterval) {
    previousStatusMillis = currentMillis;
    sendStatusData("online");
  }
}
```

## Ghi chú triển khai

1. **Thay thế thông tin WiFi và Server**: Đảm bảo thay đổi thông tin WiFi, địa chỉ IP máy chủ và API key phù hợp với cấu hình của bạn.

2. **Tương thích ESP32**: Đối với ESP32, thay `ESP8266WiFi.h` bằng `WiFi.h`.

3. **Quản lý bộ nhớ**: Nếu gặp sự cố tràn bộ nhớ, hãy giảm kích thước `DynamicJsonDocument` (nếu payload của bạn nhỏ) hoặc sử dụng `SPIFFS` để lưu trữ dữ liệu tạm thời.

4. **Chứng chỉ SSL**: Nếu bạn muốn kết nối qua SSL (WSS), cần bổ sung xử lý chứng chỉ và thay đổi URL kết nối thành `wss://`.

5. **Tiết kiệm pin**: Để tiết kiệm pin, hãy cân nhắc đưa ESP vào trạng thái ngủ giữa các lần gửi dữ liệu. 