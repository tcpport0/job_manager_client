import json
import pytest
from job_manager_client.worker import process_job
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn


def test_simple_job():
    """Test a very simple job without any complexity"""
    
    def simple_task(params):
        return {"message": "Hello"}
    
    # Create and process job
    job_id = 'test_simple'
    job = queue.enqueue(simple_task, args=({},), job_id=job_id)
    process_job(simple_task, job)
    
    # Verify result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result found"
    result_data = json.loads(result)
    assert result_data == {"message": "Hello"}, "Unexpected result"


def test_job_with_params():
    """Test a job that receives parameters"""
    
    def param_task(params):
        return {"received": params}
    
    # Create and process job
    job_id = 'test_params'
    test_params = {"key": "value"}
    job = queue.enqueue(param_task, args=(test_params,), job_id=job_id)
    process_job(param_task, job)
    
    # Verify result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result found"
    result_data = json.loads(result)
    assert result_data == {"received": test_params}, "Parameters not correctly passed"


def test_job_error():
    """Test error handling in a job"""
    
    def error_task(params):
        raise ValueError("Test error")
    
    # Create and process job
    job_id = 'test_error'
    job = queue.enqueue(error_task, args=({},), job_id=job_id)
    
    # Job should raise error but still record it
    with pytest.raises(ValueError, match="Test error"):
        process_job(error_task, job)
    
    # Verify error was recorded
    error = keydb_conn.hget(f'job:{job_id}:status', 'error')
    assert error is not None, "No error found"
    error_data = json.loads(error)
    assert "Test error" in error_data['error'], "Unexpected error message"
    assert 'traceback' in error_data, "No traceback in error"
