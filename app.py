from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import CORS_ORIGINS
from routes.api import api_router

app = FastAPI(
    title="🩸 HemoAlerta API",
    description="API REST para gestão de doadores de sangue voluntários, compatibilidade sanguínea e alertas de emergência (LGPD compliant).",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para permitir acesso seguro do frontend React / Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    from config.settings import HOST, PORT
    print(f"🚀 HemoAlerta API iniciando em http://localhost:{PORT}")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
