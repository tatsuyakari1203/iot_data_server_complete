import requests
import json
import time
from datetime import datetime, timedelta
import unittest
from tabulate import tabulate
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IoTDataRetrievalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configuration
        cls.API_KEY = "8a679613-019f-4b88-9068-da10f09dcdd2"
        cls.API_BASE_URL = "https://iot.karis.cloud/api"
        cls.headers = {
            "Content-Type": "application/json",
            "X-API-Key": cls.API_KEY
        }

    def setUp(self):
        """Setup before each test"""
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def test_01_api_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{self.API_BASE_URL}/devices")
            self.assertEqual(response.status_code, 200)
            logger.info("API connectivity test passed")
        except requests.exceptions.RequestException as e:
            logger.error(f"API connectivity test failed: {e}")
            raise

    def test_02_get_devices(self):
        """Test retrieving all devices"""
        response = self.session.get(f"{self.API_BASE_URL}/devices")
        devices = response.json().get('devices', [])
        
        self.assertIsInstance(devices, list)
        if devices:
            logger.info("\nDevices found:")
            device_table = [[d.get('id', 'N/A'), d.get('name', 'N/A'), d.get('description', 'N/A')] 
                          for d in devices]
            print(tabulate(device_table, headers=["ID", "Name", "Description"], tablefmt="grid"))
        else:
            logger.warning("No devices found")

    def test_03_get_topics(self):
        """Test retrieving all topics"""
        response = self.session.get(f"{self.API_BASE_URL}/topics")
        topics = response.json().get('topics', [])
        
        self.assertIsInstance(topics, list)
        if topics:
            logger.info("\nTopics found:")
            topic_table = [[t.get('id', 'N/A'), t.get('name', 'N/A'), t.get('description', 'N/A')] 
                         for t in topics]
            print(tabulate(topic_table, headers=["ID", "Name", "Description"], tablefmt="grid"))
        else:
            logger.warning("No topics found")

    def test_04_get_telemetry_data(self):
        """Test retrieving telemetry data with different parameters"""
        test_cases = [
            {"params": {}, "name": "all data"},
            {"params": {"device": "test_device_1"}, "name": "specific device"},
            {"params": {"topic": "temperature"}, "name": "specific topic"},
            {"params": {"limit": 5}, "name": "limited records"},
            {"params": {"device": "test_device_1", "topic": "temperature", "limit": 3}, 
             "name": "combined filters"}
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                response = self.session.get(
                    f"{self.API_BASE_URL}/data",
                    params=case["params"]
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json().get('data', [])
                self.assertIsInstance(data, list)
                
                logger.info(f"\nTelemetry data for {case['name']}:")
                if data:
                    self._display_telemetry_data(data)
                else:
                    logger.warning(f"No data found for {case['name']}")

    def test_05_error_handling(self):
        """Test error handling with invalid requests"""
        test_cases = [
            {
                "params": {"device": "nonexistent_device"},
                "name": "nonexistent device"
            },
            {
                "params": {"limit": "invalid"},
                "name": "invalid limit parameter"
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                response = self.session.get(
                    f"{self.API_BASE_URL}/data",
                    params=case["params"]
                )
                logger.info(f"Testing error handling for {case['name']}")
                self.assertEqual(response.status_code, 200)  # Server always returns 200
                data = response.json().get('data', [])
                self.assertEqual(len(data), 0)  # Invalid requests should return empty data
                logger.info(f"✓ {case['name']} test passed - received empty data array")

    def _display_telemetry_data(self, data):
        """Helper method to display telemetry data in a table format"""
        table_data = []
        for item in data:
            payload = item.get('payload', {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {}

            row = [
                item.get('id', 'N/A'),
                item.get('device_name', 'N/A'),
                item.get('topic_name', 'N/A'),
                item.get('timestamp', 'N/A'),
                payload.get('temperature', payload.get('value', 'N/A')),
                payload.get('humidity', 'N/A'),
                payload.get('unit', 'N/A')
            ]
            table_data.append(row)

        headers = ["ID", "Device", "Topic", "Timestamp", "Temperature", "Humidity", "Unit"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

def run_tests():
    """Run the test suite with a custom test runner"""
    suite = unittest.TestLoader().loadTestsFromTestCase(IoTDataRetrievalTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    print("=== IoT Data Retrieval Test Suite ===")
    print("Running all tests...")
    run_tests() 