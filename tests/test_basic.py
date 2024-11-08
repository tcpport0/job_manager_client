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


def test_basic_job_processing():
    """Test basic job processing without any complexity"""
    
    def basic_task(params):
        return {"status": "completed"}
    
    # Create and enqueue a job
    job_id = 'test_basic_job'
    job = queue.enqueue(basic_task, job_id=job_id, args=({},))
    
    # Process the job
    start_worker(basic_task)
    
    # Wait for job completion
    def check_completion():
        status = keydb_conn.hget(f'job:{job_id}:status', 'status')
        return status == 'COMPLETE'
    
    assert wait_for_condition(check_completion), "Job did not complete in time"
    
    # Verify the result
    result = keydb_conn.hget(f'job:{job_id}:status', 'result')
    assert result is not None, "No result stored"
    result_data = json.loads(result)
    assert result_data == {"status": "completed"}, "Unexpected result"


def test_job_with_parameters():
    """Test job processing with parameters"""
    
    def param_task(params):
        return {"received": params}
    
    # Create and enqueue a job with parameters
    job_id = 'test_param_job'
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


def test_simple_error_handling():
    """Test basic error handling"""
    
    def error_task(params):
        raise ValueError("Test error")
    
    # Create and enqueue a job
    job_id = 'test_error_job'
    job = queue.enqueue(error_task, job_id=job_id, args=({},))
    
    # Process the job
    start_worker(error_task)
    
    # Wait for job completion (will be error)
    def check_error():
        error = keydb_conn.hget(f'job:{job_id}:status', 'error')
        return error is not None
    
    assert wait_for_condition(check_error), "Error was not recorded in time"
    
    # Verify the error
    error = keydb_conn.hget(f'job:{job_id}:status', 'error')
    assert error is not None, "No error stored"
    error_data = json.loads(error)
    assert "Test error" in error_data['error'], "Error message not correctly stored"
    assert 'traceback' in error_data, "Traceback not included in error"
