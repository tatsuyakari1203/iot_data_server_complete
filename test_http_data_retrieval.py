import requests
import json
import time
from datetime import datetime
from tabulate import tabulate  # Để hiển thị dữ liệu dạng bảng, cài đặt: pip install tabulate

# Cấu hình
API_KEY = "b78b761a-69e4-4a54-b640-7fb05cd674ee"
API_BASE_URL = "http://127.0.0.1:5000/api"
DEVICE_NAME = "test_device_1"  # Tên thiết bị muốn lấy dữ liệu, để trống để lấy tất cả
TOPIC_NAME = "temperature"  # Tên chủ đề muốn lấy dữ liệu, để trống để lấy tất cả
LIMIT = 10  # Số lượng bản ghi tối đa muốn lấy

def get_all_devices():
    """Lấy danh sách tất cả thiết bị"""
    url = f"{API_BASE_URL}/devices"
    
    # Tạo headers với API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('devices', [])
        else:
            print(f"Lỗi: {response.status_code}")
            print(f"Chi tiết: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối: {e}")
        return []

def get_all_topics():
    """Lấy danh sách tất cả chủ đề"""
    url = f"{API_BASE_URL}/topics"
    
    # Tạo headers với API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('topics', [])
        else:
            print(f"Lỗi: {response.status_code}")
            print(f"Chi tiết: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối: {e}")
        return []

def get_telemetry_data(device_name=None, topic_name=None, limit=10):
    """Lấy dữ liệu telemetry từ API"""
    url = f"{API_BASE_URL}/data"
    
    # Tạo headers với API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Tạo query parameters
    params = {}
    if device_name:
        params['device'] = device_name
    if topic_name:
        params['topic'] = topic_name
    if limit:
        params['limit'] = limit
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f"Lỗi: {response.status_code}")
            print(f"Chi tiết: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối: {e}")
        return []

