import logging
import os

logger = logging.getLogger(__name__)

# Get the absolute path to the backend/app directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

JOB_STATUS: dict[str, dict] = {}  # {job_id: {stage:…, current:…, total:…}}


def set_status(job_id: str, **kwargs):
    old_status = JOB_STATUS.get(job_id, {})
    new_status = {**old_status, **kwargs}
    JOB_STATUS[job_id] = new_status

    stage = new_status.get("stage", "unknown")
    msg = f"[{job_id[:8]}] -> stage: {stage}"
    if "current" in new_status and "total" in new_status:
        msg += f" ({new_status['current']}/{new_status['total']})"
    if "error" in new_status:
        msg += f" [WARNING] error: {new_status['error']}"
    logger.info(msg)


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
