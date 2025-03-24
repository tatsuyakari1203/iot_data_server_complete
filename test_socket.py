import socketio
import time
import json
import random
from datetime import datetime

# Khởi tạo Socket.IO client
sio = socketio.Client(logger=False, engineio_logger=False)

# Thông tin kết nối
SERVER_URL = "http://localhost:5000"  # Thay thế bằng địa chỉ thực tế của server
API_KEY = "1d05a3f5-f2c8-46dc-873c-4c87e0af26ab"  # API key của client kari
DEVICE_NAME = "python_test_device"

# Topic mặc định
SENSOR_TOPIC = "sensors"  # Topic chung cho tất cả dữ liệu cảm biến
TEMPERATURE_TOPIC = "temperature"  # Topic riêng cho nhiệt độ
HUMIDITY_TOPIC = "humidity"  # Topic riêng cho độ ẩm
PRESSURE_TOPIC = "pressure"  # Topic riêng cho áp suất
LIGHT_TOPIC = "light"  # Topic riêng cho ánh sáng

# Định nghĩa các callback
@sio.event
def connect():
    print("Đã kết nối thành công tới Socket.IO server!")
    register_device()

@sio.event
def connect_error(data):
    print(f"Lỗi kết nối: {data}")

@sio.event
def disconnect():
    print("Đã ngắt kết nối từ server")

@sio.on('response')
def on_response(data):
    print(f"Nhận được response từ server: {data}")

@sio.on('error')
def on_error(data):
    print(f"Nhận được thông báo lỗi: {data}")

def register_device():
    """Đăng ký thiết bị với server."""
    print("Đăng ký thiết bị với server...")
    
    # Tạo thông tin đăng ký
    data = {
        "api_key": API_KEY,
        "device": DEVICE_NAME,
        "action": "register",
        "capabilities": "temperature,humidity,pressure,light"
    }
    
    # Gửi đăng ký
    sio.emit('device_register', data)

def create_standard_measurement(value, unit, type, timestamp=None):
    """Tạo cấu trúc dữ liệu chuẩn cho phép đo."""
    if timestamp is None:
        timestamp = time.time()
        
    return {
        "value": value,
        "unit": unit,
        "type": type,
        "timestamp": timestamp
    }

def send_combined_sensor_data(topic_name=SENSOR_TOPIC):
    """Gửi tất cả dữ liệu cảm biến trong một payload thống nhất."""
    # Tạo dữ liệu ngẫu nhiên cho các cảm biến
    temperature = round(random.uniform(20, 30), 2)
    humidity = round(random.uniform(40, 80), 2)
    pressure = round(random.uniform(980, 1020), 2)
    light = round(random.uniform(0, 1000), 2)
    
    # Tạo timestamp chung cho tất cả các phép đo
    timestamp = time.time()
    
    # Tạo payload với cấu trúc chuẩn
    data = {
        "api_key": API_KEY,
        "device": DEVICE_NAME,
        "topic": topic_name,
        "payload": {
            "measurements": [
                create_standard_measurement(temperature, "celsius", "temperature", timestamp),
                create_standard_measurement(humidity, "percent", "humidity", timestamp),
                create_standard_measurement(pressure, "hPa", "pressure", timestamp),
                create_standard_measurement(light, "lux", "light", timestamp)
            ],
            "source": "python_test",
            "device_time": timestamp
        }
    }
    
    print(f"Đang gửi tất cả dữ liệu cảm biến lên topic '{topic_name}':")
    print(f" - Nhiệt độ: {temperature}°C")
    print(f" - Độ ẩm: {humidity}%")
    print(f" - Áp suất: {pressure} hPa")
    print(f" - Ánh sáng: {light} lux")
    
    sio.emit('telemetry', data)
    print("Đã gửi dữ liệu cảm biến thành công.")

