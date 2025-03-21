# IoT Data Server

*Read this in: [English](#iot-data-server-1), [Tiếng Việt](#máy-chủ-dữ-liệu-iot)*

## IoT Data Server

A comprehensive platform for collecting, storing, and visualizing IoT device data. Supports both MQTT and HTTP protocols, with data storage in SQLite and a modern web-based management interface.

### Features

- MQTT broker for IoT device communication
- HTTP API for device data submission
- REST API for web/mobile app data retrieval
- Web UI for managing clients, topics, devices, and viewing data
- SQLite database for persistent storage
- API key authentication system
- CSV data export functionality
- Bootstrap-based modern responsive interface

### Prerequisites

- Python 3.8+ installed
- Docker and Docker Compose (for running the Mosquitto MQTT broker)
- Git (optional, for cloning the repository)

### Setup Instructions

#### For Windows

1. **Install Dependencies**

   Open PowerShell or Command Prompt and run:

   ```powershell
   # Create a virtual environment (optional but recommended)
   python -m venv venv
   
   # Activate the virtual environment
   .\venv\Scripts\Activate.ps1    # For PowerShell
   # OR
   .\venv\Scripts\activate.bat    # For Command Prompt
   
   # Install required packages
   pip install -r requirements.txt
   ```

2. **Set Up the Mosquitto MQTT Broker**

   ```powershell
   # Create password file for Mosquitto
   .\create_mqtt_password.ps1
   
   # Start the Docker containers
   docker-compose up -d
   ```

3. **Start the Server**

   ```powershell
   python app.py
   ```

4. **Access the Web Interface**

   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

#### For Linux

1. **Install Dependencies**

   Open a terminal and run:

   ```bash
   # Create a virtual environment (optional but recommended)
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate
   
   # Install required packages
   pip install -r requirements.txt
   ```

2. **Set Up the Mosquitto MQTT Broker**

   ```bash
   # Make the script executable
   chmod +x create_mqtt_password.sh
   
   # Create password file for Mosquitto
   ./create_mqtt_password.sh
   
   # Start the Docker containers
   docker-compose up -d
   ```

3. **Start the Server**

   ```bash
   python app.py
   ```

4. **Access the Web Interface**

   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Project Structure

```
iot_data_server/
│
├── app.py                  # Main Flask application
├── mqtt_server.py          # MQTT server implementation
├── database.py             # Database operations
├── api.py                  # REST API endpoints
├── docker-compose.yml      # Docker configuration
├── requirements.txt        # Python dependencies
│
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard
│   ├── clients.html        # Clients management
│   ├── topics.html         # Topics management
│   ├── devices.html        # Devices management
│   ├── data.html           # Data visualization
│   ├── api_docs.html       # API documentation
│   └── about.html          # About page
│
├── static/                 # Static assets
│   ├── css/                # CSS files
│   └── code_examples/      # Code examples for integration
│
└── mosquitto/              # Mosquitto MQTT broker
    ├── config/             # Broker configuration
    ├── data/               # Broker data
    └── log/                # Broker logs
```

### Usage

1. **Set Up Your Environment**
   - Create a client to get an API key in the Clients page
   - Create topics for your data streams in the Topics page

2. **Connect Your IoT Devices**
   - Use either MQTT or HTTP protocol as shown in the Devices page
   - Make sure to include your API key in every request

3. **View and Analyze Data**
   - Navigate to the Data page to view telemetry data
   - Export data to CSV for further analysis

### Device Integration

#### MQTT Connection
- **Broker Host**: Your server IP/hostname
- **Broker Port**: 1883
- **Broker Username**: admin (optional, depends on broker configuration)
- **Broker Password**: admin (optional, depends on broker configuration)
- **Topic Format**: device_name/topic_name
- **API Key**: Must be included in the JSON payload

#### HTTP Connection
- **API Endpoint**: http://your_server_ip:5000/api/publish
- **Method**: POST
- **Content-Type**: application/json
- **Payload**: Include device_name, topic_name, api_key, value and other data

Refer to the Device Connect page and API Documentation for detailed examples.

### Troubleshooting

- **MQTT Connection Issues**: Check if the Mosquitto container is running with `docker ps`
- **API Key Authentication Failures**: Check the invalid_key_log.txt for details on failed authentication attempts
- **Database Errors**: Ensure SQLite is properly installed and the database file is not corrupted

---

## Máy chủ dữ liệu IoT

Nền tảng toàn diện để thu thập, lưu trữ và hiển thị dữ liệu từ thiết bị IoT. Hỗ trợ cả giao thức MQTT và HTTP, với lưu trữ dữ liệu trong SQLite và giao diện quản lý hiện đại dựa trên web.

### Tính năng

- Máy chủ MQTT cho giao tiếp với thiết bị IoT
- API HTTP để gửi dữ liệu từ thiết bị
- REST API để ứng dụng web/mobile lấy dữ liệu
- Giao diện Web UI để quản lý clients, topics, thiết bị và xem dữ liệu
- Cơ sở dữ liệu SQLite để lưu trữ dài hạn
- Hệ thống xác thực bằng API key
- Chức năng xuất dữ liệu CSV
- Giao diện hiện đại, tương thích với nhiều thiết bị dựa trên Bootstrap

### Yêu cầu hệ thống

- Python 3.8+ đã được cài đặt
- Docker và Docker Compose (để chạy Mosquitto MQTT broker)
- Git (tùy chọn, để clone repository)

### Hướng dẫn cài đặt

#### Cho Windows

1. **Cài đặt các gói phụ thuộc**

   Mở PowerShell hoặc Command Prompt và chạy:

   ```powershell
   # Tạo môi trường ảo (tùy chọn nhưng khuyến nghị)
   python -m venv venv
   
   # Kích hoạt môi trường ảo
   .\venv\Scripts\Activate.ps1    # Cho PowerShell
   # HOẶC
   .\venv\Scripts\activate.bat    # Cho Command Prompt
   
   # Cài đặt các gói cần thiết
   pip install -r requirements.txt
   ```

2. **Thiết lập Mosquitto MQTT Broker**

   ```powershell
   # Tạo file mật khẩu cho Mosquitto
   .\create_mqtt_password.ps1
   
   # Khởi động các container Docker
   docker-compose up -d
   ```

3. **Khởi động máy chủ**

   ```powershell
   python app.py
   ```

4. **Truy cập giao diện web**

   Mở trình duyệt và truy cập:
   ```
   http://localhost:5000
   ```

#### Cho Linux

1. **Cài đặt các gói phụ thuộc**

   Mở terminal và chạy:

   ```bash
   # Tạo môi trường ảo (tùy chọn nhưng khuyến nghị)
   python3 -m venv venv
   
   # Kích hoạt môi trường ảo
   source venv/bin/activate
   
   # Cài đặt các gói cần thiết
   pip install -r requirements.txt
   ```

2. **Thiết lập Mosquitto MQTT Broker**

   ```bash
   # Cấp quyền thực thi cho script
   chmod +x create_mqtt_password.sh
   
   # Tạo file mật khẩu cho Mosquitto
   ./create_mqtt_password.sh
   
   # Khởi động các container Docker
   docker-compose up -d
   ```

3. **Khởi động máy chủ**

   ```bash
   python app.py
   ```

4. **Truy cập giao diện web**

   Mở trình duyệt và truy cập:
   ```
   http://localhost:5000
   ```

### Cấu trúc dự án

```
iot_data_server/
│
├── app.py                  # Ứng dụng Flask chính
├── mqtt_server.py          # Triển khai máy chủ MQTT
├── database.py             # Các thao tác với cơ sở dữ liệu
├── api.py                  # Các endpoint REST API
├── docker-compose.yml      # Cấu hình Docker
├── requirements.txt        # Các gói phụ thuộc Python
│
├── templates/              # Các template HTML
│   ├── base.html           # Template cơ sở
│   ├── index.html          # Bảng điều khiển
│   ├── clients.html        # Quản lý clients
│   ├── topics.html         # Quản lý topics
│   ├── devices.html        # Quản lý thiết bị
│   ├── data.html           # Hiển thị dữ liệu
│   ├── api_docs.html       # Tài liệu API
│   └── about.html          # Trang giới thiệu
│
├── static/                 # Tài nguyên tĩnh
│   ├── css/                # Các file CSS
│   └── code_examples/      # Ví dụ code tích hợp
│
└── mosquitto/              # Mosquitto MQTT broker
    ├── config/             # Cấu hình broker
    ├── data/               # Dữ liệu broker
    └── log/                # Log broker
```

### Cách sử dụng

1. **Thiết lập môi trường của bạn**
   - Tạo client để nhận API key trong trang Clients
   - Tạo topics cho các luồng dữ liệu trong trang Topics

2. **Kết nối thiết bị IoT của bạn**
   - Sử dụng giao thức MQTT hoặc HTTP như được hiển thị trong trang Devices
   - Đảm bảo kèm theo API key trong mọi request

3. **Xem và phân tích dữ liệu**
   - Điều hướng đến trang Data để xem dữ liệu telemetry
   - Xuất dữ liệu sang CSV để phân tích sâu hơn

### Tích hợp thiết bị

#### Kết nối MQTT
- **Broker Host**: IP/hostname của máy chủ của bạn
- **Broker Port**: 1883
- **Broker Username**: admin (tùy chọn, phụ thuộc vào cấu hình broker)
- **Broker Password**: admin (tùy chọn, phụ thuộc vào cấu hình broker)
- **Định dạng Topic**: device_name/topic_name
- **API Key**: Phải được kèm theo trong payload JSON

#### Kết nối HTTP
- **API Endpoint**: http://ip_may_chu:5000/api/publish
- **Method**: POST
- **Content-Type**: application/json
- **Payload**: Bao gồm device_name, topic_name, api_key, value và các dữ liệu khác

Tham khảo trang Kết nối thiết bị và Tài liệu API để biết các ví dụ chi tiết.

### Xử lý sự cố

- **Vấn đề kết nối MQTT**: Kiểm tra xem container Mosquitto có đang chạy bằng lệnh `docker ps`
- **Lỗi xác thực API Key**: Kiểm tra file invalid_key_log.txt để biết chi tiết về các nỗ lực xác thực thất bại
- **Lỗi cơ sở dữ liệu**: Đảm bảo SQLite được cài đặt đúng cách và file cơ sở dữ liệu không bị hỏng
