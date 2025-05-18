from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bootstrap import Bootstrap
from mqtt_server import mqtt_server
from database import (
    init_db, create_client, get_all_clients, create_topic, get_all_topics,
    get_all_devices, delete_topic, delete_device, get_telemetry_data, delete_client, get_telemetry_data_count,
    cleanup_orphaned_data, update_client_api_key, get_device_telemetry_data
)
from api import api_bp
import threading
import json
import os
from dotenv import load_dotenv
from flask_login import login_required, login_user, logout_user, current_user, LoginManager
from auth import User, init_login_manager, verify_credentials
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
app.config['HOST'] = os.getenv('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.getenv('FLASK_PORT', 5000))
Bootstrap(app)

# Initialize Flask-Login
login_manager = init_login_manager(app)

# Custom login_required for redirecting to login with next parameter
def custom_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Register the API blueprint
app.register_blueprint(api_bp)

# Initialize the database
init_db()

# Start the MQTT server in a separate thread
mqtt_thread = None

# Initialize function to start MQTT server
def start_mqtt_server():
    global mqtt_thread
    if mqtt_thread is None:
        mqtt_thread = threading.Thread(target=mqtt_server.start)
        mqtt_thread.daemon = True
        mqtt_thread.start()

# In Flask 2.0+, before_first_request is removed
# Use this alternative approach
with app.app_context():
    start_mqtt_server()

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_credentials(username, password):
            user = User(1, username)
            login_user(user)
            flash('Login successful!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

# Root route - redirects to About page
@app.route('/')
def index():
    return redirect(url_for('about'))

# Main dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    clients = get_all_clients()
    topics = get_all_topics()
    devices = get_all_devices()
    
    # Get the latest telemetry data
    latest_data = get_telemetry_data(limit=10)
    
    # Count statistics
    stats = {
        'client_count': len(clients),
        'topic_count': len(topics),
        'device_count': len(devices),
        'data_count': get_telemetry_data_count()  # Use a new function to get total count
    }
    
    # Get MQTT broker information
    mqtt_info = {
        'broker_host': mqtt_server.broker_host,
        'broker_port': mqtt_server.broker_port,
        'is_connected': mqtt_server.client.is_connected() if hasattr(mqtt_server.client, 'is_connected') else False
    }
    
    return render_template('index.html', stats=stats, latest_data=latest_data, mqtt_info=mqtt_info)

# Client management
@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        name = request.form.get('name')
        api_key = request.form.get('api_key')  # Lấy API key từ form
        
        if name:
            client_id, api_key = create_client(name, api_key)  # Truyền api_key vào hàm create_client
            flash(f'Client created successfully. API Key: {api_key}', 'success')
        else:
            flash('Client name is required', 'danger')
    
    clients = get_all_clients()
    return render_template('clients.html', clients=clients)

# Delete a client
@app.route('/clients/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client_route(client_id):
    success = delete_client(client_id)
    
    if success:
        flash('Client deleted successfully along with all associated devices and topics', 'success')
    else:
        flash('Failed to delete client. Please try again.', 'danger')
        
    return redirect(url_for('clients'))

# Update a client's API key
@app.route('/clients/update-api-key/<int:client_id>', methods=['POST'])
@login_required
def update_client_api_key_route(client_id):
    new_api_key = request.form.get('new_api_key')
    
    if not new_api_key:
        flash('API key cannot be empty', 'danger')
        return redirect(url_for('clients'))
    
    success = update_client_api_key(client_id, new_api_key)
    
    if success:
        flash('API key updated successfully', 'success')
    else:
        flash('Failed to update API key. Please try again.', 'danger')
        
    return redirect(url_for('clients'))

# Topic management
@app.route('/topics', methods=['GET', 'POST'])
@login_required
def topics():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        client_id = request.form.get('client_id')
        
        if name and client_id:
            topic_id = create_topic(name, description, client_id)
            if topic_id:
                flash('Topic created successfully', 'success')
            else:
                flash('Topic already exists with that name', 'danger')
        else:
            flash('Topic name and client are required', 'danger')
    
    topics = get_all_topics()
    clients = get_all_clients()
    return render_template('topics.html', topics=topics, clients=clients)

# Delete a topic
@app.route('/topics/delete/<int:topic_id>', methods=['POST'])
@login_required
def delete_topic_route(topic_id):
    # Get the optional client_id filter if provided in the form
    client_id = request.form.get('client_id', type=int)
    
    # Use the improved delete_topic function with error handling
    success = delete_topic(topic_id, client_id)
    
    if success:
        flash('Topic deleted successfully', 'success')
    else:
        flash('Failed to delete topic. Please ensure you have access and the topic exists.', 'danger')
    
    return redirect(url_for('topics'))

# Delete a device
@app.route('/devices/delete/<int:device_id>', methods=['POST'])
@login_required
def delete_device_route(device_id):
    # Get the optional client_id filter if provided in the form
    client_id = request.form.get('client_id', type=int)
    
    # Use the improved delete_device function with error handling
    success = delete_device(device_id, client_id)
    
    if success:
        flash('Device deleted successfully', 'success')
    else:
        flash('Failed to delete device. Please ensure you have access and the device exists.', 'danger')
    
    return redirect(url_for('devices'))

# Device management
@app.route('/devices')
def devices():
    if current_user.is_authenticated:
        devices = get_all_devices()
        clients = get_all_clients()
        return render_template('devices.html', devices=devices, clients=clients)
    else:
        # For non-authenticated users, just show device documentation
        return render_template('devices_public.html')

# Data visualization
@app.route('/data')
@login_required
def data():
    topic_id = request.args.get('topic_id', type=int)
    
    # Get all devices
    devices = get_all_devices()
    topics = get_all_topics()
    clients = get_all_clients()  # Get all clients
    
    # Initialize device data dictionary to store telemetry data for each device
    device_data = {}
    
    # Get data for each device with selected topic if specified
    for device in devices:
        telemetry = get_telemetry_data(device_id=device['id'], topic_id=topic_id, limit=50)
        if telemetry:
            device_data[device['id']] = {
                'device': device,
                'telemetry': telemetry
            }
    
    # Add current datetime for CSV export filename
    from datetime import datetime
    now = datetime.now()
    
    # Get all telemetry data for table view and export
    all_telemetry = get_telemetry_data(topic_id=topic_id, limit=100)
    
    return render_template('data.html', 
                         device_data=device_data,
                         data=all_telemetry,
                         devices=devices, 
                         topics=topics, 
                         clients=clients,  # Pass clients to the template
                         selected_topic=topic_id,
                         now=now)

# API documentation
@app.route('/api_docs')
def api_docs():
    return render_template('api_docs_gate.html')

@app.route('/about')
def about():
    return render_template('about.html')

# API endpoints for real-time updates
@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API endpoint for dashboard statistics"""
    clients = get_all_clients()
    topics = get_all_topics()
    devices = get_all_devices()
    
    stats = {
        'client_count': len(clients),
        'topic_count': len(topics),
        'device_count': len(devices),
        'data_count': get_telemetry_data_count()
    }
    
    return jsonify({'stats': stats})

@app.route('/api/latest_data', methods=['GET'])
def api_latest_data():
    """API endpoint for latest telemetry data"""
    limit = request.args.get('limit', 10, type=int)
    topic_id = request.args.get('topic_id', type=int)
    
    # Giới hạn limit tối đa là 1000 để tránh quá tải
    limit = min(max(limit, 1), 1000)
    
    latest_data = get_telemetry_data(topic_id=topic_id, limit=limit)
    
    # Process payload - convert JSON strings to objects if possible
    for item in latest_data:
        try:
            if isinstance(item['payload'], str):
                item['payload'] = json.loads(item['payload'])
        except (json.JSONDecodeError, TypeError):
            pass
    
    return jsonify({'latest_data': latest_data})

@app.route('/api/mqtt_status', methods=['GET'])
def api_mqtt_status():
    """API endpoint for MQTT broker status"""
    mqtt_info = {
        'broker_host': mqtt_server.broker_host,
        'broker_port': mqtt_server.broker_port,
        'is_connected': mqtt_server.client.is_connected() if hasattr(mqtt_server.client, 'is_connected') else False
    }
    
    return jsonify({'mqtt_info': mqtt_info})

# API endpoint for device data with client and topic information
@app.route('/api/device_data', methods=['GET'])
def api_device_data():
    """API endpoint for device-specific data"""
    topic_id = request.args.get('topic_id', type=int)
    limit = request.args.get('limit', 5, type=int)
    
    # Giới hạn limit tối đa là 1000 bản ghi cho mỗi thiết bị để tránh quá tải
    limit = min(max(limit, 1), 1000)
    
    # Get device-specific data
    device_data = get_device_telemetry_data(topic_id=topic_id, limit_per_device=limit)
    
    # Process payload - convert JSON strings to objects if possible
    for device_id, info in device_data.items():
        for item in info.get('telemetry', []):
            try:
                if isinstance(item.get('payload'), str):
                    item['payload'] = json.loads(item['payload'])
            except (json.JSONDecodeError, TypeError):
                pass
    
    return jsonify({'device_data': device_data})

# Cleanup orphaned data
@app.route('/cleanup-orphaned-data', methods=['POST'])
@login_required
def cleanup_data_route():
    result = cleanup_orphaned_data()
    
    if result['success']:
        if result['deleted_count'] > 0:
            flash(f'Successfully cleaned up {result["deleted_count"]} orphaned data records.', 'success')
        else:
            flash('No orphaned data found to clean up.', 'info')
    else:
        flash(f'Error cleaning up orphaned data: {result.get("error", "Unknown error")}', 'danger')
    
    return redirect(url_for('data'))

# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    if current_user.is_authenticated:
        return render_template('404.html'), 404
    else:
        return redirect(url_for('login', next=request.url))

# Handle 401 errors (unauthorized)
@app.errorhandler(401)
def unauthorized(e):
    flash('Please login to continue.', 'warning')
    return redirect(url_for('login', next=request.url))

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
