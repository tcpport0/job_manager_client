# Job Manager Client

A Python package that provides a client for managing long-running jobs with automatic keepalive messages.

## Features

- Automatic keepalive messages every 0.5 seconds for long-running tasks
- Redis pub/sub for real-time status updates
- KeyDB storage for large results
- Full error tracking with tracebacks
- Proper cleanup of resources
- Secure authentication for Redis and KeyDB

## Testing Setup

The testing environment uses Docker Compose to create a complete testing infrastructure:

- Redis container for job queue and pub/sub messaging (password protected)
- KeyDB container for result storage (password protected)
- Test container running pytest

### Prerequisites

- Docker
- Docker Compose

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password  # Required for authentication

# KeyDB Configuration
KEYDB_HOST=localhost
KEYDB_PORT=6380
KEYDB_PASSWORD=your_keydb_password  # Required for authentication

# Queue Configuration
JOB_QUEUE=test_queue
```

For testing with docker-compose, if no passwords are provided in the .env file, default development passwords will be used.

### Running Tests

1. Start the testing environment:
```bash
docker-compose up --build
```

This will:
- Build the test container
- Start Redis and KeyDB services with password authentication
- Run the test suite

2. To run tests individually or with specific options:
```bash
docker-compose run test pytest tests/test_worker.py -v -k "test_long_running_task"
```

### Test Cases

The test suite includes:

1. `test_long_running_task`: Verifies keepalive messages during long operations
2. `test_error_handling`: Ensures errors are properly captured and reported
3. `test_large_result_handling`: Tests storage of large results in KeyDB
4. `test_cleanup`: Verifies proper cleanup of resources

## Development

To set up a development environment:

1. Clone the repository

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with the required configuration (see Environment Variables section above)

## Security Notes

- Both Redis and KeyDB instances are password protected
- Default development passwords are only used in the Docker testing environment
- In production, always use strong, unique passwords
- Never commit passwords or .env files to version control

## Usage Example

```python
from job_manager_client.worker import start_worker

def my_long_running_task(params):
    # This function can run for any duration
    # Keepalives will automatically be sent every 0.5 seconds
    result = do_some_work(params)
    return result

# Start the worker
start_worker(my_long_running_task)
```

The worker will automatically:
- Send keepalive messages every 0.5 seconds
- Handle errors and include tracebacks
- Store results in KeyDB if they're too large for Redis pub/sub
- Use secure authentication for all Redis and KeyDB operations
