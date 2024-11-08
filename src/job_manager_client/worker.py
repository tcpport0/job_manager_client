import json
import traceback
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn
from job_manager_client.job_status import JobStatus


def process_job(task_function, job):
    """
    Process a single job and update its status
    
    :param task_function: The function to execute
    :param job: The RQ job object
    """
    job_id = job.id
    params = job.args[0] if job.args else {}
            
    job_status = JobStatus(job_id)
    job_status.start()
    
    # Check for params in KeyDB if not provided
    if not params:
        stored_params = keydb_conn.get(f"job:{job_id}:params")
        if stored_params:
            params = json.loads(stored_params)
    
    try:
        # Execute the task
        result = task_function(params)
        job_status.complete(result=result)
        return result
            
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        job_status.complete(error=error_info)
        raise  # Re-raise to ensure error is properly propagated
