# topic_listener.py - Chương trình theo dõi và hiển thị các thay đổi trên topics đã đăng ký
import socketio
import time
import json
import sys
import threading
import requests
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt

# Khởi tạo Rich console để hiển thị đẹp hơn
console = Console()

# Thông tin kết nối
SERVER_URL = "http://localhost:5000"  # Thay thế bằng địa chỉ thực tế của server
API_KEY = "1d05a3f5-f2c8-46dc-873c-4c87e0af26ab"  # API key của client kari 
DEVICE_NAME = "topic_monitor"

# Khởi tạo Socket.IO client
sio = socketio.Client(logger=False, engineio_logger=False)

# Theo dõi dữ liệu nhận được
topic_data = {}  # Lưu trữ dữ liệu nhận được theo topic
subscribed_topics = []  # Danh sách các topic đã đăng ký
available_topics = []  # Danh sách các topic có sẵn trên server

# Định nghĩa các callback
@sio.event
def connect():
    console.print("[bold green]✅ Đã kết nối thành công tới Socket.IO server![/]")
    register_device()
    fetch_available_topics()

@sio.event
def connect_error(data):
    console.print(f"[bold red]❌ Lỗi kết nối: {data}[/]")

@sio.event
def disconnect():
    console.print("[bold yellow]⚠️ Đã ngắt kết nối từ server[/]")

@sio.on('response')
def on_response(data):
    if data.get('status') == 'success':
        console.print(f"[green]✓ {data.get('message', 'Thành công')}[/]")
    else:
        console.print(f"[yellow]⚠️ {data.get('message', 'Thông báo không rõ')}[/]")

@sio.on('error')
def on_error(data):
    console.print(f"[bold red]❌ Lỗi: {data.get('message', 'Không rõ lỗi')}[/]")

