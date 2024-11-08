import pytest
import json
from job_manager_client.utils.connections import redis_conn, keydb_conn

def test_redis_connection():
    """Test basic Redis connectivity and operations"""
    # Test connection
    assert redis_conn.ping(), "Redis connection failed"
    
    # Test basic operations
    test_key = "test:redis:key"
    test_value = {"test": "data"}
    
    # Set value
    redis_conn.set(test_key, json.dumps(test_value))
    
    # Get value
    stored_value = redis_conn.get(test_key)
    assert stored_value is not None, "Failed to retrieve value from Redis"
    assert json.loads(stored_value) == test_value, "Retrieved value doesn't match"
    
    # Test pub/sub
    pubsub = redis_conn.pubsub()
    channel = "test:channel"
    message = {"status": "test"}
    
    # Subscribe
    pubsub.subscribe(channel)
    
    # Publish
    redis_conn.publish(channel, json.dumps(message))
    
    # Get message (skip subscription confirmation message)
    pubsub.get_message()  # subscription message
    received = pubsub.get_message(timeout=1)
    
    assert received is not None, "No message received"
    assert json.loads(received['data']) == message, "Message content doesn't match"
    
    # Cleanup
    pubsub.unsubscribe()
    redis_conn.delete(test_key)

def test_keydb_connection():
    """Test basic KeyDB connectivity and operations"""
    # Test connection
    assert keydb_conn.ping(), "KeyDB connection failed"
    
    # Test hash operations
    test_key = "test:keydb:hash"
    test_data = {
        "field1": json.dumps({"data": "value1"}),
        "field2": json.dumps({"data": "value2"})
    }
    
    # Set hash fields
    keydb_conn.hset(test_key, mapping=test_data)
    
    # Get individual field
    value1 = keydb_conn.hget(test_key, "field1")
    assert value1 is not None, "Failed to retrieve hash field from KeyDB"
    assert json.loads(value1) == {"data": "value1"}, "Retrieved value doesn't match"
    
    # Get all fields
    all_values = keydb_conn.hgetall(test_key)
    assert len(all_values) == 2, "Wrong number of hash fields"
    assert all_values["field1"] == test_data["field1"], "Field 1 doesn't match"
    assert all_values["field2"] == test_data["field2"], "Field 2 doesn't match"
    
    # Cleanup
    keydb_conn.delete(test_key)

def test_connection_error_handling():
    """Test error handling for invalid operations"""
    # Test Redis error handling
    test_key = "test:string:key"
    redis_conn.set(test_key, "not_a_number")
    
    with pytest.raises(Exception):
        redis_conn.incr(test_key)  # Try to increment non-numeric value
    
    # Test KeyDB error handling
    keydb_conn.set(test_key, "not_a_number")
    with pytest.raises(Exception):
        keydb_conn.incr(test_key)  # Try to increment non-numeric value
    
    # Cleanup
    redis_conn.delete(test_key)
    keydb_conn.delete(test_key)

def test_connection_parameters():
    """Test that connection parameters are correct"""
    # Redis info
    redis_info = redis_conn.info()
    assert redis_info['redis_version'] is not None, "Could not get Redis version"
    
    # KeyDB info
    keydb_info = keydb_conn.info()
    assert keydb_info['redis_version'] is not None, "Could not get KeyDB version"
    
    # Test Redis responses (should be bytes since decode_responses=False)
    test_key = "test:string:key"
    test_value = "test_value"
    
    redis_conn.set(test_key, test_value)
    retrieved = redis_conn.get(test_key)
    assert isinstance(retrieved, bytes), "Redis should return bytes"
    assert retrieved.decode() == test_value, "Retrieved value doesn't match"
    
    # Test KeyDB responses (should be strings since decode_responses=True)
    keydb_conn.set(test_key, test_value)
    retrieved = keydb_conn.get(test_key)
    assert isinstance(retrieved, str), "KeyDB decode_responses not working"
    assert retrieved == test_value, "Retrieved value doesn't match"
    
    # Cleanup
    redis_conn.delete(test_key)
    keydb_conn.delete(test_key)
