from fastapi import APIRouter
from controllers.donor_controller import router as donor_router
from controllers.emergency_controller import router as emergency_router
from controllers.hemocentro_controller import router as hemocentro_router
from controllers.admin_controller import router as admin_router
from services.donor_service import DonorService

api_router = APIRouter(prefix="/api")

# Inclusão dos sub-controladores
api_router.include_router(donor_router)
api_router.include_router(emergency_router)
api_router.include_router(hemocentro_router)
api_router.include_router(admin_router)

@api_router.get("/stats", tags=["Estatísticas Gerais"])
def get_global_stats():
    """Retorna métricas consolidadas de doadores, vidas salvas e distribuição por UF"""
    return DonorService.get_stats()
