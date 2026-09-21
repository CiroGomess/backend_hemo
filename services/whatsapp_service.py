import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from config.database import db
from services.matching_service import MatchingService

VENOM_SERVICE_URL = "http://127.0.0.1:8001"

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
    def send_message(cls, to: str, message: str) -> Dict[str, Any]:
        """Envia uma mensagem de texto direta para um número de WhatsApp"""
        return cls._make_request("/send", method="POST", data={"to": to, "message": message})

    @classmethod
    def broadcast_alert_to_donors(
        cls,
        blood_type: str,
        estado: str,
        cidade: Optional[str] = None,
        hospital: Optional[str] = None,
        urgencia: str = "ALTA"
    ) -> Dict[str, Any]:
        """
        Localiza doadores compatíveis no SQLite (hemoalerta.db)
        e dispara mensagens de emergência via Venom WhatsApp
        """
        # Tipos sanguíneos compatíveis que podem doar para este receptor
        compat_types = MatchingService.get_compatible_donors(blood_type)

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
              AND status = 'ATIVO'
        """

        if cidade:
            query += " AND LOWER(cidade) = ?"
            params.append(cidade.lower())

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

        base_msg = (
            f"🚨 *ALERTA DE EMERGÊNCIA - HEMOALERTA* 🚨\n\n"
            f"Olá {{nome}},\n"
            f"Precisamos com *URGÊNCIA MÁXIMA ({urgencia})* de doação de sangue tipo *{blood_type}* "
            f"em {cidade or 'sua região'} / {estado.upper()}.\n\n"
            f"🏥 Local/Hospital: {hospital or 'Hemocentro Regional'}\n"
            f"❤️ Você está cadastrado no HemoAlerta como compatível.\n\n"
            f"Se você puder doar hoje ou nos próximos dias, por favor responda esta mensagem ou dirija-se ao hemocentro.\n"
            f"Cada bolsa salva até 4 vidas! 🙏"
        )

        result = cls._make_request("/broadcast", method="POST", data={
            "recipients": recipients,
            "message": base_msg
        })

        result["totalEncontrados"] = len(recipients)
        return result
