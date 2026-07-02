"""Configurações centralizadas do Flight Tracker."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Rota monitorada
# ---------------------------------------------------------------------------
ORIGIN = "PDT"  # Presidente Prudente
DESTINATIONS = ["GIG", "SDU"]  # Rio de Janeiro (Galeão / Santos Dumont)

DEPARTURE_DATES = ["2026-09-03", "2026-09-04", "2026-09-05"]
RETURN_DATES = ["2026-09-07", "2026-09-08", "2026-09-09"]

EVENT_NAME = "Rock in Rio 2026"
EVENT_DATE = "2026-09-05"

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
SCHEDULER_ENABLED = True
SCHEDULER_INTERVAL_MINUTES = 30
DAILY_REPORT_TIME = "12:00"  # HH:MM, 24h

# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------
PRICE_DROP_THRESHOLD = 10  # % de queda que dispara alerta

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "flights.db"

# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "flight_tracker.log"

# ---------------------------------------------------------------------------
# Dashboard (Flask)
# ---------------------------------------------------------------------------
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ---------------------------------------------------------------------------
# Email (SMTP)
# ---------------------------------------------------------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "franchi.contato@gmail.com")

# ---------------------------------------------------------------------------
# Machine Learning
# ---------------------------------------------------------------------------
ML_MIN_DATA_POINTS = 50
ML_MIN_CONFIDENCE = 75  # %
