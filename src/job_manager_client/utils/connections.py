import os
from redis import Redis
from rq import Queue

JOB_QUEUE = os.getenv('JOB_QUEUE', 'default')

# Redis connection settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# KeyDB connection settings
KEYDB_HOST = os.getenv('KEYDB_HOST', 'localhost')
KEYDB_PORT = int(os.getenv('KEYDB_PORT', '6379'))
KEYDB_DB = int(os.getenv('KEYDB_DB', '0'))
KEYDB_PASSWORD = os.getenv('KEYDB_PASSWORD')

# Common Redis connection settings
COMMON_REDIS_KWARGS = {
    'decode_responses': True,  # Always decode responses to strings
    'socket_timeout': 5,       # 5 second timeout
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30
}

# setup queue redis (without decode_responses for RQ compatibility)
redis_conn = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
    decode_responses=False  # RQ needs this to be False
)

# keydb store used for storing job results
keydb_conn = Redis(
    host=KEYDB_HOST,
    port=KEYDB_PORT,
    db=KEYDB_DB,
    password=KEYDB_PASSWORD,
    **COMMON_REDIS_KWARGS
)

# Queue used to receive jobs
queue = Queue(JOB_QUEUE, connection=redis_conn)

# Test connections on import
try:
    redis_conn.ping()
    print("Successfully connected to Redis")
except Exception as e:
    print(f"Warning: Could not connect to Redis: {e}")

try:
    keydb_conn.ping()
    print("Successfully connected to KeyDB")
except Exception as e:
    print(f"Warning: Could not connect to KeyDB: {e}")
