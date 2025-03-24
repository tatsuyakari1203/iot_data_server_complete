/**
 * IoT Data Server - Web Application Socket.IO Example
 * 
 * Mã nguồn ví dụ kết nối ứng dụng web với IoT Data Server sử dụng Socket.IO
 * để nhận dữ liệu từ các thiết bị và tương tác với chúng.
 */

// Thông tin kết nối
const SERVER_URL = window.location.hostname + ':5000'; // Hoặc địa chỉ IP cụ thể
const API_KEY = 'YOUR_API_KEY'; // Thay thế bằng API key của bạn

// Biến lưu trữ
let socket;
let isConnected = false;
let subscribedTopics = [];
let devicesList = [];

// Khởi tạo kết nối Socket.IO
function initializeSocket() {
  console.log('Initializing Socket.IO connection to ' + SERVER_URL);
  
  // Khởi tạo đối tượng Socket.IO
  socket = io(SERVER_URL, {
    transports: ['websocket', 'polling'],
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 20000
  });
  
  // Xử lý sự kiện kết nối
  socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
    isConnected = true;
    updateConnectionStatus('Connected', 'success');
    
    // Đăng ký nhận thông tin
    authenticateClient();
  });
  
  // Xử lý sự kiện ngắt kết nối
  socket.on('disconnect', (reason) => {
    console.log('Disconnected from Socket.IO server: ' + reason);
    isConnected = false;
    updateConnectionStatus('Disconnected: ' + reason, 'danger');
    clearDeviceData();
  });
  
  // Xử lý sự kiện lỗi kết nối
  socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateConnectionStatus('Connection error: ' + error.message, 'danger');
  });
  
  // Lắng nghe sự kiện dữ liệu thiết bị
  socket.on('device_data', (data) => {
    console.log('Received device data:', data);
    processDeviceData(data);
  });
  
  // Lắng nghe sự kiện phản hồi
  socket.on('response', (data) => {
    console.log('Server response:', data);
    processServerResponse(data);
  });
  
  // Lắng nghe sự kiện lỗi
  socket.on('error', (data) => {
    console.error('Server error:', data);
    showNotification('Error', data.message, 'danger');
  });
  
  // Lắng nghe sự kiện thông tin thiết bị
  socket.on('devices_info', (data) => {
    console.log('Received devices info:', data);
    updateDevicesList(data.devices);
  });
  
  // Lắng nghe sự kiện danh sách topic
  socket.on('topics_list', (data) => {
    console.log('Received topics list:', data);
    updateTopicsList(data.topics);
  });
}

// Xác thực với server
function authenticateClient() {
  if (!isConnected) return;
  
  // Gửi API key để xác thực
  socket.emit('authenticate', {
    api_key: API_KEY,
    client_type: 'web_app'
  });
  
  console.log('Sent authentication request');
}

// Đăng ký nhận dữ liệu từ topic
function subscribeToTopic(topic) {
  if (!isConnected) {
    showNotification('Error', 'Not connected to server', 'danger');
    return;
  }
  
  // Kiểm tra xem đã đăng ký topic này chưa
  if (subscribedTopics.includes(topic)) {
    showNotification('Info', 'Already subscribed to topic: ' + topic, 'info');
    return;
  }
  
  // Gửi yêu cầu đăng ký topic
  socket.emit('subscribe', {
    api_key: API_KEY,
    topic: topic
  });
  
  console.log('Subscribed to topic: ' + topic);
  subscribedTopics.push(topic);
  updateSubscribedTopicsList();
}

// Hủy đăng ký nhận dữ liệu từ topic
function unsubscribeFromTopic(topic) {
  if (!isConnected) return;
  
  // Gửi yêu cầu hủy đăng ký topic
  socket.emit('unsubscribe', {
    api_key: API_KEY,
    topic: topic
  });
  
  console.log('Unsubscribed from topic: ' + topic);
  
  // Cập nhật danh sách topics đã đăng ký
  subscribedTopics = subscribedTopics.filter(t => t !== topic);
  updateSubscribedTopicsList();
}

// Lấy danh sách thiết bị từ server
function requestDevicesList() {
  if (!isConnected) return;
  
  socket.emit('get_devices', {
    api_key: API_KEY
  });
  
  console.log('Requested devices list');
}

// Lấy danh sách topics từ server
function requestTopicsList() {
  if (!isConnected) return;
  
  socket.emit('get_topics', {
    api_key: API_KEY
  });
  
  console.log('Requested topics list');
}

// Gửi lệnh đến thiết bị cụ thể
function sendCommandToDevice(deviceId, command, parameters = {}) {
  if (!isConnected) {
    showNotification('Error', 'Not connected to server', 'danger');
    return;
  }
  
  const payload = {
    api_key: API_KEY,
    device: deviceId,
    command: command,
    ...parameters
  };
  
  socket.emit('device_command', payload);
  console.log('Sent command to device ' + deviceId + ':', command, parameters);
}

