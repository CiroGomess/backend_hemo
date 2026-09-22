import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_PROJECT_DIR = BASE_DIR.parent

DB_PATH = BASE_DIR / "hemoalerta.db"
SEED_FILE = ROOT_PROJECT_DIR / "doadores.json"

CORS_ORIGINS = [
    "https://hemoalert.squareweb.app",
    "http://hemoalert.squareweb.app",
    "https://backendhemoalert.squareweb.app",
    "http://backendhemoalert.squareweb.app",
    "https://whatsservicehemoalert.squareweb.app",
    "http://whatsservicehemoalert.squareweb.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# URL do serviço de WhatsApp (Venom)
VENOM_SERVICE_URL = os.getenv("VENOM_SERVICE_URL", "https://whatsservicehemoalert.squareweb.app")
