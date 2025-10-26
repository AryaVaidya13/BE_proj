from datetime import datetime

def log_message(message):
    """Pretty console logger with timestamps."""
    time = datetime.now().strftime("%H:%M:%S")
    print(f"[{time}] {message}")
