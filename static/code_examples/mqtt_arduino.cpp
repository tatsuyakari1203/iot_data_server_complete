#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_MQTT_SERVER_IP";
const int mqtt_port = 1883;
const char* api_key = "YOUR_API_KEY";
const char* device_name = "esp8266_sensor";
const char* topic_name = "temperature";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  // Wait for WiFi connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  
  // Connect to MQTT broker
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Read sensor data (example)
  float temp = 25.5;  // Replace with actual sensor reading
  
  // Create topic and payload
  String topic = String(api_key) + "/" + device_name + "/" + topic_name;
  String payload = "{\"value\":" + String(temp) + "}";
  
  // Publish data
  client.publish(topic.c_str(), payload.c_str());
  
  // Wait 30 seconds before next reading
  delay(30000);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(device_name)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}
