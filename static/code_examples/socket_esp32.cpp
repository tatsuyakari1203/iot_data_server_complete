/**
 * IoT Data Server - ESP32 Socket.IO Example
 * 
 * Mã nguồn ví dụ kết nối ESP32 với IoT Data Server sử dụng Socket.IO
 * và gửi dữ liệu cảm biến theo cấu trúc chuẩn với mảng measurements.
 * 
 * Yêu cầu thư viện:
 * - ArduinoJson: https://github.com/bblanchon/ArduinoJson
 * - WebSockets: https://github.com/Links2004/arduinoWebSockets
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <SocketIOclient.h>
#include <ArduinoJson.h>

// Thông tin WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Thông tin Socket.IO server
const char* socketIOHost = "your_server_ip"; // Địa chỉ IP server
const uint16_t socketIOPort = 5000;          // Cổng server Socket.IO
const char* socketIOUrl = "/socket.io/?EIO=4";

// Thông tin thiết bị
const char* apiKey = "YOUR_API_KEY";   // API key xác thực
const char* deviceName = "esp32_device"; // Tên thiết bị
const char* sensorsTopic = "sensors";    // Topic chung cho tất cả cảm biến

// Khởi tạo client Socket.IO
SocketIOclient socketIO;

// Biến trạng thái
bool isConnected = false;
bool isRegistered = false;

// Hàm xử lý sự kiện Socket.IO
void socketIOEvent(socketIOmessageType_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case sIOtype_DISCONNECT:
      Serial.println("[Socket.IO] Disconnected");
      isConnected = false;
      isRegistered = false;
      break;
    
    case sIOtype_CONNECT:
      Serial.println("[Socket.IO] Connected");
      isConnected = true;
      
      // Đăng ký thiết bị sau khi kết nối
      registerDevice();
      break;
    
    case sIOtype_EVENT:
      Serial.print("[Socket.IO] Event: ");
      Serial.println((char*)payload);
      
      // Xử lý các sự kiện từ server
      handleServerEvent(payload, length);
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
      Serial.print("[Socket.IO] Binary Event: ");
      Serial.println(length);
      break;
    
    case sIOtype_BINARY_ACK:
      Serial.print("[Socket.IO] Binary ACK: ");
      Serial.println(length);
      break;
  }
}

// Xử lý sự kiện từ server
void handleServerEvent(uint8_t * payload, size_t length) {
  // Chuyển payload thành chuỗi để phân tích
  String payloadStr = (char*)payload;
  
  // Kiểm tra loại sự kiện
  if (payloadStr.indexOf("\"response\"") > 0) {
    Serial.println("Received success response");
    
    // Xử lý sự kiện đăng ký
    if (payloadStr.indexOf("\"device registered\"") > 0) {
      isRegistered = true;
      Serial.println("Device registration confirmed by server");
    }
  } 
  else if (payloadStr.indexOf("\"error\"") > 0) {
    Serial.println("Received error response");
    
    // Xử lý lỗi đăng ký thiết bị
    if (payloadStr.indexOf("\"invalid api key\"") > 0) {
      Serial.println("ERROR: Invalid API key");
    }
  }
  else if (payloadStr.indexOf("\"command\"") > 0) {
    Serial.println("Received command from server");
    handleCommand(payloadStr);
  }
}

// Xử lý lệnh từ server
void handleCommand(String payload) {
  // Phân tích JSON
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, payload.substring(payload.indexOf('[')+1, payload.lastIndexOf(']')));
  
  // Lấy đối tượng dữ liệu
  JsonObject obj = doc[1]; // Format: ["event_name", {data}]
  
  if (obj.containsKey("command")) {
    String command = obj["command"].as<String>();
    
    if (command == "restart") {
      Serial.println("Executing restart command from server");
      delay(1000);
      ESP.restart();
    }
    else if (command == "status") {
      Serial.println("Sending status information to server");
      sendStatusData();
    }
    else if (command == "set_interval") {
      if (obj.containsKey("value")) {
        long newInterval = obj["value"].as<long>();
        if (newInterval >= 1000) {
          Serial.print("Setting new send interval: ");
          Serial.println(newInterval);
          // Set new interval logic here
        }
      }
    }
  }
}

// Đăng ký thiết bị với server
void registerDevice() {
  Serial.println("Registering device with server...");
  
  // Tạo JSON payload cho đăng ký
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["action"] = "register";
  payload["capabilities"] = "temperature,humidity,pressure,light";
  
  // Chuyển JSON thành chuỗi
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện đăng ký
  socketIO.sendEVENT("device_register", output.c_str());
}

// Gửi dữ liệu trạng thái thiết bị
void sendStatusData() {
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = "status";
  
  JsonObject data = payload.createNestedObject("payload");
  data["ip"] = WiFi.localIP().toString();
  data["rssi"] = WiFi.RSSI();
  data["uptime"] = millis() / 1000;
  data["free_heap"] = ESP.getFreeHeap();
  data["timestamp"] = millis();
  
  // Chuyển JSON thành chuỗi
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện telemetry
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.println("Sent status data");
}

// Tạo cấu trúc đo lường chuẩn
JsonObject createMeasurement(JsonArray& array, float value, const char* unit, const char* type, unsigned long timestamp) {
  JsonObject measurement = array.createNestedObject();
  measurement["value"] = value;
  measurement["unit"] = unit;
  measurement["type"] = type;
  measurement["timestamp"] = timestamp;
  return measurement;
}

// Gửi dữ liệu tất cả cảm biến trong một payload (phương thức gộp)
void sendCombinedSensorData() {
  // Giả lập dữ liệu cảm biến (thay bằng dữ liệu thực tế trong ứng dụng của bạn)
  float temperature = random(2000, 3000) / 100.0; // 20.00-30.00
  float humidity = random(4000, 8000) / 100.0;    // 40.00-80.00
  float pressure = random(9800, 10200) / 10.0;    // 980.0-1020.0
  float light = random(0, 1000);                  // 0-1000
  
  // Thời gian hiện tại (sử dụng cho tất cả các phép đo)
  unsigned long timestamp = millis();
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = sensorsTopic;
  
  JsonObject data = payload.createNestedObject("payload");
  
  // Tạo mảng measurements
  JsonArray measurements = data.createNestedArray("measurements");
  
  // Thêm từng loại dữ liệu
  createMeasurement(measurements, temperature, "celsius", "temperature", timestamp);
  createMeasurement(measurements, humidity, "percent", "humidity", timestamp);
  createMeasurement(measurements, pressure, "hPa", "pressure", timestamp);
  createMeasurement(measurements, light, "lux", "light", timestamp);
  
  // Thêm thông tin bổ sung
  data["source"] = deviceName;
  data["device_time"] = timestamp;
  
  // Chuyển JSON thành chuỗi
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện telemetry
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.println("Sent combined sensor data:");
  Serial.print("  Temperature: "); Serial.print(temperature); Serial.println("°C");
  Serial.print("  Humidity: "); Serial.print(humidity); Serial.println("%");
  Serial.print("  Pressure: "); Serial.print(pressure); Serial.println(" hPa");
  Serial.print("  Light: "); Serial.print(light); Serial.println(" lux");
}

// Gửi dữ liệu một loại cảm biến lên topic riêng (phương thức riêng biệt)
void sendSingleSensorData(float value, const char* unit, const char* type, const char* topic) {
  // Thời gian hiện tại
  unsigned long timestamp = millis();
  
  // Tạo JSON payload
  DynamicJsonDocument doc(1024);
  JsonObject payload = doc.to<JsonObject>();
  
  payload["api_key"] = apiKey;
  payload["device"] = deviceName;
  payload["topic"] = topic;
  
  JsonObject data = payload.createNestedObject("payload");
  
  // Tạo mảng measurements chỉ với một phép đo
  JsonArray measurements = data.createNestedArray("measurements");
  createMeasurement(measurements, value, unit, type, timestamp);
  
  // Thêm thông tin bổ sung
  data["source"] = deviceName;
  data["device_time"] = timestamp;
  
  // Chuyển JSON thành chuỗi
  String output;
  serializeJson(doc, output);
  
  // Gửi sự kiện telemetry
  socketIO.sendEVENT("telemetry", output.c_str());
  
  Serial.print("Sent "); Serial.print(type); Serial.print(" data: ");
  Serial.print(value); Serial.print(" "); Serial.println(unit);
}

// Gửi dữ liệu nhiệt độ
void sendTemperatureData() {
  float temperature = random(2000, 3000) / 100.0; // 20.00-30.00
  sendSingleSensorData(temperature, "celsius", "temperature", "temperature");
}

// Gửi dữ liệu độ ẩm
void sendHumidityData() {
  float humidity = random(4000, 8000) / 100.0; // 40.00-80.00
  sendSingleSensorData(humidity, "percent", "humidity", "humidity");
}

void setup() {
  Serial.begin(115200);
  Serial.println("\nESP32 Socket.IO Client - IoT Data Server");
  
  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // Kết nối tới Socket.IO server
  socketIO.begin(socketIOHost, socketIOPort, socketIOUrl);
  socketIO.onEvent(socketIOEvent);
  socketIO.setReconnectInterval(5000); // Kết nối lại sau mỗi 5 giây nếu mất kết nối
  
  Serial.print("Connecting to Socket.IO server at ");
  Serial.print(socketIOHost);
  Serial.print(":");
  Serial.println(socketIOPort);
}

unsigned long previousMillis = 0;
const long interval = 10000; // Gửi dữ liệu mỗi 10 giây

void loop() {
  // Cần gọi loop() liên tục để duy trì kết nối Socket.IO
  socketIO.loop();
  
  // Chỉ gửi dữ liệu nếu đã kết nối và đăng ký thành công
  if (isConnected && isRegistered) {
    unsigned long currentMillis = millis();
    
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      
      // Gửi dữ liệu cảm biến gộp
      sendCombinedSensorData();
      
      // Hoặc gửi từng loại dữ liệu riêng biệt (bỏ comment để sử dụng)
      // sendTemperatureData();
      // delay(1000);
      // sendHumidityData();
    }
  }
} 