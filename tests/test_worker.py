import time
import json
import pytest
import threading
from job_manager_client.worker import start_worker
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn


def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """Helper function to wait for a condition with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def test_simple_task():
    """Test a simple, quick task without any long-running operations"""
    
    def simple_task(params):
        return {"message": "Hello, World!"}
    
    # Create and process job
    job_id = 'test_simple_job'
    job = queue.enqueue(simple_task, args=({},), job_id=job_id)
    
    # Process the job
    start_worker(simple_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "Result was not stored"
    result_data = json.loads(result)
    assert result_data == {"message": "Hello, World!"}, "Unexpected result data"


def test_error_handling():
    """Test that errors are properly captured and reported"""
    
    def failing_task(params):
        raise ValueError("Test error")
    
    # Create and process job
    job_id = 'test_job_error'
    job = queue.enqueue(failing_task, args=({},), job_id=job_id)
    
    # Process the job
    start_worker(failing_task)
    
    # Wait for error to be recorded
    def check_error():
        error = keydb_conn.hget(f'job:{job_id}:status', 'error')
        return error is not None
    
    assert wait_for_condition(check_error), "Error was not recorded in time"
    
    # Verify error was recorded
    error = keydb_conn.hget(f'job:{job_id}:status', 'error')
    assert error is not None, "Error was not stored"
    error_data = json.loads(error)
    assert "Test error" in error_data['error'], "Unexpected error message"
    assert 'traceback' in error_data, "No traceback in error"


def test_large_result_handling():
    """Test that large results are properly stored in KeyDB"""
    
    def large_result_task(params):
        return {"data": "x" * 2000000}  # 2MB of data
    
    # Create and process job
    job_id = 'test_large_result'
    job = queue.enqueue(large_result_task, args=({},), job_id=job_id)
    
    # Process the job
    start_worker(large_result_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify large result was stored
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "Result was not stored"
    result_data = json.loads(result)
    assert len(result_data['data']) == 2000000, "Result data size incorrect"


def test_job_status_updates():
    """Test that job status is properly updated"""
    
    def status_task(params):
        return {"status": "done"}
    
    # Create and process job
    job_id = 'test_status'
    job = queue.enqueue(status_task, args=({},), job_id=job_id)
    
    # Process the job
    start_worker(status_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify final status
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "Result was not stored"
    result_data = json.loads(result)
    assert result_data == {"status": "done"}, "Unexpected result data"


def test_background_keepalive():
    """Test that keepalive messages are sent in parallel with task execution"""
    
    def slow_task(params):
        """Task that takes a few seconds to complete"""
        time.sleep(2)  # Simulate long-running work
        return {"status": "done"}
    
    # Create and process job
    job_id = 'test_background_keepalive'
    job = queue.enqueue(slow_task, args=({},), job_id=job_id)
    
    # Start collecting messages in background
    messages = []
    message_lock = threading.Lock()
    
    def collect_messages():
        pubsub = redis_conn.pubsub()
        pubsub.subscribe(f'job:{job_id}')
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                with message_lock:
                    messages.append((time.time(), data))
                
                # Stop collecting after job completes
                if data.get('status') == 'COMPLETE':
                    break
    
    # Start message collector thread
    collector_thread = threading.Thread(target=collect_messages)
    collector_thread.daemon = True
    collector_thread.start()
    
    # Process the job
    start_time = time.time()
    start_worker(slow_task)
    
    # Wait for collector to finish
    collector_thread.join(timeout=3.0)
    
    # Analyze messages
    with message_lock:
        keepalives = [m for t, m in messages if m.get('keepalive')]
        
    # Verify we got regular keepalive messages
    assert len(keepalives) > 2, "Not enough keepalive messages"
    
    # Check message timing
    timestamps = [t for t, m in messages if m.get('keepalive')]
    intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
    
    # Verify keepalive frequency (allowing some timing variance)
    assert all(0.4 <= i <= 0.6 for i in intervals), "Keepalive interval outside expected range"
