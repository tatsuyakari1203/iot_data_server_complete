import sqlite3
import uuid
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Define Vietnam timezone
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

# Get database path from environment variable or use default
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data.db')

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the schema."""
    if not os.path.exists(DATABASE_PATH):
        conn = get_db_connection()
        with open('schema.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print(f"Database initialized at {DATABASE_PATH}")

def generate_api_key():
    """Generate a unique API key."""
    return str(uuid.uuid4())

# Client operations
def create_client(name, api_key=None):
    """Create a new client with a provided or generated API key."""
    conn = get_db_connection()
    if api_key is None:
        api_key = generate_api_key()
    conn.execute('INSERT INTO clients (name, api_key) VALUES (?, ?)',
                (name, api_key))
    conn.commit()
    client_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return client_id, api_key

def get_client_by_api_key(api_key):
    """Get a client by their API key."""
    conn = get_db_connection()
    client = conn.execute('SELECT * FROM clients WHERE api_key = ?',
                        (api_key,)).fetchone()
    conn.close()
    return dict(client) if client else None

def get_all_clients():
    """Get all clients."""
    conn = get_db_connection()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    return [dict(client) for client in clients]

def delete_client(client_id):
    """
    Delete a client and all associated data.
    
    Args:
        client_id (int): ID of the client to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Check if client exists
        client = conn.execute(
            'SELECT * FROM clients WHERE id = ?', (client_id,)
        ).fetchone()
        
        if not client:
            print(f"Attempted to delete non-existent client with ID {client_id}")
            conn.rollback()
            conn.close()
            return False
            
        # No need to explicitly delete devices, topics or telemetry data
        # as they will be automatically deleted due to ON DELETE CASCADE constraints
        
        # Delete the client
        conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        
        # Commit the transaction
        conn.commit()
        print(f"Successfully deleted client ID {client_id} and all associated data")
        return True
    except sqlite3.Error as e:
        print(f"Error deleting client: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_client_api_key(client_id, new_api_key):
    """
    Update a client's API key.
    
    Args:
        client_id (int): ID of the client to update
        new_api_key (str): New API key to set
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Check if client exists
        client = conn.execute(
            'SELECT * FROM clients WHERE id = ?', (client_id,)
        ).fetchone()
        
        if not client:
            print(f"Attempted to update API key for non-existent client with ID {client_id}")
            conn.rollback()
            conn.close()
            return False
            
        # Update API key
        conn.execute('UPDATE clients SET api_key = ? WHERE id = ?', 
                    (new_api_key, client_id))
        
        # Commit the transaction
        conn.commit()
        print(f"Successfully updated API key for client ID {client_id}")
        return True
    except sqlite3.Error as e:
        print(f"Error updating client API key: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Topic operations
def create_topic(name, description, client_id):
    """Create a new topic."""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO topics (name, description, client_id) VALUES (?, ?, ?)',
            (name, description, client_id)
        )
        conn.commit()
        topic_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return topic_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_topic_by_name(name, client_id=None):
    """
    Get a topic by its name.
    
    Args:
        name (str): Name of the topic to find
        client_id (int, optional): If provided, only look for topics belonging to this client
        
    Returns:
        dict or None: Dictionary containing topic data if found, None otherwise
    """
    conn = get_db_connection()
    
    if client_id is not None:
        topic = conn.execute(
            'SELECT * FROM topics WHERE name = ? AND client_id = ?', 
            (name, client_id)
        ).fetchone()
    else:
        topic = conn.execute('SELECT * FROM topics WHERE name = ?', (name,)).fetchone()
        
    conn.close()
    return dict(topic) if topic else None

def get_all_topics(client_id=None):
    """Get all topics, optionally filtered by client_id."""
    conn = get_db_connection()
    if client_id:
        topics = conn.execute('SELECT * FROM topics WHERE client_id = ?', 
                            (client_id,)).fetchall()
    else:
        topics = conn.execute('SELECT * FROM topics').fetchall()
    conn.close()
    return [dict(topic) for topic in topics]

def delete_topic(topic_id, client_id=None):
    """
    Delete a topic.
    
    Args:
        topic_id (int): ID of the topic to delete
        client_id (int, optional): If provided, ensures the topic belongs to this client
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Check if the topic exists and belongs to the client (if client_id provided)
        if client_id is not None:
            topic = conn.execute(
                'SELECT * FROM topics WHERE id = ? AND client_id = ?',
                (topic_id, client_id)
            ).fetchone()
            
            if not topic:
                print(f"Warning: Attempted to delete topic ID {topic_id} not owned by client {client_id}")
                conn.rollback()
                conn.close()
                return False
        else:
            # Just check if topic exists
            topic = conn.execute(
                'SELECT * FROM topics WHERE id = ?',
                (topic_id,)
            ).fetchone()
            
            if not topic:
                print(f"Warning: Attempted to delete non-existent topic ID {topic_id}")
                conn.rollback()
                conn.close()
                return False
        
        # Delete the topic (this will cascade delete all related telemetry data)
        conn.execute('DELETE FROM topics WHERE id = ?', (topic_id,))
        
        # Commit the transaction
        conn.commit()
        print(f"Successfully deleted topic ID {topic_id}")
        return True
    except sqlite3.Error as e:
        print(f"Error deleting topic: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Device operations
def create_device(name, description, client_id):
    """Create a new device."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO devices (name, description, client_id) VALUES (?, ?, ?)',
        (name, description, client_id)
    )
    conn.commit()
    device_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return device_id

def get_device_by_name(name, client_id):
    """Get a device by its name and client_id."""
    conn = get_db_connection()
    device = conn.execute(
        'SELECT * FROM devices WHERE name = ? AND client_id = ?',
        (name, client_id)
    ).fetchone()
    conn.close()
    return dict(device) if device else None

def get_all_devices(client_id=None):
    """Get all devices, optionally filtered by client_id."""
    conn = get_db_connection()
    if client_id:
        devices = conn.execute(
            'SELECT * FROM devices WHERE client_id = ?', 
            (client_id,)
        ).fetchall()
    else:
        devices = conn.execute('SELECT * FROM devices').fetchall()
    conn.close()
    return [dict(device) for device in devices]

def update_device_last_seen(device_id):
    """Update the last_seen time for a device."""
    if not device_id:
        print("Error: device_id must be provided to update last_seen")
        return False
        
    conn = get_db_connection()
    try:
        conn.execute(
            'UPDATE devices SET last_seen = ? WHERE id = ?',
            (datetime.now(VN_TZ).isoformat(), device_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error updating device last_seen: {e}")
        return False
    finally:
        conn.close()

def delete_device(device_id, client_id=None):
    """
    Delete a device.
    
    Args:
        device_id (int): ID of the device to delete
        client_id (int, optional): If provided, ensures the device belongs to this client
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Check if the device exists
        if client_id is not None:
            device = conn.execute(
                'SELECT * FROM devices WHERE id = ? AND client_id = ?',
                (device_id, client_id)
            ).fetchone()
            
            if not device:
                print(f"Warning: Attempted to delete device ID {device_id} not owned by client {client_id}")
                conn.rollback()
                conn.close()
                return False
        else:
            # Just check if device exists
            device = conn.execute(
                'SELECT * FROM devices WHERE id = ?',
                (device_id,)
            ).fetchone()
            
            if not device:
                print(f"Warning: Attempted to delete non-existent device ID {device_id}")
                conn.rollback()
                conn.close()
                return False
        
        # Delete the device (this will cascade delete all related telemetry data)
        conn.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        
        # Commit the transaction
        conn.commit()
        print(f"Successfully deleted device ID {device_id}")
        return True
    except sqlite3.Error as e:
        print(f"Error deleting device: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Telemetry data operations
def store_telemetry_data(device_id, topic_id, payload):
    """
    Store telemetry data from a device with improved error handling and validation.
    
    Args:
        device_id (int): ID of the device sending data
        topic_id (int): ID of the topic the data belongs to
        payload (dict or str): The data payload to store
        
    Returns:
        bool: True if data was stored successfully, False otherwise
    """
    if not device_id or not topic_id:
        print("Error: device_id and topic_id must be provided for telemetry data")
        return False
        
    # Store as JSON string if payload is dictionary
    if isinstance(payload, dict):
        try:
            payload = json.dumps(payload)
        except (TypeError, ValueError) as e:
            print(f"Error converting payload to JSON: {e}")
            return False
    
    # Validate payload is a string at this point
    if not isinstance(payload, str):
        print(f"Error: payload must be a string or dictionary, got {type(payload)}")
        return False
    
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Verify device exists
        device = conn.execute('SELECT * FROM devices WHERE id = ?', (device_id,)).fetchone()
        if not device:
            print(f"Error: device with ID {device_id} does not exist")
            conn.rollback()
            return False
            
        # Verify topic exists
        topic = conn.execute('SELECT * FROM topics WHERE id = ?', (topic_id,)).fetchone()
        if not topic:
            print(f"Error: topic with ID {topic_id} does not exist")
            conn.rollback()
            return False
        
        # Store the telemetry data
        conn.execute(
            'INSERT INTO telemetry_data (device_id, topic_id, payload) VALUES (?, ?, ?)',
            (device_id, topic_id, payload)
        )
        
        # Update device's last_seen timestamp
        conn.execute(
            'UPDATE devices SET last_seen = ? WHERE id = ?',
            (datetime.now(VN_TZ).isoformat(), device_id)
        )
        
        # Commit the transaction
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error when storing telemetry data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_telemetry_data(device_id=None, topic_id=None, limit=100):
    """Get telemetry data, optionally filtered by device_id and/or topic_id."""
    conn = get_db_connection()
    
    # Modified query to join with devices and topics tables
    query = '''
        SELECT 
            td.id, td.device_id, td.topic_id, td.payload, td.timestamp,
            d.name as device_name, t.name as topic_name
        FROM telemetry_data td
        LEFT JOIN devices d ON td.device_id = d.id
        LEFT JOIN topics t ON td.topic_id = t.id
    '''
    
    params = []
    
    if device_id and topic_id:
        query += ' WHERE td.device_id = ? AND td.topic_id = ?'
        params.extend([device_id, topic_id])
    elif device_id:
        query += ' WHERE td.device_id = ?'
        params.append(device_id)
    elif topic_id:
        query += ' WHERE td.topic_id = ?'
        params.append(topic_id)
    
    query += ' ORDER BY td.timestamp DESC LIMIT ?'
    params.append(limit)
    
    data = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(item) for item in data]

def get_telemetry_data_count():
    """Get the total count of all telemetry data records in the database."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM telemetry_data').fetchone()[0]
    conn.close()
    return count

def cleanup_orphaned_data():
    """
    Clean up orphaned telemetry data that might remain after devices or topics are deleted.
    
    This function removes any telemetry data records that reference non-existent devices or topics.
    
    Returns:
        dict: A dictionary containing the number of records deleted and success status
    """
    conn = get_db_connection()
    try:
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Delete telemetry data with non-existent device_id
        result1 = conn.execute('''
            DELETE FROM telemetry_data 
            WHERE device_id NOT IN (SELECT id FROM devices)
        ''')
        deleted_device_data = result1.rowcount
        
        # Delete telemetry data with non-existent topic_id
        result2 = conn.execute('''
            DELETE FROM telemetry_data 
            WHERE topic_id NOT IN (SELECT id FROM topics)
        ''')
        deleted_topic_data = result2.rowcount
        
        # Commit the transaction
        conn.commit()
        
        total_deleted = deleted_device_data + deleted_topic_data
        print(f"Successfully cleaned up {total_deleted} orphaned telemetry data records")
        
        return {
            'success': True,
            'deleted_count': total_deleted,
            'device_data_deleted': deleted_device_data,
            'topic_data_deleted': deleted_topic_data
        }
    except sqlite3.Error as e:
        print(f"Error cleaning up orphaned data: {e}")
        conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()

def get_device_telemetry_data(topic_id=None, limit_per_device=5):
    """
    Get telemetry data organized by device with improved limit handling.
    
    Args:
        topic_id (int, optional): Filter by topic ID
        limit_per_device (int, optional): Maximum number of telemetry records per device
        
    Returns:
        dict: A dictionary with device_id as keys and device info + telemetry as values
    """
    conn = get_db_connection()
    
    # Get all devices
    devices = get_all_devices()
    
    # Get all topics for reference
    all_topics = get_all_topics()
    
    # Get all clients for reference
    all_clients = get_all_clients()
    
    # Dictionary to store results
    device_data = {}
    
    # Get data for each device
    for device in devices:
        if device:
            # Build the query for telemetry data
            query = '''
                SELECT t.*, tp.name as topic_name 
                FROM telemetry_data t
                LEFT JOIN topics tp ON t.topic_id = tp.id
                WHERE t.device_id = ?
            '''
            params = [device['id']]
            
            # Add topic filter if specified
            if topic_id is not None:
                query += ' AND t.topic_id = ?'
                params.append(topic_id)
            
            # Add ordering and limit
            query += ' ORDER BY t.timestamp DESC LIMIT ?'
            params.append(limit_per_device)
            
            # Execute query
            telemetry = conn.execute(query, params).fetchall()
            telemetry = [dict(row) for row in telemetry]
            
            if telemetry:
                # Find client info for this device
                client = next((c for c in all_clients if c['id'] == device['client_id']), None)
                
                # Find all topics this device has sent data to
                device_topics = []
                topic_ids = set()
                for item in telemetry:
                    if item['topic_id'] not in topic_ids:
                        topic_ids.add(item['topic_id'])
                        topic = next((t for t in all_topics if t['id'] == item['topic_id']), None)
                        if topic:
                            device_topics.append(topic)
                
                device_data[device['id']] = {
                    'device': device,
                    'client': client,
                    'topics': device_topics,
                    'telemetry': telemetry
                }
    
    conn.close()
    return device_data

def get_topic_by_id(topic_id):
    """Lấy thông tin của một topic cụ thể theo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM topics WHERE id = ?', (topic_id,))
    topic = cursor.fetchone()
    
    if topic:
        topic_dict = dict(zip([column[0] for column in cursor.description], topic))
        conn.close()
        return topic_dict
    
    conn.close()
    return None

def get_all_telemetry_by_topic(topic_id):
    """Lấy toàn bộ dữ liệu telemetry cho một topic không giới hạn số lượng"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, d.name as device_name, tp.name as topic_name 
        FROM telemetry t
        JOIN devices d ON t.device_id = d.id
        JOIN topics tp ON t.topic_id = tp.id
        WHERE t.topic_id = ?
        ORDER BY t.timestamp DESC
    ''', (topic_id,))
    
    data = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return data

def get_device_by_id(device_id):
    """Lấy thông tin của một thiết bị cụ thể theo ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
    device = cursor.fetchone()
    
    if device:
        device_dict = dict(zip([column[0] for column in cursor.description], device))
        conn.close()
        return device_dict
    
    conn.close()
    return None

def get_device_telemetry_data_full(device_id):
    """Lấy toàn bộ dữ liệu telemetry cho một thiết bị"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, tp.name as topic_name 
        FROM telemetry t
        JOIN topics tp ON t.topic_id = tp.id
        WHERE t.device_id = ?
        ORDER BY t.timestamp DESC
    ''', (device_id,))
    
    data = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return data

def get_device_topic_telemetry_data(device_id, topic_id):
    """Lấy toàn bộ dữ liệu telemetry cho một thiết bị và một topic cụ thể"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.*, tp.name as topic_name 
        FROM telemetry t
        JOIN topics tp ON t.topic_id = tp.id
        WHERE t.device_id = ? AND t.topic_id = ?
        ORDER BY t.timestamp DESC
    ''', (device_id, topic_id))
    
    data = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return data
