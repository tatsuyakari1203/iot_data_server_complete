/**
 * Real-time updates for IoT Data Server
 * This script handles WebSocket connections and periodic data fetching
 */

// Configuration
const config = {
    // Update intervals in milliseconds
    updateIntervals: {
        stats: 5000,           // Update statistics every 5 seconds
        latestData: 3000,      // Update latest data every 3 seconds
        mqttStatus: 10000      // Update MQTT status every 10 seconds
    },
    // API endpoints
    api: {
        stats: '/api/stats',
        latestData: '/api/latest_data',
        mqttStatus: '/api/mqtt_status'
    }
};

// Store for active update intervals
const activeIntervals = {};

// Store for last data timestamp to detect changes
let lastDataTimestamp = '';

/**
 * Initialize real-time updates
 */
function initRealTimeUpdates() {
    console.log('Initializing real-time updates...');
    
    // Initialize MQTT WebSocket connection if available on the page
    initMqttWebSocket();
    
    // Initialize periodic updates for different components
    initPeriodicUpdates();
    
    // Add event listeners for page visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);
}

/**
 * Initialize MQTT WebSocket connection
 */
function initMqttWebSocket() {
    // Check if MQTT broker info is available on the page
    const mqttInfoElement = document.getElementById('mqtt-broker-info');
    if (!mqttInfoElement) return;
    
    // Extract MQTT broker information
    const brokerHost = mqttInfoElement.dataset.host;
    const brokerPort = mqttInfoElement.dataset.wsPort || '8083'; // WebSocket port
    
    // Create WebSocket connection if broker info is available
    if (brokerHost) {
        console.log(`Connecting to MQTT broker via WebSocket: ${brokerHost}:${brokerPort}`);
        // WebSocket connection will be implemented here if needed
    }
}

/**
 * Initialize periodic updates for different components
 */
function initPeriodicUpdates() {
    // Update statistics
    if (document.querySelector('.stat-card')) {
        updateStats();
        activeIntervals.stats = setInterval(updateStats, config.updateIntervals.stats);
    }
    
    // Update latest data
    if (document.querySelector('#latest-data-table')) {
        updateLatestData();
        activeIntervals.latestData = setInterval(updateLatestData, config.updateIntervals.latestData);
    }
    
    // Update MQTT status
    if (document.querySelector('#mqtt-status')) {
        updateMqttStatus();
        activeIntervals.mqttStatus = setInterval(updateMqttStatus, config.updateIntervals.mqttStatus);
    }
}

/**
 * Handle page visibility changes to conserve resources
 */
function handleVisibilityChange() {
    if (document.hidden) {
        // Page is hidden, pause updates
        Object.values(activeIntervals).forEach(interval => clearInterval(interval));
    } else {
        // Page is visible again, resume updates
        initPeriodicUpdates();
    }
}

/**
 * Update statistics cards
 */
async function updateStats() {
    try {
        const response = await fetch(config.api.stats);
        if (!response.ok) throw new Error('Failed to fetch statistics');
        
        const data = await response.json();
        
        // Update each statistic card
        updateStatCard('client_count', data.stats.client_count);
        updateStatCard('topic_count', data.stats.topic_count);
        updateStatCard('device_count', data.stats.device_count);
        updateStatCard('data_count', data.stats.data_count);
    } catch (error) {
        console.error('Error updating statistics:', error);
    }
}

/**
 * Update a specific statistic card
 */
function updateStatCard(id, value) {
    const element = document.querySelector(`.stat-card .count[data-id="${id}"]`);
    if (element && element.textContent !== value.toString()) {
        // Add animation class
        element.classList.add('update-flash');
        // Update value
        element.textContent = value;
        // Remove animation class after animation completes
        setTimeout(() => {
            element.classList.remove('update-flash');
        }, 1000);
    }
}

/**
 * Update latest telemetry data table
 */
