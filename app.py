from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bootstrap import Bootstrap
from mqtt_server import mqtt_server
from database import (
    init_db, create_client, get_all_clients, create_topic, get_all_topics,
    get_all_devices, delete_topic, delete_device, get_telemetry_data, delete_client
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

@app.before_first_request
def start_mqtt_server():
    global mqtt_thread
    if mqtt_thread is None:
        mqtt_thread = threading.Thread(target=mqtt_server.start)
        mqtt_thread.daemon = True
        mqtt_thread.start()

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
            flash('Đăng nhập thành công!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công!', 'success')
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
        'data_count': len(latest_data)
    }
    
    return render_template('index.html', stats=stats, latest_data=latest_data)

# Client management
@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            client_id, api_key = create_client(name)
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
        flash('Đã xóa client thành công cùng với tất cả thiết bị và chủ đề liên quan', 'success')
    else:
        flash('Không thể xóa client. Vui lòng kiểm tra lại.', 'danger')
        
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
        flash('Chủ đề đã được xóa thành công', 'success')
    else:
        flash('Không thể xóa chủ đề. Hãy chắc chắn rằng bạn có quyền truy cập và chủ đề tồn tại.', 'danger')
    
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
        flash('Thiết bị đã được xóa thành công', 'success')
    else:
        flash('Không thể xóa thiết bị. Hãy chắc chắn rằng bạn có quyền truy cập và thiết bị tồn tại.', 'danger')
    
    return redirect(url_for('devices'))

# Device management
@app.route('/devices')
@login_required
def devices():
    devices = get_all_devices()
    clients = get_all_clients()
    return render_template('devices.html', devices=devices, clients=clients)

# Data visualization
@app.route('/data')
@login_required
def data():
    topic_id = request.args.get('topic_id', type=int)
    
    # Get all devices
    devices = get_all_devices()
    topics = get_all_topics()
    
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
                         selected_topic=topic_id,
                         now=now)

# API documentation
@app.route('/api_docs')
def api_docs():
    return render_template('api_docs.html')

@app.route('/about')
def about():
    return render_template('about.html')

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
    flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
    return redirect(url_for('login', next=request.url))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
