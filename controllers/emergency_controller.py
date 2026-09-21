from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.emergency_service import EmergencyService

router = APIRouter(prefix="/emergencias", tags=["Emergências e Alertas SOS"])

class CompatibilityCheckDTO(BaseModel):
    tipoSanguineo: str = Field(..., description="Tipo sanguíneo solicitado (ex: A+, O-)")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    cidade: Optional[str] = Field(None, description="Cidade do hospital/paciente")

class EmergencyCreateDTO(BaseModel):
    tipo: str = Field(..., description="Tipo sanguíneo necessário")
    quantidade: int = Field(1, ge=1, description="Quantidade de bolsas solicitadas")
    paciente: str = Field(..., description="Nome do paciente ou instituição")
    hospital: Optional[str] = Field("Hemocentro Regional", description="Hospital ou Hemocentro onde deve ser realizada a doação")
    cidade: str = Field(..., description="Cidade da emergência")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    urgencia: str = Field("ALTA", description="Nível de urgência: MÉDIA, ALTA, CRÍTICA")
    contato: str = Field(..., description="Telefone de contato do hemocentro/hospital")
    mensagem: Optional[str] = Field(None, description="Informações adicionais para o doador")

@router.get("/disponibilidade-regiao")
def get_regional_availability(estado: str, cidade: Optional[str] = None):
    """Retorna os tipos sanguíneos que possuem doadores reais cadastrados naquela região"""
    return EmergencyService.get_regional_availability(estado=estado, cidade=cidade)

@router.post("/calcular-compatibilidade")
def calculate_compatibility(payload: CompatibilityCheckDTO):
    """Calcula instantaneamente quantos doadores compatíveis e aptos existem na região"""
    return EmergencyService.calculate_compatibility(
        blood_type=payload.tipoSanguineo,
        estado=payload.estado,
        cidade=payload.cidade
    )

@router.post("/solicitar", status_code=status.HTTP_201_CREATED)
def create_emergency(payload: EmergencyCreateDTO):
    """Cria uma solicitação de emergência como PENDENTE de aprovação pelo Admin/Hemocentro"""
    try:
        emergency = EmergencyService.create_emergency(payload.model_dump())
        return {
            "sucesso": True,
            "mensagem": f"Solicitação SOS #{emergency['id']} registrada com sucesso! Encaminhada para a moderação e validação da equipe do Hemocentro.",
            "emergencia": emergency
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
