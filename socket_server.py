import json
import os
from datetime import datetime
from flask_socketio import SocketIO, join_room, leave_room
from database import (
    get_client_by_api_key, get_topic_by_name, get_device_by_name,
    create_device, create_topic, store_telemetry_data
)

# Create a SocketIO instance to be initialized with Flask app
socketio = SocketIO()

# Lưu trữ thông tin về các topic đã đăng ký
registered_topic_handlers = set()

def init_socket_server(app):
    """Initialize the Socket.IO server with the Flask app."""
    socketio.init_app(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        print("Client connected to Socket.IO server")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        print("Client disconnected from Socket.IO server")
    
    @socketio.on('telemetry')
    def handle_telemetry(data):
        """Handle telemetry data from ESP devices."""
        try:
            print("Received telemetry data via Socket.IO:")
            print(data)
            
            # Validate data structure
            if not isinstance(data, dict):
                emit_error("Dữ liệu không hợp lệ. Phải là đối tượng JSON")
                return
            
            # Check for required fields
            required_fields = ['api_key', 'device', 'topic', 'payload']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                emit_error(f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}")
                return
            
            # Extract fields
            api_key = data.get('api_key')
            device_name = data.get('device')
            topic_name = data.get('topic')
            payload = data.get('payload')
            
            # Validate API key
            client = get_client_by_api_key(api_key)
            if not client:
                emit_error("API key không hợp lệ")
                _log_invalid_message(f"device: {device_name}, topic: {topic_name}", 
                                    json.dumps(payload), "API key không hợp lệ")
                return
            
            client_id = client['id']
            print(f"Authentication successful for client: {client['name']} (ID: {client_id})")
            
            # Validate device name
            if not isinstance(device_name, str) or not device_name.strip():
                emit_error("Tên thiết bị không hợp lệ")
                return
                
            # Sanitize device name
            device_name = device_name.strip()
            
            # Validate topic name
            if not isinstance(topic_name, str) or not topic_name.strip():
                emit_error("Tên chủ đề không hợp lệ")
                return
                
            # Sanitize topic name
            topic_name = topic_name.strip()
            
            # Validate payload
            if not isinstance(payload, (dict, list, str, int, float, bool)):
                emit_error("Dữ liệu payload không hợp lệ")
                return
            
            # Get or create device
            device = get_device_by_name(device_name, client_id)
            if not device:
                try:
                    device_id = create_device(device_name, f"Auto-created device for {device_name}", client_id)
                    if not device_id:
                        emit_error(f"Không thể tạo thiết bị: {device_name}")
                        return
                    print(f"Created new device: {device_name} with ID {device_id}")
                except Exception as e:
                    emit_error(f"Lỗi khi tạo thiết bị: {str(e)}")
                    return
            else:
                device_id = device['id']
            
            # Get or create topic
            topic = get_topic_by_name(topic_name, client_id)
            if not topic:
                try:
                    topic_id = create_topic(topic_name, f"Auto-created topic for {topic_name}", client_id)
                    if not topic_id:
                        emit_error(f"Không thể tạo chủ đề: {topic_name}")
                        return
                    print(f"Created new topic: {topic_name} with ID {topic_id}")
                except Exception as e:
                    emit_error(f"Lỗi khi tạo chủ đề: {str(e)}")
                    return
            else:
                topic_id = topic['id']
            
            # Store telemetry data
            success = store_telemetry_data(device_id, topic_id, payload)
            if not success:
                emit_error("Lỗi khi lưu trữ dữ liệu telemetry")
                return
                
            # Send success response
            socketio.emit('response', {
                'status': 'success',
                'message': 'Dữ liệu đã được lưu trữ thành công'
            })
            
            # Nếu là dữ liệu trạng thái, gửi cập nhật trạng thái ra toàn bộ hệ thống
            if topic_name == 'status':
                socketio.emit('status_update', {
                    'device': device_name,
                    'payload': payload,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Gửi dữ liệu đến các thiết bị đã đăng ký vào topic này
            topic_room = f"topic:{topic_name}"
            socketio.emit(topic_name, {
                'device': device_name,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }, room=topic_room)
            
            print(f"Successfully stored telemetry data from device '{device_name}' on topic '{topic_name}'")
            
        except Exception as e:
            print(f"Unexpected error processing Socket.IO message: {e}")
            emit_error(f"Lỗi không xác định: {str(e)}")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Xử lý yêu cầu đăng ký nhận các cập nhật từ một topic cụ thể."""
        try:
            print(f"Received subscribe request: {data}")
            
            # Validate data structure
            if not isinstance(data, dict):
                emit_error("Dữ liệu đăng ký không hợp lệ")
                return
            
            # Check required fields
            required_fields = ['api_key', 'device', 'topic']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                emit_error(f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}")
                return
            
            # Extract fields
            api_key = data.get('api_key')
            device_name = data.get('device')
            topic_name = data.get('topic')
            
            # Validate API key
            client = get_client_by_api_key(api_key)
            if not client:
                emit_error("API key không hợp lệ")
                return
            
            client_id = client['id']
            print(f"Authentication successful for client: {client['name']} (ID: {client_id})")
            
            # Join a room for this device (for targeted messages)
            join_room(device_name)
            
            # Join a room for the topic (for broadcasting to all devices on a topic)
            topic_room = f"topic:{topic_name}"
            join_room(topic_room)
            
            # Register dynamic event handler for this topic if not already registered
            register_dynamic_handler(topic_name)
            
            print(f"Device {device_name} subscribed to {topic_name}")
            
            # Send confirmation
            socketio.emit('response', {
                'status': 'success',
                'message': f'Đăng ký thành công cho thiết bị {device_name} vào topic {topic_name}'
            })
            
        except Exception as e:
            print(f"Error in subscribe handler: {e}")
            emit_error(f"Lỗi xử lý đăng ký: {str(e)}")
    
    @socketio.on('device_register')
    def handle_device_register(data):
        """Xử lý đăng ký thiết bị mới."""
        try:
            print(f"Received device registration: {data}")
            
            # Validate data structure
            if not isinstance(data, dict):
                emit_error("Dữ liệu đăng ký không hợp lệ")
                return
            
            # Check required fields
            required_fields = ['api_key', 'device', 'action']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                emit_error(f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}")
                return
            
            # Extract fields
            api_key = data.get('api_key')
            device_name = data.get('device')
            action = data.get('action')
            capabilities = data.get('capabilities', '')
            
            # Validate API key
            client = get_client_by_api_key(api_key)
            if not client:
                emit_error("API key không hợp lệ")
                return
            
            client_id = client['id']
            print(f"Authentication successful for client: {client['name']} (ID: {client_id})")
            
            # Validate device name
            if not isinstance(device_name, str) or not device_name.strip():
                emit_error("Tên thiết bị không hợp lệ")
                return
                
            # Sanitize device name
            device_name = device_name.strip()
            
            # Join a room for this device (for targeted messages)
            join_room(device_name)
            
            # Get or create device
            device = get_device_by_name(device_name, client_id)
            if not device:
                try:
                    # Tạo mô tả có thông tin về khả năng của thiết bị
                    description = f"Auto-registered device with capabilities: {capabilities}"
                    device_id = create_device(device_name, description, client_id)
                    if not device_id:
                        emit_error(f"Không thể tạo thiết bị: {device_name}")
                        return
                    print(f"Registered new device: {device_name} with ID {device_id}")
                except Exception as e:
                    emit_error(f"Lỗi khi tạo thiết bị: {str(e)}")
                    return
            else:
                print(f"Device {device_name} already registered")
            
            # Send confirmation
            socketio.emit('response', {
                'status': 'success',
                'message': f'Thiết bị {device_name} đã được đăng ký thành công'
            })
            
        except Exception as e:
            print(f"Error in device register handler: {e}")
            emit_error(f"Lỗi xử lý đăng ký thiết bị: {str(e)}")
    
    @socketio.on('command')
    def handle_command(data):
        """Xử lý các lệnh điều khiển gửi đến thiết bị."""
        try:
            print(f"Received command: {data}")
            
            # Validate data
            if not isinstance(data, dict):
                emit_error("Dữ liệu lệnh không hợp lệ")
                return
            
            # Check required fields
            required_fields = ['api_key', 'device', 'topic', 'action', 'target']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                emit_error(f"Thiếu các trường bắt buộc: {', '.join(missing_fields)}")
                return
            
            # Extract fields
            api_key = data.get('api_key')
            device_name = data.get('device')
            topic_name = data.get('topic')
            action = data.get('action')
            target = data.get('target')
            
            # Validate API key
            client = get_client_by_api_key(api_key)
            if not client:
                emit_error("API key không hợp lệ")
                return
            
            client_id = client['id']
            print(f"Authentication successful for client: {client['name']} (ID: {client_id})")
            
            # Validate device exists
            device = get_device_by_name(device_name, client_id)
            if not device:
                emit_error(f"Thiết bị không tồn tại: {device_name}")
                return
            
            # Forward the command to the specified device
            command_data = {
                'action': action,
                'target': target,
                'api_key': api_key,
                'device': device_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Gửi lệnh qua room của thiết bị
            socketio.emit('command', command_data, room=device_name)
            
            # Gửi lệnh qua topic cụ thể đã chỉ định
            register_dynamic_handler(topic_name)  # Đảm bảo handler cho topic này đã được đăng ký
            socketio.emit(topic_name, command_data, room=f"topic:{topic_name}")
            
            print(f"Command {action} sent to device {device_name} via topic {topic_name}")
            
            # Acknowledge command was sent
            socketio.emit('response', {
                'status': 'success',
                'message': f'Lệnh {action} đã được gửi đến {device_name} qua topic {topic_name}'
            })
            
        except Exception as e:
            print(f"Error in command handler: {e}")
            emit_error(f"Lỗi xử lý lệnh: {str(e)}")
    
    def register_dynamic_handler(topic_name):
        """Đăng ký handler cho một topic động nếu chưa được đăng ký."""
        global registered_topic_handlers
        
        if topic_name in registered_topic_handlers:
            return  # Đã đăng ký trước đó
            
        @socketio.on(topic_name)
        def dynamic_topic_handler(data):
            """Xử lý các message trên topic tùy chỉnh."""
            try:
                print(f"Received message on custom topic '{topic_name}': {data}")
                
                # Validate API key if present
                if isinstance(data, dict) and 'api_key' in data:
                    api_key = data.get('api_key')
                    client = get_client_by_api_key(api_key)
                    if not client:
                        # Không phát lỗi, chỉ log và return
                        print(f"Invalid API key in message on topic {topic_name}")
                        return
                
                # Broadcast message to all subscribers of this topic
                socketio.emit(topic_name, data, room=f"topic:{topic_name}")
                
                # If it's a command, forward to target device
                if isinstance(data, dict) and 'action' in data and 'target' in data and 'device' in data:
                    device_name = data.get('device')
                    socketio.emit('command', data, room=device_name)
                
            except Exception as e:
                print(f"Error handling message on topic '{topic_name}': {e}")
        
        # Đánh dấu là đã đăng ký
        registered_topic_handlers.add(topic_name)
        print(f"Registered dynamic handler for topic: {topic_name}")
    
    def emit_error(message):
        """Emit an error message to the client."""
        socketio.emit('error', {
            'status': 'error',
            'message': message
        })
    
    def _log_invalid_message(topic, payload, reason):
        """Log invalid messages to a file for later analysis."""
        try:
            timestamp = datetime.now().isoformat()
            with open("invalid_socket_messages.log", "a") as f:
                f.write(f"[{timestamp}] TOPIC: {topic} | REASON: {reason} | PAYLOAD: {payload}\n")
        except Exception as e:
            print(f"Error logging invalid message: {e}")
    
    return socketio 