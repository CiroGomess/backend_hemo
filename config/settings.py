import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_PROJECT_DIR = BASE_DIR.parent

DB_PATH = BASE_DIR / "hemoalerta.db"
SEED_FILE = ROOT_PROJECT_DIR / "doadores.json"

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*",  # Em desenvolvimento, permite todas as origens locais
]

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
