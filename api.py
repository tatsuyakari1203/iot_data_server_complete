from flask import Blueprint, request, jsonify
from database import (
    get_client_by_api_key, get_all_topics, get_all_devices, 
    get_telemetry_data, get_topic_by_name, get_device_by_name
)
from datetime import datetime

# Create a Blueprint for the REST API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Authenticate API requests
def authenticate():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        api_key = request.json.get('api_key') if request.is_json else None
    if not api_key:
        return None
    return get_client_by_api_key(api_key)

# Endpoint to get all topics for a client
@api_bp.route('/topics', methods=['GET'])
def get_topics():
    client = authenticate()
    if not client:
        return jsonify({'error': 'Authentication required'}), 401
    
    topics = get_all_topics(client['id'])
    return jsonify({'topics': topics})

# Endpoint to get all devices for a client
@api_bp.route('/devices', methods=['GET'])
def get_devices():
    client = authenticate()
    if not client:
        return jsonify({'error': 'Authentication required'}), 401
    
    devices = get_all_devices(client['id'])
    return jsonify({'devices': devices})

# Endpoint to get telemetry data
@api_bp.route('/data', methods=['GET'])
def get_data():
    client = authenticate()
    if not client:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Get query parameters
    device_name = request.args.get('device')
    topic_name = request.args.get('topic')
    limit = request.args.get('limit', 100, type=int)
    
    device_id = None
    topic_id = None
    
    # If device name is provided, get the device ID
    if device_name:
        device = get_device_by_name(device_name, client['id'])
        if device:
            device_id = device['id']
        else:
            # Auto-create device if not found
            from database import create_device
            device_id = create_device(device_name, f"Auto-created device for {device_name}", client['id'])
            print(f"Auto-created device: {device_name} with ID: {device_id}")
    
    # If topic name is provided, get the topic ID
    if topic_name:
        topic = get_topic_by_name(topic_name)
        if topic:
            topic_id = topic['id']
        else:
            # Auto-create topic if not found
            from database import create_topic
            topic_id = create_topic(topic_name, f"Auto-created topic for {topic_name}", client['id'])
            print(f"Auto-created topic: {topic_name} with ID: {topic_id}")
    
    # Get the telemetry data
    data = get_telemetry_data(device_id, topic_id, limit)
    
    # Process payload - convert JSON strings to objects if possible
    for item in data:
        try:
            if isinstance(item['payload'], str):
                import json
                item['payload'] = json.loads(item['payload'])
        except (json.JSONDecodeError, TypeError):
            pass
    
    return jsonify({'data': data})