async function updateLatestData() {
    try {
        const response = await fetch(config.api.latestData);
        if (!response.ok) throw new Error('Failed to fetch latest data');
        
        const data = await response.json();
        const tableBody = document.querySelector('#latest-data-table tbody');
        
        if (!tableBody) return;
        
        // Get the data indicator element
        const dataIndicator = document.getElementById('data-indicator');
        
        // Check if there's new data by comparing with the first item's timestamp
        let hasNewData = false;
        if (data.latest_data.length > 0) {
            const newTimestamp = data.latest_data[0].timestamp;
            if (newTimestamp !== lastDataTimestamp) {
                lastDataTimestamp = newTimestamp;
                hasNewData = true;
                
                // Activate the indicator
                if (dataIndicator) {
                    dataIndicator.classList.add('active');
                    // Remove the active class after 2 seconds
                    setTimeout(() => {
                        dataIndicator.classList.remove('active');
                    }, 2000);
                }
            }
        }
        
        // Clear "No data available" row if it exists
        const noDataRow = tableBody.querySelector('tr td[colspan="4"].text-center');
        if (noDataRow && data.latest_data.length > 0) {
            tableBody.innerHTML = '';
        }
        
        // Update or add new rows
        if (data.latest_data.length > 0) {
            let newHtml = '';
            
            data.latest_data.forEach(item => {
                newHtml += `
                <tr class="${hasNewData ? 'new-data-row' : ''}">
                    <td>${item.timestamp}</td>
                    <td>${item.device_id}</td>
                    <td>${item.topic_id}</td>
                    <td><code>${typeof item.payload === 'object' ? JSON.stringify(item.payload) : item.payload}</code></td>
                </tr>`;
            });
            
            // Replace table content
            tableBody.innerHTML = newHtml;
            
            // Animate new rows
            if (hasNewData) {
                setTimeout(() => {
                    document.querySelectorAll('.new-data-row').forEach(row => {
                        row.classList.remove('new-data-row');
                    });
                }, 1000);
            }
        } else if (tableBody.children.length === 0) {
            // If no data and table is empty
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center">No data available</td></tr>';
        }
    } catch (error) {
        console.error('Error updating latest data:', error);
    }
}

/**
 * Update MQTT broker status
 */
async function updateMqttStatus() {
    try {
        const response = await fetch(config.api.mqttStatus);
        if (!response.ok) throw new Error('Failed to fetch MQTT status');
        
        const data = await response.json();
        const statusElement = document.querySelector('#mqtt-status');
        
        if (!statusElement) return;
        
        // Update connection status
        const statusBadge = statusElement.querySelector('.badge');
        if (statusBadge) {
            if (data.mqtt_info.is_connected) {
                statusBadge.textContent = 'Connected';
                statusBadge.classList.remove('bg-danger');
                statusBadge.classList.add('bg-success');
                statusElement.querySelector('i').classList.remove('text-danger');
                statusElement.querySelector('i').classList.add('text-success');
            } else {
                statusBadge.textContent = 'Disconnected';
                statusBadge.classList.remove('bg-success');
                statusBadge.classList.add('bg-danger');
                statusElement.querySelector('i').classList.remove('text-success');
                statusElement.querySelector('i').classList.add('text-danger');
            }
        }
    } catch (error) {
        console.error('Error updating MQTT status:', error);
    }
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initRealTimeUpdates);

// Mobile sidebar management
document.addEventListener('DOMContentLoaded', function() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const sidebarMenu = document.getElementById('sidebarMenu');
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    
    // Toggle sidebar when navbar toggler is clicked
    if (navbarToggler && sidebarMenu) {
        navbarToggler.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                // Toggle sidebar visibility
                if (sidebarMenu.classList.contains('show')) {
                    sidebarMenu.classList.remove('show');
                } else {
                    sidebarMenu.classList.add('show');
                }
            }
        });
    }
    
    // Close sidebar when a link is clicked (mobile only)
    if (sidebarLinks && sidebarMenu) {
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                // Check if we're on mobile view
                if (window.innerWidth < 768) {
                    sidebarMenu.classList.remove('show');
                }
            });
        });
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768 && sidebarMenu) {
            sidebarMenu.classList.remove('show');
        }
    });
});