# Hàm xử lý dữ liệu chung cho tất cả các topic
def handle_topic_data(topic, data):
    """Xử lý dữ liệu nhận được từ một topic"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Lưu dữ liệu mới nhất cho topic này
    if topic not in topic_data:
        topic_data[topic] = []
    
    # Giới hạn số lượng tin nhắn lưu trữ cho mỗi topic
    if len(topic_data[topic]) >= 5:
        topic_data[topic].pop(0)
    
    # Thêm dữ liệu mới
    topic_data[topic].append({
        'timestamp': timestamp,
        'data': data
    })
    
    # Hiển thị thông báo nhận được dữ liệu mới
    console.print(f"[bold blue]📨 Nhận dữ liệu mới trên topic[/] [bold yellow]{topic}[/] [blue]lúc {timestamp}[/]")
    
    # Hiển thị chi tiết dữ liệu
    try:
        device = data.get('device', 'không rõ')
        
        if 'payload' in data:
            payload = data['payload']
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, indent=2, ensure_ascii=False)
                console.print(Panel(f"[bold green]Thiết bị:[/] {device}\n[bold green]Dữ liệu:[/]\n{payload_str}", 
                                   title=f"Topic: {topic}", border_style="blue"))
            else:
                console.print(Panel(f"[bold green]Thiết bị:[/] {device}\n[bold green]Dữ liệu:[/] {payload}", 
                                   title=f"Topic: {topic}", border_style="blue"))
        elif 'action' in data and 'target' in data:
            # Đây là một lệnh điều khiển
            action = data.get('action')
            target = data.get('target')
            console.print(Panel(f"[bold green]Thiết bị:[/] {device}\n[bold green]Hành động:[/] {action}\n[bold green]Đối tượng:[/] {target}", 
                               title=f"Lệnh trên topic: {topic}", border_style="yellow"))
        else:
            console.print(Panel(f"[bold green]Dữ liệu nhận được:[/]\n{json.dumps(data, indent=2, ensure_ascii=False)}", 
                               title=f"Topic: {topic}", border_style="blue"))
    except Exception as e:
        console.print(f"[red]Lỗi khi hiển thị dữ liệu: {e}[/]")

def register_device():
    """Đăng ký thiết bị với server."""
    console.print("[yellow]Đăng ký thiết bị với server...[/]")
    
    # Tạo thông tin đăng ký
    data = {
        "api_key": API_KEY,
        "device": DEVICE_NAME,
        "action": "register",
        "capabilities": "topic_monitor"
    }
    
    # Gửi đăng ký
    sio.emit('device_register', data)

def subscribe_to_topic(topic_name):
    """Đăng ký nhận thông tin trên một topic cụ thể."""
    if topic_name in subscribed_topics:
        console.print(f"[yellow]Đã đăng ký trước đó cho topic: {topic_name}[/]")
        return
        
    console.print(f"[yellow]Đăng ký nhận thông tin trên topic: {topic_name}...[/]")
    
    # Tạo yêu cầu đăng ký
    data = {
        "api_key": API_KEY,
        "device": DEVICE_NAME,
        "topic": topic_name
    }
    
    # Tạo một handler cho topic này
    create_topic_handler(topic_name)
    
    # Gửi yêu cầu đăng ký
    sio.emit('subscribe', data)
    
    # Thêm vào danh sách đã đăng ký
    subscribed_topics.append(topic_name)

def create_topic_handler(topic_name):
    """Tạo handler cho một topic cụ thể."""
    # Định nghĩa handler cho topic này để nhận thông báo
    @sio.on(topic_name)
    def on_topic_message(data):
        handle_topic_data(topic_name, data)

def fetch_available_topics():
    """Lấy danh sách các topic có sẵn từ server thông qua API."""
    global available_topics
    
    console.print("[yellow]Đang lấy danh sách topic từ server...[/]")
    
    try:
        # Gửi request API để lấy danh sách topics
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{SERVER_URL}/api/topics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'topics' in data:
                # Lấy danh sách tên topic
                available_topics = [topic.get('name') for topic in data.get('topics', [])]
                console.print(f"[green]Đã lấy {len(available_topics)} topic từ server.[/]")
            else:
                console.print("[yellow]Không tìm thấy danh sách topic trong phản hồi.[/]")
        else:
            console.print(f"[red]Lỗi khi gọi API: {response.status_code} - {response.text}[/]")
    
    except Exception as e:
        console.print(f"[red]Lỗi khi lấy danh sách topic: {e}[/]")
        
    # Nếu không có topic nào từ API, thêm một số topic mặc định
    if not available_topics:
        # Thêm các topic mặc định thường dùng
        default_topics = ["temperature", "humidity", "pressure", "light", "status", "control", "telemetry"]
        for topic in default_topics:
            if topic not in available_topics:
                available_topics.append(topic)
        console.print("[yellow]Sử dụng danh sách topic mặc định.[/]")

def list_and_select_topics():
    """Hiển thị danh sách topic và cho phép người dùng chọn để theo dõi."""
    global available_topics
    
    # Lấy lại danh sách topic mới nhất
    fetch_available_topics()
    
    if not available_topics:
        console.print("[red]Không có topic nào khả dụng.[/]")
        return
    
    console.print("\n" + "="*50)
    console.print("[bold cyan]📋 DANH SÁCH TOPIC KHẢ DỤNG[/]")
    console.print("="*50)
    
    table = Table(title="Topics có thể theo dõi")
    table.add_column("STT", style="cyan")
    table.add_column("Tên Topic", style="green")
    table.add_column("Đã đăng ký", style="magenta")
    
    for idx, topic in enumerate(available_topics, 1):
        subscribed = "✓" if topic in subscribed_topics else "✗"
        table.add_row(str(idx), topic, subscribed)
    
    console.print(table)
    
    # Cho phép người dùng chọn một hoặc nhiều topic
    choice = input("\nNhập STT của topic muốn theo dõi (nhiều topic cách nhau bởi dấu phẩy, nhập 'all' để chọn tất cả): ")
    
    if choice.lower() == 'all':
        # Đăng ký tất cả topic
        for topic in available_topics:
            if topic not in subscribed_topics:
                subscribe_to_topic(topic)
    else:
        try:
            # Xử lý danh sách STT được nhập
            selected_indices = [int(idx.strip()) - 1 for idx in choice.split(',') if idx.strip().isdigit()]
            
            for idx in selected_indices:
                if 0 <= idx < len(available_topics):
                    topic = available_topics[idx]
                    if topic not in subscribed_topics:
                        subscribe_to_topic(topic)
                else:
                    console.print(f"[red]STT {idx+1} không hợp lệ![/]")
        except Exception as e:
            console.print(f"[red]Lỗi khi xử lý lựa chọn: {e}[/]")

def show_status():
    """Hiển thị trạng thái hiện tại của phần mềm."""
    console.print("\n" + "="*50)
    console.print("[bold]📊 TRẠNG THÁI THEO DÕI TOPIC[/]")
    console.print("="*50)
    
    if not subscribed_topics:
        console.print("[yellow]Chưa đăng ký theo dõi topic nào![/]")
    else:
        table = Table(title="Topics đang theo dõi")
        table.add_column("STT", style="cyan")
        table.add_column("Tên Topic", style="green")
        table.add_column("Số thông báo", style="magenta")
        
        for idx, topic in enumerate(subscribed_topics, 1):
            message_count = len(topic_data.get(topic, []))
            table.add_row(str(idx), topic, str(message_count))
        
        console.print(table)
    
    console.print("="*50)

def display_menu():
    """Hiển thị menu cho người dùng."""
    console.print("\n" + "="*50)
    console.print("[bold cyan]🔍 CHƯƠNG TRÌNH THEO DÕI TOPIC[/]")
    console.print("="*50)
    console.print("1. Đăng ký theo dõi topic mới (nhập tên)")
    console.print("2. Xem và chọn topic từ danh sách")
    console.print("3. Hiển thị trạng thái hiện tại")
    console.print("4. Xem lịch sử dữ liệu nhận được")
    console.print("5. Làm mới danh sách topic từ server")
    console.print("0. Thoát")
    console.print("="*50)
    return input("Nhập lựa chọn của bạn: ")

def add_new_topic():
    """Thêm topic mới để theo dõi."""
    console.print("\n" + "="*50)
    console.print("[bold cyan]📥 ĐĂNG KÝ THEO DÕI TOPIC MỚI[/]")
    console.print("="*50)
    
    topic_name = input("Nhập tên topic bạn muốn theo dõi: ")
    
    if not topic_name or not topic_name.strip():
        console.print("[red]Tên topic không hợp lệ![/]")
        return
    
    subscribe_to_topic(topic_name.strip())

def view_topic_history():
    """Xem lịch sử dữ liệu nhận được trên các topic."""
    if not topic_data:
        console.print("[yellow]Chưa nhận được dữ liệu nào từ các topic![/]")
        return
    
    console.print("\n" + "="*50)
    console.print("[bold cyan]📜 LỊCH SỬ DỮ LIỆU NHẬN ĐƯỢC[/]")
    console.print("="*50)
    
    # Hiển thị các topic có dữ liệu
    topics_with_data = list(topic_data.keys())
    table = Table(title="Topics có dữ liệu")
    table.add_column("STT", style="cyan")
    table.add_column("Tên Topic", style="green")
    table.add_column("Số thông báo", style="magenta")
    
    for idx, topic in enumerate(topics_with_data, 1):
        message_count = len(topic_data.get(topic, []))
        table.add_row(str(idx), topic, str(message_count))
    
    console.print(table)
    
    # Chọn topic để xem chi tiết
    topic_idx = input("Nhập STT của topic để xem chi tiết (nhấn Enter để quay lại): ")
    
    if not topic_idx:
        return
    
    try:
        idx = int(topic_idx) - 1
        if 0 <= idx < len(topics_with_data):
            selected_topic = topics_with_data[idx]
            show_topic_data(selected_topic)
        else:
            console.print("[red]STT không hợp lệ![/]")
    except ValueError:
        console.print("[red]Vui lòng nhập một số![/]")

def show_topic_data(topic_name):
    """Hiển thị dữ liệu chi tiết của một topic."""
    if topic_name not in topic_data or not topic_data[topic_name]:
        console.print(f"[yellow]Không có dữ liệu cho topic {topic_name}[/]")
        return
    
    console.print(f"\n[bold cyan]📋 DỮ LIỆU CHI TIẾT CHO TOPIC: {topic_name}[/]")
    
    for idx, entry in enumerate(topic_data[topic_name], 1):
        timestamp = entry['timestamp']
        data = entry['data']
        
        console.print(f"[bold]Thông báo #{idx} - {timestamp}[/]")
        console.print(Panel(json.dumps(data, indent=2, ensure_ascii=False), 
                           title=f"Dữ liệu #{idx}", border_style="green"))

def main():
    try:
        console.print(f"[bold cyan]Kết nối tới Socket.IO server: {SERVER_URL}[/]")
        # Kết nối với timeout để tránh treo
        sio.connect(SERVER_URL, wait_timeout=10, transports=['websocket', 'polling'])
        
        # Vòng lặp menu
        while True:
            choice = display_menu()
            
            if choice == "1":
                add_new_topic()
            elif choice == "2":
                list_and_select_topics()
            elif choice == "3":
                show_status()
            elif choice == "4":
                view_topic_history()
            elif choice == "5":
                fetch_available_topics()
            elif choice == "0":
                break
            else:
                console.print("[red]Lựa chọn không hợp lệ, vui lòng thử lại![/]")
        
        # Ngắt kết nối
        if sio.connected:
            sio.disconnect()
        
    except Exception as e:
        console.print(f"[bold red]Lỗi: {e}[/]")
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    # Cài đặt các thư viện cần thiết
    try:
        # Kiểm tra nếu các gói đã được cài đặt
        import subprocess
        import sys
        
        # Cài đặt các gói cần thiết
        console.print("[yellow]Đảm bảo các thư viện cần thiết được cài đặt...[/]")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-socketio[client]", "websocket-client", "rich", "requests"])
        console.print("[green]Đã cài đặt các thư viện cần thiết.[/]")
    except Exception as e:
        console.print(f"[red]Lỗi khi cài đặt thư viện: {e}[/]")
        console.print("[yellow]Vui lòng cài đặt thủ công: pip install python-socketio[client] websocket-client rich requests[/]")
    
    main() 