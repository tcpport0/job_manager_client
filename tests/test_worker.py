import json
import pytest
from job_manager_client.worker import process_job
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn


def test_simple_task():
    """Test a simple, quick task without any long-running operations"""
    
    def simple_task(params):
        return {"message": "Hello, World!"}
    
    # Create and process job
    job_id = 'test_simple_job'
    job = queue.enqueue(simple_task, args=({},), job_id=job_id)
    process_job(simple_task, job)
    
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
    
    # Job should raise error but still record it
    with pytest.raises(ValueError, match="Test error"):
        process_job(failing_task, job)
    
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
    process_job(large_result_task, job)
    
    # Verify large result was stored
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "Result was not stored"
    result_data = json.loads(result)
    assert len(result_data['data']) == 2000000, "Large result not stored correctly"


def test_job_status_updates():
    """Test that job status is properly updated"""
    
    def status_task(params):
        return {"status": "done"}
    
    # Create and process job
    job_id = 'test_status'
    job = queue.enqueue(status_task, args=({},), job_id=job_id)
    process_job(status_task, job)
    
    # Verify final status
    status = keydb_conn.hget(f'job:{job_id}:status', 'status')
    assert status == 'COMPLETE', "Job status not updated correctly"
    
    # Verify result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    result_data = json.loads(result)
    assert result_data == {"status": "done"}, "Unexpected result"
