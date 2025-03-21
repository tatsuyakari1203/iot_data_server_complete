from flask import Flask, render_template, jsonify
import requests
import json

app = Flask(__name__)

# Configuration
API_KEY = "YOUR_API_KEY"
IOT_SERVER_URL = "http://your_server_ip:5000"

@app.route('/')
def index():
    return render_template('index.html', data=get_latest_data())

@app.route('/api/latest-data')
def api_latest_data():
    return jsonify(get_latest_data())

def get_latest_data():
    # Set up headers with API key
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Get device list
        device_response = requests.get(
            f"{IOT_SERVER_URL}/api/devices", 
            headers=headers
        )
        device_response.raise_for_status()
        devices = device_response.json()["devices"]
        
        # Get topic list
        topic_response = requests.get(
            f"{IOT_SERVER_URL}/api/topics", 
            headers=headers
        )
        topic_response.raise_for_status()
        topics = topic_response.json()["topics"]
        
        # Get latest data for each device and topic
        result = []
        for device in devices:
            for topic in topics:
                data_response = requests.get(
                    f"{IOT_SERVER_URL}/api/data?device={device['name']}&topic={topic['name']}&limit=1", 
                    headers=headers
                )
                if data_response.status_code == 200:
                    data = data_response.json()["data"]
                    if data:
                        result.append({
                            "device": device["name"],
                            "topic": topic["name"],
                            "payload": data[0]["payload"],
                            "timestamp": data[0]["timestamp"]
                        })
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []

# HTML template (index.html):
"""
<!DOCTYPE html>
<html>
<head>
    <title>IoT Data Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <h1>IoT Data Dashboard</h1>
        
        <div class="row mt-4">
            {% for item in data %}
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-header">
                        {{ item.device }} - {{ item.topic }}
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{{ item.payload.value }}
                            {% if item.payload.unit %}{{ item.payload.unit }}{% endif %}
                        </h5>
                        <p class="card-text text-muted">
                            <small>{{ item.timestamp }}</small>
                        </p>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <button id="refreshBtn" class="btn btn-primary mt-3">Refresh Data</button>
    </div>
    
    <script>
        document.getElementById('refreshBtn').addEventListener('click', function() {
            fetch('/api/latest-data')
                .then(response => response.json())
                .then(data => {
                    // Here you'd update the UI with the refreshed data
                    console.log(data);
                    location.reload(); // Simple solution is to refresh the page
                });
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
