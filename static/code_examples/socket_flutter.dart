// IoT Data Server - Flutter Socket.IO Example
// Mã nguồn ví dụ kết nối Socket.IO trong ứng dụng Flutter

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;
import 'package:intl/intl.dart';
import 'package:charts_flutter/flutter.dart' as charts;

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IoT Data Server Client',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.light,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      darkTheme: ThemeData(
        primarySwatch: Colors.blue,
        brightness: Brightness.dark,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      themeMode: ThemeMode.system,
      home: HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with SingleTickerProviderStateMixin {
  // Socket.IO connection
  io.Socket? socket;
  bool isConnected = false;
  String connectionStatus = 'Disconnected';
  
  // API Key for authentication
  final String apiKey = 'YOUR_API_KEY';
  
  // Data containers
  List<String> subscribedTopics = [];
  Map<String, dynamic> deviceData = {};
  Map<String, List<SensorReading>> sensorReadings = {};
  List<String> topics = [];
  List<DeviceInfo> devices = [];
  List<String> logs = [];
  
  // Controller for tab view
  late TabController _tabController;
  
  // Text controllers
  final TextEditingController _serverController = TextEditingController(text: '192.168.1.100:5000');
  final TextEditingController _topicController = TextEditingController();
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    
    // Connect automatically when app starts
    WidgetsBinding.instance.addPostFrameCallback((_) {
      connectToServer();
    });
  }
  
  @override
  void dispose() {
    socket?.disconnect();
    _tabController.dispose();
    _serverController.dispose();
    _topicController.dispose();
    super.dispose();
  }
  
  // Connect to Socket.IO server
  void connectToServer() {
    final String serverUrl = _serverController.text;
    
    if (serverUrl.isEmpty) {
      _showSnackBar('Please enter a server URL');
      return;
    }
    
    setState(() {
      connectionStatus = 'Connecting...';
    });
    
    try {
      // Close previous connection if exists
      socket?.disconnect();
      
      // Initialize Socket.IO connection
      socket = io.io('http://$serverUrl', <String, dynamic>{
        'transports': ['websocket', 'polling'],
        'autoConnect': true,
        'reconnection': true,
        'reconnectionAttempts': 5,
        'reconnectionDelay': 1000,
      });
      
      // Setup event handlers
      socket?.onConnect((_) {
        _addLog('Connected to server');
        setState(() {
          isConnected = true;
          connectionStatus = 'Connected';
        });
        
        // Authenticate
        _authenticate();
      });
      
      socket?.onDisconnect((_) {
        _addLog('Disconnected from server');
        setState(() {
          isConnected = false;
          connectionStatus = 'Disconnected';
        });
      });
      
      socket?.onConnectError((error) {
        _addLog('Connection error: $error');
        setState(() {
          connectionStatus = 'Connection Error';
        });
      });
      
      socket?.onError((error) {
        _addLog('Socket error: $error');
      });
      
      // Handle device data
      socket?.on('device_data', (data) {
        _handleDeviceData(data);
      });
      
      // Handle response events
      socket?.on('response', (data) {
        _handleResponse(data);
      });
      
      // Handle error events
      socket?.on('error', (data) {
        _handleError(data);
      });
      
      // Handle devices info
      socket?.on('devices_info', (data) {
        _handleDevicesInfo(data);
      });
      
      // Handle topics list
      socket?.on('topics_list', (data) {
        _handleTopicsList(data);
      });
    } catch (e) {
      _addLog('Error initializing socket: $e');
      setState(() {
        connectionStatus = 'Error: $e';
      });
    }
  }
  
  // Authenticate with server
  void _authenticate() {
    socket?.emit('authenticate', {
      'api_key': apiKey,
      'client_type': 'mobile_app'
    });
    _addLog('Sent authentication request');
  }
  
  // Subscribe to a topic
  void _subscribeTopic(String topic) {
    if (!isConnected) {
      _showSnackBar('Not connected to server');
      return;
    }
    
    if (subscribedTopics.contains(topic)) {
      _showSnackBar('Already subscribed to $topic');
      return;
    }
    
    socket?.emit('subscribe', {
      'api_key': apiKey,
      'topic': topic
    });
    
    setState(() {
      subscribedTopics.add(topic);
    });
    
    _addLog('Subscribed to topic: $topic');
    _topicController.clear();
  }
  
  // Unsubscribe from a topic
  void _unsubscribeTopic(String topic) {
    if (!isConnected) return;
    
    socket?.emit('unsubscribe', {
      'api_key': apiKey,
      'topic': topic
    });
    
    setState(() {
      subscribedTopics.remove(topic);
    });
    
    _addLog('Unsubscribed from topic: $topic');
  }
  
  // Request devices list
  void _requestDevicesList() {
    if (!isConnected) {
      _showSnackBar('Not connected to server');
      return;
    }
    
    socket?.emit('get_devices', {
      'api_key': apiKey
    });
    
    _addLog('Requested devices list');
  }
  
  // Request topics list
  void _requestTopicsList() {
    if (!isConnected) {
      _showSnackBar('Not connected to server');
      return;
    }
    
    socket?.emit('get_topics', {
      'api_key': apiKey
    });
    
    _addLog('Requested topics list');
  }
  
  // Send command to device
  void _sendCommand(String deviceId, String command, [Map<String, dynamic>? parameters]) {
    if (!isConnected) {
      _showSnackBar('Not connected to server');
      return;
    }
    
    final Map<String, dynamic> payload = {
      'api_key': apiKey,
      'device': deviceId,
      'command': command,
    };
    
    if (parameters != null) {
      payload.addAll(parameters);
    }
    
    socket?.emit('device_command', payload);
    _addLog('Sent command to device $deviceId: $command');
  }
  
  // Handle device data event
  void _handleDeviceData(dynamic data) {
    try {
      // Basic validation
      if (data == null || !data.containsKey('topic') || !data.containsKey('payload') || !data.containsKey('device')) {
        _addLog('Invalid data format received');
        return;
      }
      
      final String deviceId = data['device'];
      final String topic = data['topic'];
      final dynamic payload = data['payload'];
      
      // Update device data map
      setState(() {
        deviceData[deviceId] = deviceData[deviceId] ?? {};
        deviceData[deviceId][topic] = payload;
      });
      
      // Handle structured data with measurements array
      if (payload is Map && payload.containsKey('measurements') && payload['measurements'] is List) {
        List<dynamic> measurements = payload['measurements'];
        
        measurements.forEach((measurement) {
          if (measurement is Map && 
              measurement.containsKey('value') && 
              measurement.containsKey('type') && 
              measurement.containsKey('unit')) {
            
            // Extract data
            String type = measurement['type'];
            double value = measurement['value'] is double 
                ? measurement['value'] 
                : double.tryParse(measurement['value'].toString()) ?? 0;
            String unit = measurement['unit'];
            int timestamp = (measurement['timestamp'] is int)
                ? measurement['timestamp']
                : (measurement['timestamp'] is double)
                    ? measurement['timestamp'].toInt()
                    : DateTime.now().millisecondsSinceEpoch ~/ 1000;
            
            // Create sensor reading
            SensorReading reading = SensorReading(
              deviceId: deviceId,
              sensorType: type,
              value: value,
              unit: unit,
              timestamp: timestamp,
            );
            
            // Add to historical data
            setState(() {
              String key = '$deviceId:$type';
              sensorReadings[key] = sensorReadings[key] ?? [];
              
              // Limit to last 50 readings
              if (sensorReadings[key]!.length >= 50) {
                sensorReadings[key]!.removeAt(0);
              }
              
              sensorReadings[key]!.add(reading);
            });
          }
        });
      } 
      // Handle simple data format
      else if (payload is Map && 
               payload.containsKey('value') && 
               payload.containsKey('unit')) {
        
        double value = payload['value'] is double 
            ? payload['value'] 
            : double.tryParse(payload['value'].toString()) ?? 0;
        String unit = payload['unit'];
        int timestamp = payload.containsKey('timestamp') 
            ? (payload['timestamp'] is int ? payload['timestamp'] : payload['timestamp'].toInt())
            : DateTime.now().millisecondsSinceEpoch ~/ 1000;
        
        // Create sensor reading
        SensorReading reading = SensorReading(
          deviceId: deviceId,
          sensorType: topic,
          value: value,
          unit: unit,
          timestamp: timestamp,
        );
        
        // Add to historical data
        setState(() {
          String key = '$deviceId:$topic';
          sensorReadings[key] = sensorReadings[key] ?? [];
          
          // Limit to last 50 readings
          if (sensorReadings[key]!.length >= 50) {
            sensorReadings[key]!.removeAt(0);
          }
          
          sensorReadings[key]!.add(reading);
        });
      }
      
      _addLog('Received data for device $deviceId on topic $topic');
    } catch (e) {
      _addLog('Error processing device data: $e');
    }
  }
  
  // Handle response event
  void _handleResponse(dynamic data) {
    try {
      if (data is Map && data.containsKey('status')) {
        if (data['status'] == 'success') {
          if (data.containsKey('message')) {
            _addLog('Success: ${data['message']}');
          }
          
          // Handle specific actions
          if (data.containsKey('action')) {
            String action = data['action'];
            
            if (action == 'authenticated') {
              _showSnackBar('Authenticated successfully');
              
              // Request devices and topics
              _requestDevicesList();
              _requestTopicsList();
              
              // Subscribe to all data by default
              _subscribeTopic('all');
            }
          }
        }
      }
    } catch (e) {
      _addLog('Error handling response: $e');
    }
  }
  
  // Handle error event
  void _handleError(dynamic data) {
    try {
      if (data is Map && data.containsKey('message')) {
        _showSnackBar('Error: ${data['message']}', true);
        _addLog('Error from server: ${data['message']}');
      }
    } catch (e) {
      _addLog('Error handling error event: $e');
    }
  }
  
  // Handle devices info event
  void _handleDevicesInfo(dynamic data) {
    try {
      if (data is Map && data.containsKey('devices') && data['devices'] is List) {
        List<dynamic> devicesList = data['devices'];
        
        List<DeviceInfo> newDevices = devicesList.map((device) {
          return DeviceInfo(
            id: device['id'] ?? '',
            name: device['name'] ?? 'Unknown',
            isOnline: device['is_online'] ?? false,
            lastSeen: device.containsKey('last_seen') ? device['last_seen'] : 0,
            capabilities: device['capabilities']?.toString() ?? '',
          );
        }).toList();
        
        setState(() {
          devices = newDevices;
        });
        
        _addLog('Received info for ${devices.length} devices');
      }
    } catch (e) {
      _addLog('Error handling devices info: $e');
    }
  }
  
  // Handle topics list event
  void _handleTopicsList(dynamic data) {
    try {
      if (data is Map && data.containsKey('topics') && data['topics'] is List) {
        List<dynamic> topicsList = data['topics'];
        
        setState(() {
          topics = topicsList.map((topic) => topic['name'].toString()).toList();
        });
        
        _addLog('Received list of ${topics.length} topics');
      }
    } catch (e) {
      _addLog('Error handling topics list: $e');
    }
  }
  
  // Add log message
  void _addLog(String message) {
    setState(() {
      if (logs.length >= 100) logs.removeAt(0);
      logs.add('[${DateFormat('HH:mm:ss').format(DateTime.now())}] $message');
    });
  }
  
  // Show snackbar
  void _showSnackBar(String message, [bool isError = false]) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : null,
        duration: Duration(seconds: 3),
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('IoT Data Client'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(icon: Icon(Icons.devices), text: 'Devices'),
            Tab(icon: Icon(Icons.topic), text: 'Topics'),
            Tab(icon: Icon(Icons.show_chart), text: 'Charts'),
            Tab(icon: Icon(Icons.history), text: 'Logs'),
          ],
        ),
        actions: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 8.0),
            alignment: Alignment.center,
            child: Text(
              connectionStatus,
              style: TextStyle(
                color: isConnected ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildDevicesTab(),
          _buildTopicsTab(),
          _buildChartsTab(),
          _buildLogsTab(),
        ],
      ),
      bottomNavigationBar: _buildConnectionBar(),
    );
  }
  
  // Connection bar at bottom
  Widget _buildConnectionBar() {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _serverController,
              decoration: InputDecoration(
                labelText: 'Server',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 0),
              ),
            ),
          ),
          SizedBox(width: 8),
          ElevatedButton(
            onPressed: isConnected ? null : connectToServer,
            child: Text('Connect'),
          ),
          SizedBox(width: 8),
          ElevatedButton(
            onPressed: isConnected ? () => socket?.disconnect() : null,
            child: Text('Disconnect'),
            style: ElevatedButton.styleFrom(
              primary: Colors.red,
            ),
          ),
        ],
      ),
    );
  }
  
  // Devices tab
  Widget _buildDevicesTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Devices (${devices.length})',
                  style: Theme.of(context).textTheme.headline6,
                ),
              ),
              IconButton(
                icon: Icon(Icons.refresh),
                onPressed: _requestDevicesList,
                tooltip: 'Refresh Devices',
              ),
            ],
          ),
        ),
        Expanded(
          child: devices.isEmpty
              ? Center(child: Text('No devices available'))
              : ListView.builder(
                  itemCount: devices.length,
                  itemBuilder: (context, index) {
                    DeviceInfo device = devices[index];
                    return _buildDeviceCard(device);
                  },
                ),
        ),
      ],
    );
  }
  
  // Device card
  Widget _buildDeviceCard(DeviceInfo device) {
    return Card(
      margin: EdgeInsets.all(8.0),
      child: ExpansionTile(
        leading: Icon(
          Icons.device_hub,
          color: device.isOnline ? Colors.green : Colors.grey,
        ),
        title: Text(device.name),
        subtitle: Text(
          'Last seen: ${device.lastSeen > 0 ? _formatTimestamp(device.lastSeen) : 'Never'}',
        ),
        children: [
          Padding(
            padding: EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Device ID: ${device.id}'),
                if (device.capabilities.isNotEmpty)
                  Text('Capabilities: ${device.capabilities}'),
                SizedBox(height: 8),
                Text('Sensor Data:', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 4),
                _buildDeviceSensorData(device.id),
                SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    ElevatedButton.icon(
                      icon: Icon(Icons.info),
                      label: Text('Status'),
                      onPressed: () => _sendCommand(device.id, 'status'),
                    ),
                    ElevatedButton.icon(
                      icon: Icon(Icons.restart_alt),
                      label: Text('Restart'),
                      onPressed: () => _sendCommand(device.id, 'restart'),
                      style: ElevatedButton.styleFrom(
                        primary: Colors.orange,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  // Device sensor data
  Widget _buildDeviceSensorData(String deviceId) {
    if (!deviceData.containsKey(deviceId)) {
      return Text('No data available');
    }
    
    Map<String, dynamic> data = deviceData[deviceId];
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: data.entries.map((entry) {
        String topic = entry.key;
        dynamic payload = entry.value;
        
        if (payload is Map && payload.containsKey('measurements') && payload['measurements'] is List) {
          List<dynamic> measurements = payload['measurements'];
          
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Topic: $topic', style: TextStyle(fontWeight: FontWeight.bold)),
              ...measurements.map((measurement) {
                if (measurement is Map) {
                  return Padding(
                    padding: const EdgeInsets.only(left: 16.0, bottom: 4.0),
                    child: Text(
                      '${measurement['type']}: ${measurement['value']} ${measurement['unit']}',
                      style: TextStyle(fontSize: 14),
                    ),
                  );
                }
                return SizedBox.shrink();
              }).toList(),
              Divider(),
            ],
          );
        } else if (payload is Map && payload.containsKey('value') && payload.containsKey('unit')) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 4.0),
            child: Text(
              '$topic: ${payload['value']} ${payload['unit']}',
              style: TextStyle(fontSize: 14),
            ),
          );
        }
        
        return SizedBox.shrink();
      }).toList(),
    );
  }
  
  // Topics tab
  Widget _buildTopicsTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _topicController,
                  decoration: InputDecoration(
                    labelText: 'Subscribe to topic',
                    border: OutlineInputBorder(),
                    hintText: 'Enter topic name',
                    suffixIcon: IconButton(
                      icon: Icon(Icons.add),
                      onPressed: () {
                        if (_topicController.text.isNotEmpty) {
                          _subscribeTopic(_topicController.text);
                        }
                      },
                    ),
                  ),
                  onSubmitted: (value) {
                    if (value.isNotEmpty) {
                      _subscribeTopic(value);
                    }
                  },
                ),
              ),
              SizedBox(width: 8),
              IconButton(
                icon: Icon(Icons.refresh),
                onPressed: _requestTopicsList,
                tooltip: 'Refresh Topics',
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Subscribed Topics:', style: TextStyle(fontWeight: FontWeight.bold)),
              SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: subscribedTopics.map((topic) {
                  return Chip(
                    label: Text(topic),
                    onDeleted: () => _unsubscribeTopic(topic),
                    backgroundColor: Theme.of(context).primaryColor.withOpacity(0.1),
                  );
                }).toList(),
              ),
              Divider(),
              Text('Available Topics:', style: TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        Expanded(
          child: topics.isEmpty
              ? Center(child: Text('No topics available'))
              : ListView.builder(
                  itemCount: topics.length,
                  itemBuilder: (context, index) {
                    String topic = topics[index];
                    bool isSubscribed = subscribedTopics.contains(topic);
                    
                    return ListTile(
                      title: Text(topic),
                      trailing: IconButton(
                        icon: Icon(
                          isSubscribed ? Icons.notifications_active : Icons.notifications_none,
                          color: isSubscribed ? Colors.green : null,
                        ),
                        onPressed: () {
                          if (isSubscribed) {
                            _unsubscribeTopic(topic);
                          } else {
                            _subscribeTopic(topic);
                          }
                        },
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
  
  // Charts tab
  Widget _buildChartsTab() {
    if (sensorReadings.isEmpty) {
      return Center(child: Text('No sensor data available for charts'));
    }
    
    return ListView.builder(
      itemCount: sensorReadings.length,
      itemBuilder: (context, index) {
        String key = sensorReadings.keys.elementAt(index);
        List<String> parts = key.split(':');
        String deviceId = parts[0];
        String sensorType = parts[1];
        
        // Find device name
        String deviceName = 'Unknown';
        for (var device in devices) {
          if (device.id == deviceId) {
            deviceName = device.name;
            break;
          }
        }
        
        return Card(
          margin: EdgeInsets.all(8.0),
          child: Padding(
            padding: EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$deviceName - ${_formatSensorType(sensorType)}',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                SizedBox(height: 8),
                Container(
                  height: 200,
                  child: _buildChart(sensorReadings[key]!),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
  
  // Build chart for sensor readings
  Widget _buildChart(List<SensorReading> readings) {
    List<charts.Series<SensorReading, DateTime>> series = [
      charts.Series<SensorReading, DateTime>(
        id: 'Readings',
        colorFn: (_, __) => charts.MaterialPalette.blue.shadeDefault,
        domainFn: (SensorReading reading, _) => 
            DateTime.fromMillisecondsSinceEpoch(reading.timestamp * 1000),
        measureFn: (SensorReading reading, _) => reading.value,
        data: readings,
      )
    ];
    
    return charts.TimeSeriesChart(
      series,
      animate: false,
      dateTimeFactory: const charts.LocalDateTimeFactory(),
      primaryMeasureAxis: charts.NumericAxisSpec(
        tickProviderSpec: charts.BasicNumericTickProviderSpec(
          desiredTickCount: 5,
        ),
      ),
      domainAxis: charts.DateTimeAxisSpec(
        tickFormatterSpec: charts.AutoDateTimeTickFormatterSpec(
          day: charts.TimeFormatterSpec(
            format: 'HH:mm',
            transitionFormat: 'HH:mm',
          ),
        ),
      ),
    );
  }
  
  // Logs tab
  Widget _buildLogsTab() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Event Logs',
                  style: Theme.of(context).textTheme.headline6,
                ),
              ),
              IconButton(
                icon: Icon(Icons.cleaning_services),
                onPressed: () {
                  setState(() {
                    logs.clear();
                  });
                },
                tooltip: 'Clear Logs',
              ),
            ],
          ),
        ),
        Expanded(
          child: logs.isEmpty
              ? Center(child: Text('No logs available'))
              : ListView.builder(
                  itemCount: logs.length,
                  reverse: true,
                  itemBuilder: (context, index) {
                    String log = logs[logs.length - 1 - index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                      child: Text(
                        log,
                        style: TextStyle(
                          fontSize: 12,
                          fontFamily: 'monospace',
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
  
  // Format timestamp
  String _formatTimestamp(int timestamp) {
    DateTime dateTime = DateTime.fromMillisecondsSinceEpoch(timestamp * 1000);
    return DateFormat('yyyy-MM-dd HH:mm:ss').format(dateTime);
  }
  
  // Format sensor type
  String _formatSensorType(String type) {
    return type.replaceFirst(type[0], type[0].toUpperCase()).replaceAll('_', ' ');
  }
}

// Model classes
class DeviceInfo {
  final String id;
  final String name;
  final bool isOnline;
  final int lastSeen;
  final String capabilities;
  
  DeviceInfo({
    required this.id,
    required this.name,
    required this.isOnline,
    required this.lastSeen,
    required this.capabilities,
  });
}

class SensorReading {
  final String deviceId;
  final String sensorType;
  final double value;
  final String unit;
  final int timestamp;
  
  SensorReading({
    required this.deviceId,
    required this.sensorType,
    required this.value,
    required this.unit,
    required this.timestamp,
  });
} 