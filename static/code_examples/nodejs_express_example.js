const express = require('express');
const path = require('path');
const axios = require('axios');

const app = express();
const port = 5001;

// Configuration
const API_KEY = 'YOUR_API_KEY';
const IOT_SERVER_URL = 'http://your_server_ip:5000';

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/', async (req, res) => {
  try {
    const data = await getLatestData();
    res.render('index.ejs', { data });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).send('Server error');
  }
});

app.get('/api/latest-data', async (req, res) => {
  try {
    const data = await getLatestData();
    res.json(data);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to fetch data' });
  }
});

async function getLatestData() {
  // Set up headers with API key
  const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  };
  
  try {
    // Get device list
    const deviceResponse = await axios.get(`${IOT_SERVER_URL}/api/devices`, { headers });
    const devices = deviceResponse.data.devices;
    
    // Get topic list
    const topicResponse = await axios.get(`${IOT_SERVER_URL}/api/topics`, { headers });
    const topics = topicResponse.data.topics;
    
    // Get latest data for each device and topic
    const result = [];
    for (const device of devices) {
      for (const topic of topics) {
        try {
          const dataResponse = await axios.get(
            `${IOT_SERVER_URL}/api/data?device=${device.name}&topic=${topic.name}&limit=1`, 
            { headers }
          );
          const data = dataResponse.data.data;
          if (data && data.length > 0) {
            result.push({
              device: device.name,
              topic: topic.name,
              payload: data[0].payload,
              timestamp: data[0].timestamp
            });
          }
        } catch (error) {
          console.error(`Error fetching data for ${device.name}/${topic.name}:`, error.message);
        }
      }
    }
    return result;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
}

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

// EJS template (views/index.ejs):
/*
<!DOCTYPE html>
<html>
<head>
  <title>IoT Data Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .card {
      transition: transform 0.3s;
    }
    .card:hover {
      transform: translateY(-5px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
  </style>
</head>
<body>
  <div class="container mt-4">
    <h1>IoT Data Dashboard</h1>
    
    <div class="row mt-4">
      <% data.forEach(function(item) { %>
        <div class="col-md-4 mb-3">
          <div class="card">
            <div class="card-header">
              <%= item.device %> - <%= item.topic %>
            </div>
            <div class="card-body">
              <h5 class="card-title">
                <%= item.payload.value %>
                <% if (item.payload.unit) { %>
                  <%= item.payload.unit %>
                <% } %>
              </h5>
              <p class="card-text text-muted">
                <small><%= item.timestamp %></small>
              </p>
            </div>
          </div>
        </div>
      <% }); %>
    </div>
    
    <button id="refreshBtn" class="btn btn-primary mt-3">Refresh Data</button>
  </div>
  
  <script>
    document.getElementById('refreshBtn').addEventListener('click', function() {
      fetch('/api/latest-data')
        .then(response => response.json())
        .then(data => {
          console.log(data);
          location.reload(); // Simple solution is to refresh the page
        })
        .catch(error => console.error('Error fetching data:', error));
    });
  </script>
</body>
</html>
*/
