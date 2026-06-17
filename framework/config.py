"""Central configuration for the validation lab."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

THERMAL_HOST = "127.0.0.1"
THERMAL_PORT = 8001
FAN_PORT = 8002
POWER_PORT = 8003

THERMAL_URL = f"http://{THERMAL_HOST}:{THERMAL_PORT}"
FAN_URL = f"http://{THERMAL_HOST}:{FAN_PORT}"
POWER_URL = f"http://{THERMAL_HOST}:{POWER_PORT}"

LOG_DIR = PROJECT_ROOT / "logs"
COMPONENT_LOG_DIR = LOG_DIR / "component_logs"
TEST_LOG_DIR = LOG_DIR / "test_logs"
ARCHIVED_LOG_DIR = LOG_DIR / "archived"

REPORT_DIR = PROJECT_ROOT / "reports"
HTML_REPORT_DIR = REPORT_DIR / "html"
JSON_REPORT_DIR = REPORT_DIR / "json"
VALIDATION_REPORT_DIR = REPORT_DIR / "validation_reports"

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "validation.db"

SERVICE_STARTUP_TIMEOUT = 10.0
EVENT_PROPAGATION_DELAY = 0.15
