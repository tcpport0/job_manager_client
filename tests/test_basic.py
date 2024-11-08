import json
import pytest
from job_manager_client.worker import process_job
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn


def test_basic_job_processing():
    """Test basic job processing without any complexity"""
    
    def basic_task(params):
        return {"status": "completed"}
    
    # Create and process job
    job_id = 'test_basic_job'
    job = queue.enqueue(basic_task, args=({},), job_id=job_id)
    process_job(basic_task, job)
    
    # Verify the result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result stored"
    result_data = json.loads(result)
    assert result_data == {"status": "completed"}, "Unexpected result"


def test_job_with_parameters():
    """Test job processing with parameters"""
    
    def param_task(params):
        return {"received": params}
    
    # Create and process job
    job_id = 'test_param_job'
    test_params = {"key": "value"}
    job = queue.enqueue(param_task, args=(test_params,), job_id=job_id)
    process_job(param_task, job)
    
    # Verify the result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result stored"
    result_data = json.loads(result)
    assert result_data == {"received": test_params}, "Parameters not correctly passed"


def test_simple_error_handling():
    """Test basic error handling"""
    
    def error_task(params):
        raise ValueError("Test error")
    
    # Create and process job
    job_id = 'test_error_job'
    job = queue.enqueue(error_task, args=({},), job_id=job_id)
    
    # Job should raise error but still record it
    with pytest.raises(ValueError, match="Test error"):
        process_job(error_task, job)
    
    # Verify the error
    error = keydb_conn.hget(f'job:{job_id}:status', 'error')
    assert error is not None, "No error stored"
    error_data = json.loads(error)
    assert "Test error" in error_data['error'], "Error message not correctly stored"
    assert 'traceback' in error_data, "Traceback not included in error"
