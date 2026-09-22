import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "hemoalerta.db"
SEED_FILE = BASE_DIR / "data" / "doadores.json"

# ==========================================
# URLs de produção (Square Cloud) — fixas, sem .env
# ==========================================
FRONTEND_URL = "https://hemoalert.squareweb.app"
BACKEND_URL = "https://backendhemoalert.squareweb.app"
WHATS_SERVICE_URL = "https://whatsservicehemoalert.squareweb.app"

# URL do serviço de WhatsApp (Venom)
VENOM_SERVICE_URL = WHATS_SERVICE_URL

# Arte oficial enviada junto com os alertas
PROD_ART_URL = f"{FRONTEND_URL}/art.jpeg"

CORS_ORIGINS = [
    FRONTEND_URL,
    BACKEND_URL,
    WHATS_SERVICE_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

# Aceita qualquer subdomínio *.squareweb.app e localhost em qualquer porta
CORS_ORIGIN_REGEX = r"^https?://([a-z0-9-]+\.squareweb\.app|localhost|127\.0\.0\.1)(:\d+)?$"

# Porta: a Square Cloud exige 80; localmente usa 8000
PORT = int(os.getenv("PORT", 8000))
HOST = "0.0.0.0"
