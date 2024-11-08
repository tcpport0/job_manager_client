from .utils.connections import keydb_conn, redis_conn
import json
import time


class JobStatus:
    """
    Handles job status updates and result storage using Redis pub/sub and KeyDB
    """

    def __init__(self, job_id: str):
        self.keydb_conn = keydb_conn
        self.redis_conn = redis_conn
        self.job_id = job_id

    @property
    def _status_channel(self):
        return f'job:{self.job_id}'
    
    @property
    def _status_key(self):
        return f'job:{self.job_id}:status'

    def _send_status_message(self, message: dict):
        """Send a status message to the client."""
        try:
            # Ensure message is JSON serializable and includes timestamp
            message['timestamp'] = time.time()
            message_str = json.dumps(message)
            self.redis_conn.publish(self._status_channel, message_str)
        except Exception as e:
            print(f"Error sending status message: {e}")

    def _update_job(self, key: str, value):
        """Update the status of the job in keydb."""
        try:
            # Convert value to string if it's a dict/list
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            # Store in KeyDB
            self.keydb_conn.hset(self._status_key, key, value)
        except Exception as e:
            print(f"Error updating job status: {e}")

    def start(self):
        """Send a start message to the client and update status in keydb."""
        status_message = {
            'status': 'IN_PROGRESS',
            'timestamp': time.time()
        }
        self._send_status_message(status_message)
        self._update_job('status', 'IN_PROGRESS')

    def send_keepalive(self):
        """Send a keepalive message to the client."""
        try:
            self._send_status_message({
                'status': 'IN_PROGRESS',
                'keepalive': True,
                'timestamp': time.time()
            })
        except Exception as e:
            print(f"Error sending keepalive: {e}")

    def complete(self, result=None, error=None):
        """
        Send complete message and set result or error
        
        :param result: The result data to store
        :param error: Error information if the job failed
        """
        try:
            success = error is None
            self._update_job('status', 'COMPLETE')
            
            if error:
                self._update_job('error', error)
                self._send_status_message({
                    'status': 'COMPLETE',
                    'success': False,
                    'error': error,
                    'timestamp': time.time()
                })
                return None

            if result is None:
                self._send_status_message({
                    'status': 'COMPLETE',
                    'success': True,
                    'timestamp': time.time()
                })
                return None

            # Store the result
            self._update_job('result', result)
            
            # Convert result to string for size check
            str_result = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
            result_size = len(str_result)
            
            # Send appropriate message based on result size
            message = {
                'status': 'COMPLETE',
                'success': True,
                'timestamp': time.time(),
                'result_size': result_size,
                'result_key': self._status_key
            }
            
            # Include result in message only if it's small enough
            if result_size < 1000000:
                message['result'] = result
                
            self._send_status_message(message)
            
        except Exception as e:
            error_info = f"Failed to handle result: {str(e)}"
            self._update_job('error', error_info)
            self._send_status_message({
                'status': 'COMPLETE',
                'success': False,
                'error': error_info,
                'timestamp': time.time()
            })
        
        return None
