import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

void main() {
  runApp(const IoTApp());
}

class IoTApp extends StatelessWidget {
  const IoTApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'IoT Data Dashboard',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // Configuration
  final String apiKey = 'YOUR_API_KEY';
  final String serverUrl = 'http://your_server_ip:5000';
  
  List<IoTData> iotData = [];
  bool isLoading = true;
  Timer? refreshTimer;

  @override
  void initState() {
    super.initState();
    fetchData();
    
    // Set up a timer to refresh data every 30 seconds
    refreshTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      fetchData();
    });
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchData() async {
    setState(() {
      isLoading = true;
    });

    try {
      // Set up headers with API key
      final headers = {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      };

      // Get devices
      final deviceResponse = await http.get(
        Uri.parse('$serverUrl/api/devices'),
        headers: headers,
      );
      final deviceData = json.decode(deviceResponse.body);
      final devices = List<dynamic>.from(deviceData['devices']);

      // Get topics
      final topicResponse = await http.get(
        Uri.parse('$serverUrl/api/topics'),
        headers: headers,
      );
      final topicData = json.decode(topicResponse.body);
      final topics = List<dynamic>.from(topicData['topics']);

      // Get data for each device and topic
      List<IoTData> newData = [];
      for (final device in devices) {
        for (final topic in topics) {
          try {
            final dataResponse = await http.get(
              Uri.parse(
                '$serverUrl/api/data?device=${device['name']}&topic=${topic['name']}&limit=1',
              ),
              headers: headers,
            );
            
            final responseData = json.decode(dataResponse.body);
            final dataList = List<dynamic>.from(responseData['data']);
            
            if (dataList.isNotEmpty) {
              newData.add(IoTData(
                device: device['name'],
                topic: topic['name'],
                value: dataList[0]['payload']['value'].toString(),
                unit: dataList[0]['payload']['unit'] ?? '',
                timestamp: DateTime.parse(dataList[0]['timestamp']),
              ));
            }
          } catch (e) {
            print('Error fetching data for ${device['name']}/${topic['name']}: $e');
          }
        }
      }

      setState(() {
        iotData = newData;
        isLoading = false;
      });
    } catch (e) {
      print('Error: $e');
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('IoT Data Dashboard'),
      ),
      body: RefreshIndicator(
        onRefresh: fetchData,
        child: isLoading
            ? const Center(child: CircularProgressIndicator())
            : iotData.isEmpty
                ? const Center(child: Text('No data available'))
                : GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 1.5,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                    ),
                    itemCount: iotData.length,
                    itemBuilder: (context, index) {
                      final data = iotData[index];
                      return Card(
                        elevation: 2,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${data.device} - ${data.topic}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 8),
                              Expanded(
                                child: Center(
                                  child: Text(
                                    '${data.value} ${data.unit}',
                                    style: const TextStyle(
                                      fontSize: 24,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                              ),
                              Text(
                                DateFormat('yyyy-MM-dd HH:mm:ss').format(data.timestamp),
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: fetchData,
        tooltip: 'Refresh',
        child: const Icon(Icons.refresh),
      ),
    );
  }
}

class IoTData {
  final String device;
  final String topic;
  final String value;
  final String unit;
  final DateTime timestamp;

  IoTData({
    required this.device,
    required this.topic,
    required this.value,
    required this.unit,
    required this.timestamp,
  });
}
