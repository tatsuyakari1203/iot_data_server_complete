#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* server_url = "http://your_server_ip:5000/api/publish";
const char* api_key = "YOUR_API_KEY";
const char* device_name = "esp8266_sensor";
const char* topic_name = "temperature";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  // Wait for WiFi connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Read sensor data (example)
    float temp = 25.5;  // Replace with actual sensor reading
    
    // Create JSON document
    StaticJsonDocument<200> doc;
    doc["device"] = device_name;
    doc["topic"] = topic_name;
    
    JsonObject payload = doc.createNestedObject("payload");
    payload["value"] = temp;
    payload["unit"] = "celsius";
    
    // Serialize JSON to string
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    // Send HTTP POST request
    HTTPClient http;
    http.begin(server_url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", api_key);
    
    int httpCode = http.POST(jsonPayload);
    String response = http.getString();
    
    Serial.print("HTTP Response code: ");
    Serial.println(httpCode);
    Serial.println(response);
    
    http.end();
    
    // Wait 30 seconds before next reading
    delay(30000);
  }
}
