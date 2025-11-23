from datetime import datetime

def log(message):
    """Pretty console logger with timestamps."""
    time = datetime.now().strftime("%H:%M:%S")
    print(f"[{time}] {message}")
