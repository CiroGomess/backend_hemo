from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.donor_service import DonorService

router = APIRouter(prefix="/doadores", tags=["Doadores"])

class DonorCreateDTO(BaseModel):
    nomeCompleto: str = Field(..., min_length=3, description="Nome completo do voluntário")
    tipoSanguineo: str = Field(..., description="Tipo sanguíneo: A+, A-, B+, B-, AB+, AB-, O+, O-, NS")
    dataNascimento: Optional[str] = Field(None, description="Data de nascimento YYYY-MM-DD")
    cidade: str = Field(..., min_length=2, description="Cidade de residência")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado (ex: SP, RJ)")
    whatsapp: str = Field(..., min_length=10, description="Número de WhatsApp com DDD")
    email: Optional[str] = Field(None, description="E-mail de contato")
    ultimaDoacao: Optional[str] = Field(None, description="Data da última doação YYYY-MM-DD")
    optInAlertas: bool = Field(True, description="Aceita receber alertas de urgência")
    consentimentoLGPD: bool = Field(True, description="Consentimento explícito LGPD")

class DonorUpdateDTO(BaseModel):
    nomeCompleto: Optional[str] = None
    tipoSanguineo: Optional[str] = None
    dataNascimento: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    ultimaDoacao: Optional[str] = None
    optInAlertas: Optional[bool] = None

class DonorAuthDTO(BaseModel):
    email: str
    whatsapp: str

@router.get("")
def list_donors(
    search: Optional[str] = Query(None, description="Busca por nome ou cidade"),
    tipo: Optional[str] = Query(None, description="Filtro por tipo sanguíneo"),
    estado: Optional[str] = Query(None, description="Filtro por UF"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100)
):
    """Lista todos os doadores com paginação e mascaramento de dados (LGPD)"""
    return DonorService.list_donors(
        search=search,
        blood_type=tipo,
        state=estado,
        page=page,
        page_size=pageSize,
        full_access=False
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_donor(donor: DonorCreateDTO):
    """Cadastra um novo doador com conformidade LGPD"""
    try:
        new_donor = DonorService.create_donor(donor.model_dump())
        return {
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso! Obrigado por ajudar a salvar vidas.",
            "doador": DonorService.apply_lgpd_mask(new_donor, full_access=False)
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/perfil")
def access_profile(credentials: DonorAuthDTO):
    """Acesso seguro do titular para visualizar seus próprios dados completos (LGPD)"""
    donor = DonorService.find_for_auth(credentials.email, credentials.whatsapp)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doador não localizado com este e-mail e telefone informados."
        )
    return {
        "sucesso": True,
        "doador": donor # Retorna dados completos para o titular
    }

@router.put("/{donor_id}")
def update_donor(donor_id: str, updates: DonorUpdateDTO):
    """Atualização cadastral do doador"""
    cleaned_updates = {k: v for k, v in updates.model_dump().items() if v is not None}
    updated = DonorService.update_donor(donor_id, cleaned_updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doador não encontrado.")
    return {
        "sucesso": True,
        "mensagem": "Dados atualizados com sucesso!",
        "doador": updated
    }

@router.delete("/{donor_id}")
def delete_donor(donor_id: str):
    """Direito ao esquecimento / revogação do cadastro (LGPD Art. 18)"""
    deleted = DonorService.delete_donor(donor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doador não encontrado.")
    return {
        "sucesso": True,
        "mensagem": "Dados excluídos definitivamente do sistema conforme solicitado."
    }
