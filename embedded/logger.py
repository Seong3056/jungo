import os
import datetime
from config_loader import PROJECT_ROOT

def write_log(message):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

    # PROJECT_ROOT가 None이거나 잘못되면 현재 경로로 대체
    log_dir = PROJECT_ROOT if PROJECT_ROOT and os.path.isdir(PROJECT_ROOT) else os.getcwd()
    log_path = os.path.join(log_dir, "pi.log")

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{now} {message}\n")
    except Exception as e:
        print(f"[LOG ERROR] {e} → {log_path}")
