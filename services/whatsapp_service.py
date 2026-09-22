import json
import urllib.request
import urllib.error
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.database import db
from config.settings import VENOM_SERVICE_URL
from services.matching_service import MatchingService

# Caminhos e URLs da arte oficial
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ART_IMAGE_PATH = str(BASE_DIR / "frontend_hemo" / "public" / "art.jpeg")
BACKEND_ART_PATH = str(Path(__file__).resolve().parent.parent / "art.jpeg")
PROD_ART_URL = "https://hemoalert.squareweb.app/art.jpeg"

class WhatsAppService:
    @staticmethod
    def _make_request(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{VENOM_SERVICE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        body = json.dumps(data).encode("utf-8") if data else None

        try:
            with urllib.request.urlopen(req, data=body, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode("utf-8"))
            except Exception:
                return {
                    "success": False,
                    "error": f"Erro no serviço Venom (HTTP {e.code})"
                }
        except urllib.error.URLError as e:
            return {
                "status": "OFFLINE",
                "error": f"Serviço Venom WhatsApp offline ou não iniciado ({str(e.reason)})",
                "hasQrCode": False
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "hasQrCode": False
            }

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Obtém o status atual do WhatsApp no serviço Venom"""
        return cls._make_request("/status")

    @classmethod
    def get_qrcode(cls) -> Dict[str, Any]:
        """Obtém a imagem base64 do QR Code para autenticação"""
        return cls._make_request("/qrcode")

    @classmethod
    def connect(cls) -> Dict[str, Any]:
        """Solicita ao Venom a inicialização do navegador e geração do QR Code"""
        return cls._make_request("/connect", method="POST")

    @classmethod
    def disconnect(cls) -> Dict[str, Any]:
        """Encerra a sessão atual do WhatsApp"""
        return cls._make_request("/disconnect", method="POST")
    @classmethod
    def get_art_image_path(cls) -> Optional[str]:
        if os.path.exists(ART_IMAGE_PATH):
            return ART_IMAGE_PATH
        if os.path.exists(BACKEND_ART_PATH):
            return BACKEND_ART_PATH
        return PROD_ART_URL

    @classmethod
    def send_message(cls, to: str, message: str, send_art: bool = True) -> Dict[str, Any]:
        """Envia uma mensagem de texto (e opcionalmente arte) para um número de WhatsApp"""
        data = {"to": to, "message": message}
        art = cls.get_art_image_path()
        if send_art and art:
            data["imagePath"] = art
        return cls._make_request("/send", method="POST", data=data)

    @classmethod
    def broadcast_alert_to_donors(
        cls,
        blood_type: str,
        estado: str,
        cidade: Optional[str] = None,
        hospital: Optional[str] = None,
        urgencia: str = "ALTA",
        custom_message: Optional[str] = None,
        send_art: bool = True
    ) -> Dict[str, Any]:
        """
        Localiza doadores compatíveis no SQLite (hemoalerta.db)
        e dispara mensagens de emergência com arte via WhatsApp 1 por 1
        """
        # Tipos sanguíneos compatíveis que podem doar para este receptor
        compat_types = MatchingService.get_compatible_donor_types(blood_type)

        conn = db.get_connection()
        cursor = conn.cursor()

        placeholders = ",".join(["?"] * len(compat_types))
        params: List[Any] = list(compat_types)
        params.append(estado.upper())

        query = f"""
            SELECT id, nome_completo, tipo_sanguineo, whatsapp, cidade, estado
            FROM doadores
            WHERE tipo_sanguineo IN ({placeholders})
              AND UPPER(estado) = ?
              AND opt_in_alertas = 1
              AND LOWER(status) = 'ativo'
        """

        if cidade and cidade.strip():
            query += " AND LOWER(cidade) = ?"
            params.append(cidade.strip().lower())

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        recipients = []
        for r in rows:
            recipients.append({
                "id": r["id"],
                "nome": r["nome_completo"],
                "tipo": r["tipo_sanguineo"],
                "whatsapp": r["whatsapp"],
                "cidade": r["cidade"],
                "estado": r["estado"]
            })

        if not recipients:
            return {
                "sucesso": True,
                "totalEncontrados": 0,
                "totalEnviados": 0,
                "mensagem": "Nenhum doador compatível com alertas ativos encontrado para esta localidade."
            }

        if custom_message:
            base_msg = custom_message
        else:
            base_msg = (
                f"🚨 *CONVOCAÇÃO DE EMERGÊNCIA - HEMOALERTA* 🚨\n\n"
                f"Olá {{nome}},\n"
                f"Precisamos com urgência ({urgencia}) de sangue tipo *{blood_type}* na região de {cidade or 'sua localidade'} - {estado.upper()}.\n\n"
                f"🏥 *Local da Doação:* {hospital or 'Hemocentro Regional'}\n"
                f"🩸 *Compatibilidade:* Você é um doador compatível cadastrado no HemoAlerta.\n\n"
                f"Por favor, compareça ao hemocentro para doar e ajude a salvar vidas hoje. Sua ajuda é fundamental! 🙏"
            )

        payload_data = {
            "recipients": recipients,
            "message": base_msg
        }
        art = cls.get_art_image_path()
        if send_art and art:
            payload_data["imagePath"] = art

        result = cls._make_request("/broadcast", method="POST", data=payload_data)
        result["totalEncontrados"] = len(recipients)
        return result
