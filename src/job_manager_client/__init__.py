from .worker import start_worker
from .job_status import JobStatus

__version__ = "0.1.0"

__all__ = [
    "start_worker",
    "JobStatus"  # Useful if users want to create custom status updates
]