// Xử lý dữ liệu nhận được từ thiết bị
function processDeviceData(data) {
  // Kiểm tra định dạng dữ liệu
  if (!data || !data.topic || !data.payload) {
    console.error('Invalid data format received');
    return;
  }
  
  // Kiểm tra xem có phải dữ liệu cảm biến định dạng chuẩn không (có mảng measurements)
  if (data.payload.measurements && Array.isArray(data.payload.measurements)) {
    // Xử lý từng phép đo trong mảng
    data.payload.measurements.forEach(measurement => {
      // Lấy thông tin chi tiết
      const { value, unit, type, timestamp } = measurement;
      
      // Cập nhật giao diện người dùng với dữ liệu mới
      updateSensorDisplay(data.device, type, value, unit, timestamp);
      
      // Lưu dữ liệu vào bộ nhớ đệm hoặc cơ sở dữ liệu cục bộ nếu cần
      storeSensorData(data.device, type, value, unit, timestamp);
    });
  } else {
    // Xử lý dữ liệu đơn giản (định dạng cũ)
    const { value, unit, timestamp } = data.payload;
    const type = data.topic; // Sử dụng tên topic làm loại dữ liệu
    
    // Cập nhật giao diện người dùng
    updateSensorDisplay(data.device, type, value, unit, timestamp);
  }
  
  // Đánh dấu thiết bị là đang hoạt động
  markDeviceAsActive(data.device);
  
  // Thông báo cho người dùng nếu cần
  if (shouldNotifyUser(data)) {
    showDataNotification(data);
  }
}

// Xử lý phản hồi từ server
function processServerResponse(data) {
  if (data.status === 'success') {
    // Hiển thị thông báo thành công nếu cần
    if (data.action && data.action !== 'data_received') {
      showNotification('Success', data.message, 'success');
    }
    
    // Xử lý các hành động cụ thể
    if (data.action === 'authenticated') {
      // Đã xác thực thành công
      showNotification('Success', 'Authenticated successfully', 'success');
      
      // Lấy danh sách thiết bị và topics
      requestDevicesList();
      requestTopicsList();
      
      // Đăng ký nhận tất cả dữ liệu (hoặc các topics cụ thể)
      subscribeToTopic('all');
    }
  }
}

// Cập nhật danh sách thiết bị
function updateDevicesList(devices) {
  devicesList = devices;
  
  // Cập nhật giao diện người dùng
  const devicesContainer = document.getElementById('devices-list');
  if (!devicesContainer) return;
  
  // Xóa danh sách cũ
  devicesContainer.innerHTML = '';
  
  // Thêm từng thiết bị vào danh sách
  devices.forEach(device => {
    const deviceElement = document.createElement('div');
    deviceElement.className = 'device-item';
    deviceElement.innerHTML = `
      <div class="card mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h5 class="mb-0">${device.name}</h5>
          <span class="badge ${device.is_online ? 'bg-success' : 'bg-secondary'}">
            ${device.is_online ? 'Online' : 'Offline'}
          </span>
        </div>
        <div class="card-body">
          <p><strong>Last seen:</strong> ${formatTimestamp(device.last_seen)}</p>
          <p><strong>Capabilities:</strong> ${device.capabilities || 'Unknown'}</p>
          <div class="sensor-data-container" id="sensor-data-${device.id}"></div>
          <div class="mt-3">
            <button class="btn btn-sm btn-primary" onclick="sendCommandToDevice('${device.id}', 'status')">
              Request Status
            </button>
            <button class="btn btn-sm btn-warning" onclick="sendCommandToDevice('${device.id}', 'restart')">
              Restart Device
            </button>
          </div>
        </div>
      </div>
    `;
    
    devicesContainer.appendChild(deviceElement);
  });
}

// Cập nhật danh sách topics
function updateTopicsList(topics) {
  // Cập nhật giao diện người dùng
  const topicsContainer = document.getElementById('topics-list');
  if (!topicsContainer) return;
  
  // Xóa danh sách cũ
  topicsContainer.innerHTML = '';
  
  // Thêm từng topic vào danh sách
  topics.forEach(topic => {
    const isSubscribed = subscribedTopics.includes(topic.name);
    
    const topicElement = document.createElement('div');
    topicElement.className = 'topic-item';
    topicElement.innerHTML = `
      <div class="card mb-2">
        <div class="card-body py-2">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <strong>${topic.name}</strong>
              <small class="text-muted">(${topic.device_count} devices)</small>
            </div>
            <button class="btn btn-sm ${isSubscribed ? 'btn-danger' : 'btn-success'}" 
                    onclick="${isSubscribed ? 'unsubscribeFromTopic' : 'subscribeToTopic'}('${topic.name}')">
              ${isSubscribed ? 'Unsubscribe' : 'Subscribe'}
            </button>
          </div>
        </div>
      </div>
    `;
    
    topicsContainer.appendChild(topicElement);
  });
}

