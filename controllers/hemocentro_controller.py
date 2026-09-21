from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from services.hemocentro_service import HemocentroService
from config.database import db
import uuid

router = APIRouter(prefix="/hemocentros", tags=["Hemocentros"])

class HemocentroCreateDTO(BaseModel):
    nome: str = Field(..., description="Nome do hemocentro ou hospital")
    tipo: str = Field("hemocentro", description="Tipo: hemocentro, hospital, clinica, posto")
    cidade: str = Field(..., description="Cidade")
    estado: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    endereco: str = Field(..., description="Endereço completo")
    telefone: str = Field(..., description="Telefone de contato")
    horario: Optional[str] = Field("Seg-Sex: 8h-17h", description="Horário de funcionamento")

@router.get("")
def list_hemocentros(
    estado: Optional[str] = Query(None, description="Sigla da UF (ex: SP, RJ)"),
    tipo: Optional[str] = Query(None, description="Tipo de estabelecimento: hemocentro, hospital, clinica"),
    cidade: Optional[str] = Query(None, description="Nome da cidade")
):
    """Busca postos de coleta e hemocentros com filtros geográficos"""
    return HemocentroService.list_hemocentros(estado=estado, tipo=tipo, cidade=cidade)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_hemocentro(payload: HemocentroCreateDTO):
    """Cadastra um novo hemocentro/posto de coleta no banco SQLite"""
    try:
        new_id = f"HEMO-{payload.estado.upper()}-{uuid.uuid4().hex[:4].upper()}"
        data = {
            "id": new_id,
            "nome": payload.nome,
            "tipo": payload.tipo.lower(),
            "cidade": payload.cidade,
            "estado": payload.estado.upper(),
            "endereco": payload.endereco,
            "telefone": payload.telefone,
            "horario": payload.horario or "Seg-Sex: 8h-17h"
        }
        saved = db.add_hemocentro(data)
        return {
            "sucesso": True,
            "mensagem": "Hemocentro cadastrado com sucesso!",
            "hemocentro": saved
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{hemocentro_id}")
def delete_hemocentro(hemocentro_id: str):
    """Remove um hemocentro pelo ID"""
    deleted = db.delete_hemocentro(hemocentro_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Hemocentro não encontrado.")
    return {"sucesso": True, "mensagem": "Hemocentro removido com sucesso."}
