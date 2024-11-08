import time
import json
import pytest
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


def test_simple_job():
    """Test a very simple job without any complexity"""
    
    def simple_task(params):
        return {"message": "Hello"}
    
    # Create and enqueue a job
    job_id = 'test_simple'
    job = queue.enqueue(simple_task, job_id=job_id, args=({},))
    
    # Process the job
    start_worker(simple_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify the result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result stored"
    result_data = json.loads(result)
    assert result_data == {"message": "Hello"}, "Unexpected result"


def test_job_with_params():
    """Test a job that receives parameters"""
    
    def param_task(params):
        return {"received": params}
    
    # Create job with parameters
    job_id = 'test_params'
    test_params = {"key": "value"}
    job = queue.enqueue(param_task, job_id=job_id, args=(test_params,))
    
    # Process the job
    start_worker(param_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify the result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result stored"
    result_data = json.loads(result)
    assert result_data == {"received": test_params}, "Parameters not correctly passed"


def test_job_error():
    """Test error handling in a job"""
    
    def error_task(params):
        raise ValueError("Test error")
    
    # Create job
    job_id = 'test_error'
    job = queue.enqueue(error_task, job_id=job_id, args=({},))
    
    # Process the job
    start_worker(error_task)
    
    # Wait for error to be recorded
    def check_error():
        error = keydb_conn.hget(f'job:{job_id}:status', 'error')
        print(f"Current error: {error}")  # Debug output
        return error is not None
    
    assert wait_for_condition(check_error), "Error was not recorded in time"
    
    # Verify the error
    error = keydb_conn.hget(f'job:{job_id}:status', 'error')
    assert error is not None, "No error found"
    error_data = json.loads(error)
    assert "Test error" in error_data['error'], "Unexpected error message"
    assert 'traceback' in error_data, "No traceback in error"