// Cập nhật danh sách topics đã đăng ký
function updateSubscribedTopicsList() {
  const subscribedContainer = document.getElementById('subscribed-topics');
  if (!subscribedContainer) return;
  
  // Xóa danh sách cũ
  subscribedContainer.innerHTML = '';
  
  // Thêm từng topic đã đăng ký
  subscribedTopics.forEach(topic => {
    const topicElement = document.createElement('span');
    topicElement.className = 'badge bg-info me-2 mb-2';
    topicElement.innerHTML = `
      ${topic} 
      <a href="#" onclick="unsubscribeFromTopic('${topic}'); return false;" class="text-white ms-1">
        <small>×</small>
      </a>
    `;
    
    subscribedContainer.appendChild(topicElement);
  });
}

// Cập nhật hiển thị dữ liệu cảm biến
function updateSensorDisplay(deviceId, type, value, unit, timestamp) {
  const sensorContainer = document.getElementById(`sensor-data-${deviceId}`);
  if (!sensorContainer) return;
  
  // Kiểm tra nếu đã có hiển thị cho loại cảm biến này
  let sensorElement = document.getElementById(`sensor-${deviceId}-${type}`);
  
  if (!sensorElement) {
    // Tạo phần tử mới nếu chưa có
    sensorElement = document.createElement('div');
    sensorElement.id = `sensor-${deviceId}-${type}`;
    sensorElement.className = 'sensor-reading mb-2';
    sensorContainer.appendChild(sensorElement);
  }
  
  // Cập nhật nội dung
  sensorElement.innerHTML = `
    <div class="sensor-type">${formatSensorType(type)}</div>
    <div class="sensor-value">${value} ${unit}</div>
    <div class="sensor-time text-muted"><small>${formatTimestamp(timestamp)}</small></div>
  `;
  
  // Thêm hiệu ứng cập nhật
  sensorElement.classList.add('updated');
  setTimeout(() => {
    sensorElement.classList.remove('updated');
  }, 2000);
}

// Các hàm tiện ích
function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown';
  
  // Chuyển đổi timestamp thành đối tượng Date
  const date = new Date(timestamp * 1000);
  return date.toLocaleString();
}

function formatSensorType(type) {
  // Chuyển đổi kiểu cảm biến thành dạng dễ đọc
  return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
}

function markDeviceAsActive(deviceId) {
  // Cập nhật trạng thái thiết bị trong danh sách
  const deviceIndex = devicesList.findIndex(d => d.id === deviceId);
  if (deviceIndex >= 0) {
    devicesList[deviceIndex].is_online = true;
    devicesList[deviceIndex].last_seen = Math.floor(Date.now() / 1000);
  }
}

function clearDeviceData() {
  // Đánh dấu tất cả thiết bị là offline khi mất kết nối
  devicesList.forEach(device => {
    device.is_online = false;
  });
  
  // Cập nhật lại danh sách thiết bị
  updateDevicesList(devicesList);
}

function updateConnectionStatus(message, type) {
  const statusElement = document.getElementById('connection-status');
  if (statusElement) {
    statusElement.textContent = message;
    statusElement.className = `alert alert-${type}`;
  }
}

function showNotification(title, message, type) {
  // Hiển thị thông báo trên giao diện người dùng
  const notificationContainer = document.getElementById('notifications');
  if (!notificationContainer) return;
  
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  notification.innerHTML = `
    <strong>${title}:</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  notificationContainer.appendChild(notification);
  
  // Tự động ẩn thông báo sau 5 giây
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notificationContainer.removeChild(notification);
    }, 150);
  }, 5000);
}

function shouldNotifyUser(data) {
  // Kiểm tra xem có nên hiển thị thông báo cho dữ liệu này không
  // (có thể triển khai logic cảnh báo ở đây, ví dụ: nhiệt độ quá cao)
  return false;
}

function showDataNotification(data) {
  // Hiển thị thông báo liên quan đến dữ liệu
  showNotification('Sensor Alert', `Device ${data.device} reported unusual readings`, 'warning');
}

function storeSensorData(deviceId, type, value, unit, timestamp) {
  // Lưu trữ dữ liệu cảm biến vào bộ nhớ cục bộ hoặc IndexedDB
  // Triển khai nếu cần
}

// Hàm khởi tạo ứng dụng
function initializeApp() {
  // Khởi tạo kết nối Socket.IO
  initializeSocket();
  
  // Thiết lập các sự kiện giao diện người dùng
  document.getElementById('btn-connect')?.addEventListener('click', initializeSocket);
  document.getElementById('btn-disconnect')?.addEventListener('click', () => {
    if (socket && socket.connected) {
      socket.disconnect();
    }
  });
  
  document.getElementById('btn-refresh-devices')?.addEventListener('click', requestDevicesList);
  document.getElementById('btn-refresh-topics')?.addEventListener('click', requestTopicsList);
  
  // Form đăng ký topic
  document.getElementById('topic-subscribe-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const topicInput = document.getElementById('topic-name');
    if (topicInput && topicInput.value) {
      subscribeToTopic(topicInput.value);
      topicInput.value = '';
    }
  });
}

// Khởi động ứng dụng khi tài liệu đã tải xong
document.addEventListener('DOMContentLoaded', initializeApp); 