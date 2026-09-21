from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from services.hemocentro_service import HemocentroService

router = APIRouter(prefix="/hemocentros", tags=["Hemocentros"])

@router.get("")
def list_hemocentros(
    estado: Optional[str] = Query(None, description="Sigla da UF (ex: SP, RJ)"),
    tipo: Optional[str] = Query(None, description="Tipo de estabelecimento: hemocentro, hospital, clinica"),
    cidade: Optional[str] = Query(None, description="Nome da cidade")
):
    """Busca postos de coleta e hemocentros com filtros geográficos"""
    return HemocentroService.list_hemocentros(estado=estado, tipo=tipo, cidade=cidade)
