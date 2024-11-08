# Job Manager Client

A Python package that provides a client for managing long-running jobs with automatic keepalive messages.

## Features

- Automatic keepalive messages every 0.5 seconds for long-running tasks
- Background thread handling for keepalive messages (no modification of task code needed)
- Redis pub/sub for real-time status updates
- KeyDB storage for large results
- Full error tracking with tracebacks
- Proper cleanup of resources
- Secure authentication for Redis and KeyDB

## Installation

```bash
pip install job-manager-client
```

## Basic Usage

```python
from job_manager_client import start_worker

def my_long_running_task(params):
    # Your task code here
    # No need to handle keepalives - they're automatic!
    result = do_some_work(params)
    return result

# Start the worker
start_worker(my_long_running_task)
```

## Environment Variables

Create a `.env` file with:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# KeyDB Configuration
KEYDB_HOST=localhost
KEYDB_PORT=6380
KEYDB_PASSWORD=your_keydb_password

# Queue Configuration
JOB_QUEUE=test_queue
```

## How It Works

1. When a task starts, a background thread automatically sends keepalive messages every 0.5 seconds
2. Your task runs normally without any modifications needed
3. Results are stored in KeyDB if they're too large
4. All errors are captured with full tracebacks
5. Resources are automatically cleaned up when the task completes

## Advanced Usage

If you need custom status updates:

```python
from job_manager_client import JobStatus

def my_custom_task(params):
    job_status = JobStatus("my_job_id")
    
    # Custom status updates
    job_status.start()
    # ... do work ...
    job_status.complete(result={"status": "done"})
```

## Testing

Run the test suite:

```bash
docker-compose up --build
```

## Security

- Redis and KeyDB connections are password protected
- Default passwords are only used in testing
- Production environments should use strong, unique passwords
- Environment variables should never be committed to version control

## License

MIT License
