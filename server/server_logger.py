from datetime import datetime
from threading import Lock

_log_lock = Lock()

def log(message: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    with _log_lock:
        print(f"[{now}] {message}", flush=True)