def display_data_table(data):
    """Hiển thị dữ liệu dạng bảng"""
    if not data:
        print("Không có dữ liệu để hiển thị.")
        return
    
    # Chuẩn bị dữ liệu cho bảng
    table_data = []
    for item in data:
        # Xử lý payload
        payload = item.get('payload', {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                pass
        
        # Lấy thông tin cơ bản
        row = [
            item.get('id', 'N/A'),
            item.get('device_name', 'N/A'),
            item.get('topic_name', 'N/A'),
            item.get('timestamp', 'N/A')
        ]
        
        # Thêm thông tin từ payload
        if isinstance(payload, dict):
            temperature = payload.get('temperature', payload.get('value', 'N/A'))
            humidity = payload.get('humidity', 'N/A')
            unit = payload.get('unit', 'N/A')
            row.extend([temperature, humidity, unit])
        else:
            row.extend(['N/A', 'N/A', 'N/A'])
        
        table_data.append(row)
    
    # Hiển thị bảng
    headers = ["ID", "Thiết bị", "Chủ đề", "Thời gian", "Nhiệt độ", "Độ ẩm", "Đơn vị"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def run_data_retrieval_test():
    """Chạy test lấy dữ liệu"""
    print("\n===== BẮT ĐẦU TEST LẤY DỮ LIỆU =====")
    
    # 1. Lấy danh sách thiết bị
    print("\n--- Danh sách thiết bị ---")
    devices = get_all_devices()
    if devices:
        device_table = [[d.get('id', 'N/A'), d.get('name', 'N/A'), d.get('description', 'N/A')] for d in devices]
        print(tabulate(device_table, headers=["ID", "Tên", "Mô tả"], tablefmt="grid"))
    else:
        print("Không tìm thấy thiết bị nào.")
    
    # 2. Lấy danh sách chủ đề
    print("\n--- Danh sách chủ đề ---")
    topics = get_all_topics()
    if topics:
        topic_table = [[t.get('id', 'N/A'), t.get('name', 'N/A'), t.get('description', 'N/A')] for t in topics]
        print(tabulate(topic_table, headers=["ID", "Tên", "Mô tả"], tablefmt="grid"))
    else:
        print("Không tìm thấy chủ đề nào.")
    
    # 3. Lấy dữ liệu telemetry
    print(f"\n--- Dữ liệu Telemetry ---")
    if DEVICE_NAME and TOPIC_NAME:
        print(f"Lấy dữ liệu cho thiết bị '{DEVICE_NAME}' và chủ đề '{TOPIC_NAME}'")
    elif DEVICE_NAME:
        print(f"Lấy dữ liệu cho thiết bị '{DEVICE_NAME}'")
    elif TOPIC_NAME:
        print(f"Lấy dữ liệu cho chủ đề '{TOPIC_NAME}'")
    else:
        print("Lấy tất cả dữ liệu")
    
    data = get_telemetry_data(DEVICE_NAME, TOPIC_NAME, LIMIT)
    display_data_table(data)
    
    print(f"\n===== KẾT THÚC TEST =====")

def interactive_data_explorer():
    """Công cụ khám phá dữ liệu tương tác"""
    print("\n===== CÔNG CỤ KHÁM PHÁ DỮ LIỆU IOT =====")
    
    while True:
        print("\nLựa chọn:")
        print("1. Xem danh sách thiết bị")
        print("2. Xem danh sách chủ đề")
        print("3. Xem dữ liệu telemetry")
        print("4. Tìm kiếm dữ liệu theo thiết bị")
        print("5. Tìm kiếm dữ liệu theo chủ đề")
        print("6. Thoát")
        
        choice = input("\nNhập lựa chọn của bạn (1-6): ")
        
        if choice == '1':
            devices = get_all_devices()
            if devices:
                device_table = [[d.get('id', 'N/A'), d.get('name', 'N/A'), d.get('description', 'N/A')] for d in devices]
                print(tabulate(device_table, headers=["ID", "Tên", "Mô tả"], tablefmt="grid"))
            else:
                print("Không tìm thấy thiết bị nào.")
                
        elif choice == '2':
            topics = get_all_topics()
            if topics:
                topic_table = [[t.get('id', 'N/A'), t.get('name', 'N/A'), t.get('description', 'N/A')] for t in topics]
                print(tabulate(topic_table, headers=["ID", "Tên", "Mô tả"], tablefmt="grid"))
            else:
                print("Không tìm thấy chủ đề nào.")
                
        elif choice == '3':
            limit = input("Nhập số lượng bản ghi muốn xem (mặc định 10): ") or "10"
            data = get_telemetry_data(limit=int(limit))
            display_data_table(data)
            
        elif choice == '4':
            device_name = input("Nhập tên thiết bị: ")
            limit = input("Nhập số lượng bản ghi muốn xem (mặc định 10): ") or "10"
            data = get_telemetry_data(device_name=device_name, limit=int(limit))
            display_data_table(data)
            
        elif choice == '5':
            topic_name = input("Nhập tên chủ đề: ")
            limit = input("Nhập số lượng bản ghi muốn xem (mặc định 10): ") or "10"
            data = get_telemetry_data(topic_name=topic_name, limit=int(limit))
            display_data_table(data)
            
        elif choice == '6':
            print("Cảm ơn bạn đã sử dụng công cụ khám phá dữ liệu IoT!")
            break
            
        else:
            print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")

if __name__ == "__main__":
    print("===== CÔNG CỤ LẤY DỮ LIỆU IOT =====")
    print("1. Chạy test lấy dữ liệu cơ bản")
    print("2. Sử dụng công cụ khám phá dữ liệu tương tác")
    
    choice = input("\nNhập lựa chọn của bạn (1-2): ")
    
    if choice == '1':
        run_data_retrieval_test()
    elif choice == '2':
        interactive_data_explorer()
    else:
        print("Lựa chọn không hợp lệ.")
