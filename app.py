import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import CORS_ORIGINS, CORS_ORIGIN_REGEX, HOST, PORT
from routes.api import api_router
    
# Logger do uvicorn: aparece no console tanto em dev quanto em produção
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executa em qualquer forma de inicialização (python app.py, uvicorn app:app, gunicorn)
    logger.info(f"✅ HemoAlerta API v{app.version} iniciada com sucesso em {HOST}:{PORT}")
    yield
    logger.info("🛑 HemoAlerta API encerrada")

app = FastAPI(
    lifespan=lifespan,
    title="🩸 HemoAlerta API",
    description="API REST para gestão de doadores de sangue voluntários, compatibilidade sanguínea e alertas de emergência (LGPD compliant).",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para permitir acesso do frontend Next.js e whats-service
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Registro do roteador central de APIs
app.include_router(api_router)

@app.get("/", tags=["Health Check"])
def root():
    return {
        "sistema": "HemoAlerta API",
        "versao": "3.0.0",
        "status": "online",
        "documentacao": "/docs"
    }

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 HemoAlerta API iniciando em http://{HOST}:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