# HTTP endpoint to publish data (alternative to MQTT)
@api_bp.route('/publish', methods=['POST'])
def publish_data():
    client = authenticate()
    if not client:
        return jsonify({'error': 'Xác thực thất bại. Vui lòng cung cấp API key hợp lệ.'}), 401
    
    # Check if request is JSON
    if not request.is_json:
        return jsonify({'error': 'Yêu cầu phải là JSON'}), 400
    
    try:
        # Get and validate input data
        data = request.get_json()
        
        # Check for required fields
        required_fields = ['device', 'topic', 'payload']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Thiếu các trường bắt buộc: {", ".join(missing_fields)}'
            }), 400
        
        # Extract and validate each field
        device_name = data['device']
        topic_name = data['topic']
        payload = data['payload']
        
        # Validate device name
        if not isinstance(device_name, str) or not device_name.strip():
            return jsonify({'error': 'Tên thiết bị không hợp lệ'}), 400
            
        # Sanitize device name (remove leading/trailing whitespace)
        device_name = device_name.strip()
        
        # Validate topic name
        if not isinstance(topic_name, str) or not topic_name.strip():
            return jsonify({'error': 'Tên chủ đề không hợp lệ'}), 400
            
        # Sanitize topic name (remove leading/trailing whitespace)
        topic_name = topic_name.strip()
        
        # Validate payload is a dictionary or valid data type
        if not isinstance(payload, (dict, list, str, int, float, bool)):
            return jsonify({'error': 'Dữ liệu payload không hợp lệ'}), 400
            
        # Database operations with proper error handling
        try:
            # Get or auto-create the topic if not found
            topic = get_topic_by_name(topic_name, client['id'])
            if not topic:
                # Auto-create topic
                from database import create_topic
                topic_id = create_topic(topic_name, f"Auto-created topic for {topic_name}", client['id'])
                if not topic_id:
                    return jsonify({'error': f'Không thể tạo chủ đề: {topic_name}. Có thể đã tồn tại.'}), 500
                print(f"Auto-created topic: {topic_name} with ID: {topic_id}")
                topic = {'id': topic_id}
            
            # Get or create the device
            from database import create_device, store_telemetry_data
            device = get_device_by_name(device_name, client['id'])
            if not device:
                device_id = create_device(device_name, f"Auto-created device for {device_name}", client['id'])
                if not device_id:
                    return jsonify({'error': f'Không thể tạo thiết bị: {device_name}'}), 500
                print(f"Auto-created device: {device_name} with ID: {device_id}")
            else:
                device_id = device['id']
            
            # Store the telemetry data with improved error handling
            success = store_telemetry_data(device_id, topic['id'], payload)
            if not success:
                return jsonify({'error': 'Lỗi khi lưu trữ dữ liệu telemetry'}), 500
                
            return jsonify({
                'status': 'success', 
                'message': 'Dữ liệu đã được xuất bản thành công'
            })
            
        except Exception as e:
            print(f"Error in publish endpoint: {e}")
            return jsonify({'error': f'Lỗi xử lý yêu cầu: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Unexpected error in publish endpoint: {e}")
        return jsonify({'error': 'Lỗi không xác định khi xử lý yêu cầu'}), 500

# HTTP endpoint for sending commands to devices
@api_bp.route('/command', methods=['POST'])
def send_command():
    client = authenticate()
    if not client:
        return jsonify({'error': 'Xác thực thất bại. Vui lòng cung cấp API key hợp lệ.'}), 401
    
    # Check if request is JSON
    if not request.is_json:
        return jsonify({'error': 'Yêu cầu phải là JSON'}), 400
    
    try:
        # Get and validate input data
        data = request.get_json()
        
        # Check for required fields
        required_fields = ['device', 'topic', 'action', 'target']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Thiếu các trường bắt buộc: {", ".join(missing_fields)}'
            }), 400
        
        # Extract fields
        device_name = data['device']
        topic_name = data['topic']
        action = data['action']
        target = data['target']
        
        # Validate device name
        if not isinstance(device_name, str) or not device_name.strip():
            return jsonify({'error': 'Tên thiết bị không hợp lệ'}), 400
            
        # Sanitize device name
        device_name = device_name.strip()
        
        # Validate device exists
        device = get_device_by_name(device_name, client['id'])
        if not device:
            return jsonify({'error': f'Thiết bị không tồn tại: {device_name}'}), 404
        
        # Validate action
        if not isinstance(action, str) or action not in ['on', 'off', 'toggle']:
            return jsonify({'error': 'Hành động không hợp lệ. Sử dụng: on, off, hoặc toggle'}), 400
        
        # Validate target
        if not isinstance(target, str) or not target.strip():
            return jsonify({'error': 'Đối tượng mục tiêu không hợp lệ'}), 400
        
        # Forward the command to Socket.IO server
        try:
            from socket_server import socketio
            
            # Create command object
            command = {
                'action': action,
                'target': target,
                'api_key': client['api_key'] if 'api_key' in client else data.get('api_key'),
                'device': device_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send command to device's room
            socketio.emit('command', command, room=device_name)
            
            print(f"Command sent via HTTP API: {action} -> {target} for device {device_name}")
            
            return jsonify({
                'status': 'success',
                'message': f'Lệnh {action} đã được gửi đến {device_name}'
            })
            
        except Exception as e:
            print(f"Error sending command via Socket.IO: {e}")
            return jsonify({
                'error': f'Lỗi khi gửi lệnh qua Socket.IO: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Unexpected error in command endpoint: {e}")
        return jsonify({'error': f'Lỗi không xác định: {str(e)}'}), 500
