from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.whatsapp_service import WhatsAppService
from services.donor_service import DonorService

router = APIRouter(prefix="/admin", tags=["Administração & WhatsApp Venom"])

# Credenciais padrão para fins de demonstração acadêmica
ADMIN_DEFAULT_USER = "admin"
ADMIN_DEFAULT_PASS = "admin123"

class LoginDTO(BaseModel):
    username: str = Field(..., description="Usuário do administrador")
    password: str = Field(..., description="Senha do administrador")

class SendTestDTO(BaseModel):
    to: str = Field(..., description="Número de WhatsApp com DDD (ex: 83999998888)")
    message: str = Field(..., description="Mensagem de teste a ser enviada")

class BroadcastAlertDTO(BaseModel):
    tipoSanguineo: str = Field(..., description="Tipo sanguíneo urgente (ex: O-, A+)")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    cidade: Optional[str] = Field(None, description="Cidade da emergência")
    hospital: Optional[str] = Field("Hemocentro Regional", description="Nome do hospital ou hemocentro")
    urgencia: str = Field("ALTA", description="Nível de urgência: MÉDIA, ALTA, CRÍTICA")

@router.post("/login")
def admin_login(payload: LoginDTO):
    """Valida o login do administrador (Credenciais acadêmicas: admin / admin123)"""
    if payload.username.strip().lower() == ADMIN_DEFAULT_USER and payload.password == ADMIN_DEFAULT_PASS:
        return {
            "sucesso": True,
            "token": "hemoalerta-admin-auth-token-2026",
            "admin": {
                "nome": "Administrador Geral HemoAlerta",
                "usuario": ADMIN_DEFAULT_USER,
                "role": "SUPERADMIN"
            }
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais incorretas. Use admin / admin123 para o teste acadêmico."
    )

@router.get("/whatsapp/status")
def get_whatsapp_status():
    """Retorna o status de conexão do WhatsApp Venom gerenciado pelo Python"""
    return WhatsAppService.get_status()

@router.get("/whatsapp/qrcode")
def get_whatsapp_qrcode():
    """Retorna o QR Code em base64 para autenticação com o app do WhatsApp"""
    return WhatsAppService.get_qrcode()

@router.post("/whatsapp/connect")
def connect_whatsapp():
    """Solicita a inicialização do Venom e geração do QR Code"""
    return WhatsAppService.connect()

@router.post("/whatsapp/disconnect")
def disconnect_whatsapp():
    """Desconecta a sessão do WhatsApp"""
    return WhatsAppService.disconnect()

@router.post("/whatsapp/send-test")
def send_test_message(payload: SendTestDTO):
    """Envia uma mensagem de teste para verificar se o Venom está apto a disparar"""
    res = WhatsAppService.send_message(payload.to, payload.message)
    if not res.get("success", False) and "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/whatsapp/broadcast-alert")
def broadcast_alert(payload: BroadcastAlertDTO):
    """
    Busca os doadores compatíveis no SQLite (hemoalerta.db)
    e dispara o alerta de emergência via WhatsApp
    """
    res = WhatsAppService.broadcast_alert_to_donors(
        blood_type=payload.tipoSanguineo,
        estado=payload.estado,
        cidade=payload.cidade,
        hospital=payload.hospital,
        urgencia=payload.urgencia
    )
    if not res.get("success", False) and "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
