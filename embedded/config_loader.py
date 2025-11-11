import os
import sys
import yaml

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def load_config():
    config_path = os.path.join(PROJECT_ROOT, "config.yml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ config.yml 로드 실패: {e}")
        return {}

config = load_config()
