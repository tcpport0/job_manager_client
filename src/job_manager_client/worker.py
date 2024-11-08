import os
import time
import json
import threading
import traceback
from redis import Redis
from rq import Queue, Worker, SimpleWorker
from job_manager_client.utils.connections import redis_conn, queue, keydb_conn
from job_manager_client.job_status import JobStatus

def keepalive_loop(job_status, stop_event, interval=0.5):
    """
    Background thread function to send keepalive messages
    
    :param job_status: JobStatus instance to send keepalives
    :param stop_event: Threading event to signal when to stop
    :param interval: Time between keepalive messages in seconds
    """
    while not stop_event.is_set():
        try:
            job_status.send_keepalive()
            time.sleep(interval)
        except Exception as e:
            print(f"Error in keepalive loop: {e}")
            traceback.print_exc()

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
    
    # Create and start keepalive thread
    stop_keepalive = threading.Event()
    keepalive_thread = threading.Thread(
        target=keepalive_loop,
        args=(job_status, stop_keepalive),
        daemon=True  # Ensure thread stops if main thread crashes
    )
    keepalive_thread.start()
    
    try:
        # Check for params in KeyDB if not provided
        if not params:
            stored_params = keydb_conn.get(f"job:{job_id}:params")
            if stored_params:
                params = json.loads(stored_params)
        
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
        print(f"Exception during job processing: {e}")
        traceback.print_exc()
        raise
    
    finally:
        # Stop the keepalive thread
        stop_keepalive.set()
        keepalive_thread.join(timeout=1.0)

def start_worker(task_function):
    """
    Starts a worker that processes jobs from the queue.
    
    :param task_function: The actual function to execute for each job.
    """
    class CustomWorker(SimpleWorker):
        def execute_job(self, job, queue):
            return process_job(task_function, job)

    worker = CustomWorker([queue], connection=redis_conn)
    worker.work(burst=True)