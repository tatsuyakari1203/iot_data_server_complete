import paho.mqtt.client as mqtt
import json
import os
from database import get_client_by_api_key, get_topic_by_name, get_device_by_name
from database import create_device, create_topic, store_telemetry_data
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MQTTServer:
    def __init__(self, 
                 broker_host=os.getenv('MQTT_BROKER', 'iot.karis.cloud'), 
                 broker_port=int(os.getenv('MQTT_PORT', 1883)), 
                 username=os.getenv('MQTT_USERNAME', None), 
                 password=os.getenv('MQTT_PASSWORD', None)):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.client = mqtt.Client()
        
        # Set authentication credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def start(self):
        """Start the MQTT server."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            # Start the loop in a non-blocking way
            self.client.loop_start()
            print(f"MQTT server started on {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            print(f"Warning: Failed to connect to MQTT broker: {e}")
            print("The application will continue without MQTT support.")
            print("To enable MQTT, start the Mosquitto broker via Docker:")
            print("  docker-compose up -d")
            # Return True to prevent blocking app startup
            return True
            
    def stop(self):
        """Stop the MQTT server."""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT server stopped")
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        print(f"Connected to MQTT broker with result code {rc}")
        # Subscribe to all topics to capture all messages
        client.subscribe("#")
        
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        topic = msg.topic
        
        try:
            payload_str = msg.payload.decode('utf-8')
            
            # Log the message
            print(f"Received message on topic: {topic}")
            print(f"Raw payload: {payload_str}")
            
            # Validate minimum topic structure
            topic_parts = topic.split('/')
            if len(topic_parts) < 2:
                print(f"Error: Invalid topic format: {topic}. Expected format: device_name/topic_name")
                # Log the invalid message to a file
                self._log_invalid_message(topic, payload_str, "Invalid topic format")
                return
                
            device_name = topic_parts[0]
            topic_name = '/'.join(topic_parts[1:])  # Join the rest for the topic name
            
            # Ensure payload is valid JSON
            try:
                # Parse the JSON payload
                payload = json.loads(payload_str)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON payload: {e}")
                self._log_invalid_message(topic, payload_str, f"Invalid JSON: {e}")
                return
                
            # Validate payload structure
            if not isinstance(payload, dict):
                print(f"Error: Payload must be a JSON object, got {type(payload)}")
                self._log_invalid_message(topic, payload_str, "Payload not a JSON object")
                return
                
            # Extract API key from payload
            if 'api_key' not in payload:
                print("Error: No API key found in payload")
                self._log_invalid_message(topic, payload_str, "Missing API key")
                return
                
            api_key = payload.pop('api_key')  # Remove API key from payload
            
            # Validate the API key
            db_client = get_client_by_api_key(api_key)
            if not db_client:
                print(f"Error: Authentication failed - Invalid API key: {api_key}")
                self._log_invalid_message(topic, payload_str, f"Invalid API key: {api_key}")
                return
                
            print(f"Authentication successful for client: {db_client['name']} (ID: {db_client['id']})")
            
            client_id = db_client['id']
            
            # Get or create the device
            device = get_device_by_name(device_name, client_id)
            if not device:
                try:
                    device_id = create_device(device_name, f"Auto-created device for {device_name}", client_id)
                    if not device_id:
                        print(f"Error: Failed to create device: {device_name}")
                        self._log_invalid_message(topic, payload_str, f"Failed to create device: {device_name}")
                        return
                    print(f"Created new device: {device_name} with ID {device_id}")
                except Exception as e:
                    print(f"Error creating device: {e}")
                    self._log_invalid_message(topic, payload_str, f"Error creating device: {e}")
                    return
            else:
                device_id = device['id']
                
            # Get or create the topic if it doesn't exist
            topic = get_topic_by_name(topic_name, client_id)
            if not topic:
                try:
                    topic_id = create_topic(topic_name, f"Auto-created topic for {topic_name}", client_id)
                    if not topic_id:
                        print(f"Error: Failed to create topic: {topic_name} (might already exist)")
                        self._log_invalid_message(topic, payload_str, f"Failed to create topic: {topic_name}")
                        return
                    print(f"Created new topic: {topic_name} with ID {topic_id}")
                except Exception as e:
                    print(f"Error creating topic: {e}")
                    self._log_invalid_message(topic, payload_str, f"Error creating topic: {e}")
                    return
            else:
                topic_id = topic['id']
                
            # Store the telemetry data (with API key removed)
            success = store_telemetry_data(device_id, topic_id, payload)
            if not success:
                print(f"Error: Failed to store telemetry data")
                self._log_invalid_message(topic, payload_str, "Failed to store telemetry data")
                return
                
            print(f"Successfully stored telemetry data from device '{device_name}' on topic '{topic_name}'")
            
        except Exception as e:
            print(f"Unexpected error processing MQTT message: {e}")
            try:
                self._log_invalid_message(topic, msg.payload, f"Unexpected error: {e}")
            except:
                print("Error logging invalid message")
                
    def _log_invalid_message(self, topic, payload, reason):
        """Log invalid messages to a file for later analysis."""
        try:
            timestamp = datetime.now().isoformat()
            with open("invalid_mqtt_messages.log", "a") as f:
                f.write(f"[{timestamp}] TOPIC: {topic} | REASON: {reason} | PAYLOAD: {payload}\n")
        except Exception as e:
            print(f"Error logging invalid message: {e}")
            
    def publish(self, topic, payload, qos=0, retain=False):
        """Publish a message to a topic."""
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self.client.publish(topic, payload, qos, retain)

# Create a single instance to be used by the Flask app
mqtt_server = MQTTServer()