def send_sensor_data(value, unit, sensor_type, topic_name):
    """Gửi dữ liệu một loại cảm biến với cấu trúc chuẩn."""
    # Tạo payload với cấu trúc chuẩn
    data = {
        "api_key": API_KEY,
        "device": DEVICE_NAME,
        "topic": topic_name,
        "payload": {
            "measurements": [
                create_standard_measurement(value, unit, sensor_type)
            ],
            "source": "python_test",
            "device_time": time.time()
        }
    }
    
    print(f"Đang gửi dữ liệu {sensor_type}: {value} {unit}")
    sio.emit('telemetry', data)
    print(f"Đã gửi dữ liệu {sensor_type} thành công.")

def send_temperature_data():
    """Gửi dữ liệu nhiệt độ theo cấu trúc chuẩn."""
    temperature = round(random.uniform(20, 30), 2)
    send_sensor_data(temperature, "celsius", "temperature", TEMPERATURE_TOPIC)

def send_humidity_data():
    """Gửi dữ liệu độ ẩm theo cấu trúc chuẩn."""
    humidity = round(random.uniform(40, 80), 2)
    send_sensor_data(humidity, "percent", "humidity", HUMIDITY_TOPIC)

def send_pressure_data():
    """Gửi dữ liệu áp suất theo cấu trúc chuẩn."""
    pressure = round(random.uniform(980, 1020), 2)
    send_sensor_data(pressure, "hPa", "pressure", PRESSURE_TOPIC)

def send_light_data():
    """Gửi dữ liệu ánh sáng theo cấu trúc chuẩn."""
    light = round(random.uniform(0, 1000), 2)
    send_sensor_data(light, "lux", "light", LIGHT_TOPIC)

def send_custom_data():
    """Gửi dữ liệu tùy chỉnh với cấu trúc chuẩn."""
    topic_name = input("\nNhập tên topic: ")
    
    if not topic_name or not topic_name.strip():
        print("Tên topic không hợp lệ!")
        return
    
    try:
        print("\nNhập thông tin:")
        sensor_type = input("Loại dữ liệu (vd: temperature, wind_speed, ...): ")
        value = float(input("Giá trị: "))
        unit = input("Đơn vị đo (vd: celsius, m/s, ...): ")
        
        # Tạo payload theo cấu trúc chuẩn
        data = {
            "api_key": API_KEY,
            "device": DEVICE_NAME,
            "topic": topic_name.strip(),
            "payload": {
                "measurements": [
                    create_standard_measurement(value, unit, sensor_type)
                ],
                "source": "python_test",
                "device_time": time.time()
            }
        }
        
        print(f"Đang gửi dữ liệu tùy chỉnh lên topic '{topic_name.strip()}'...")
        sio.emit('telemetry', data)
        print("Đã gửi dữ liệu tùy chỉnh thành công.")
        
    except ValueError:
        print("Lỗi: Giá trị không hợp lệ!")
    except Exception as e:
        print(f"Lỗi khi gửi dữ liệu: {e}")

def send_all_data_separately():
    """Gửi tất cả các loại dữ liệu lên từng topic riêng biệt."""
    send_temperature_data()
    time.sleep(1)
    send_humidity_data()
    time.sleep(1)
    send_pressure_data()
    time.sleep(1)
    send_light_data()
    print("\nĐã gửi tất cả các loại dữ liệu thành công (phương thức riêng biệt).")

def send_advanced_custom_data():
    """Gửi dữ liệu tùy chỉnh với cấu trúc JSON hoàn toàn tùy chỉnh."""
    topic_name = input("\nNhập tên topic: ")
    
    if not topic_name or not topic_name.strip():
        print("Tên topic không hợp lệ!")
        return
    
    try:
        print("\nNhập dữ liệu tùy chỉnh (định dạng JSON):")
        print("Ví dụ: {\"measurements\": [{\"value\": 27.5, \"unit\": \"celsius\", \"type\": \"temperature\"}]}")
        
        custom_data_str = input("Dữ liệu JSON: ")
        custom_data = json.loads(custom_data_str)
        
        # Tạo payload
        data = {
            "api_key": API_KEY,
            "device": DEVICE_NAME,
            "topic": topic_name.strip(),
            "payload": custom_data
        }
        
        print(f"Đang gửi dữ liệu tùy chỉnh lên topic '{topic_name.strip()}'...")
        sio.emit('telemetry', data)
        print("Đã gửi dữ liệu tùy chỉnh thành công.")
        
    except json.JSONDecodeError:
        print("Lỗi: Dữ liệu JSON không hợp lệ!")
    except Exception as e:
        print(f"Lỗi khi gửi dữ liệu: {e}")

def continuous_send_data():
    """Gửi dữ liệu liên tục với khoảng thời gian 10 giây."""
    try:
        count = 1
        while True:
            print(f"\n[Lần {count}] Đang gửi dữ liệu...")
            send_combined_sensor_data()
            count += 1
            print(f"Đợi 10 giây cho lần gửi tiếp theo...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nĐã dừng gửi dữ liệu liên tục.")

def display_menu():
    """Hiển thị menu cho người dùng."""
    print("\n" + "="*60)
    print("🔧 CHƯƠNG TRÌNH GỬI DỮ LIỆU SOCKET.IO (CẤU TRÚC CHUẨN)")
    print("="*60)
    print("1. Gửi tất cả dữ liệu cảm biến (nhiệt độ, độ ẩm, áp suất, ánh sáng) lên một topic")
    print("2. Gửi dữ liệu nhiệt độ lên topic riêng biệt")
    print("3. Gửi dữ liệu độ ẩm lên topic riêng biệt")
    print("4. Gửi dữ liệu áp suất lên topic riêng biệt")
    print("5. Gửi dữ liệu ánh sáng lên topic riêng biệt")
    print("6. Gửi tất cả loại dữ liệu lên các topic riêng biệt")
    print("7. Gửi dữ liệu tùy chỉnh với cấu trúc chuẩn")
    print("8. Gửi dữ liệu JSON tùy chỉnh hoàn toàn")
    print("9. Gửi dữ liệu liên tục (10 giây/lần)")
    print("0. Thoát")
    print("="*60)
    return input("Nhập lựa chọn của bạn: ")

def main():
    try:
        print(f"Kết nối tới Socket.IO server: {SERVER_URL}")
        # Kết nối với timeout để tránh treo
        sio.connect(SERVER_URL, wait_timeout=10, transports=['websocket', 'polling'])
        
        # Vòng lặp menu
        while True:
            choice = display_menu()
            
            if choice == "1":
                send_combined_sensor_data()
            elif choice == "2":
                send_temperature_data()
            elif choice == "3":
                send_humidity_data()
            elif choice == "4":
                send_pressure_data()
            elif choice == "5":
                send_light_data()
            elif choice == "6":
                send_all_data_separately()
            elif choice == "7":
                send_custom_data()
            elif choice == "8":
                send_advanced_custom_data()
            elif choice == "9":
                continuous_send_data()
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ, vui lòng thử lại!")
        
        # Ngắt kết nối
        if sio.connected:
            sio.disconnect()
        
    except Exception as e:
        print(f"Lỗi: {e}")
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    # Cài đặt các thư viện cần thiết
    try:
        # Kiểm tra nếu các gói đã được cài đặt
        import subprocess
        import sys
        
        # Cài đặt các gói cần thiết
        print("Đảm bảo các thư viện cần thiết được cài đặt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-socketio[client]", "websocket-client"])
        print("Đã cài đặt các thư viện cần thiết.")
    except Exception as e:
        print(f"Lỗi khi cài đặt thư viện: {e}")
        print("Vui lòng cài đặt thủ công: pip install python-socketio[client] websocket-client")
    
    main()