from datetime import datetime
import urllib.parse
from typing import Dict, Any, List
from config.database import db
from services.matching_service import MatchingService

class EmergencyService:
    EMOJI_URGENCIA = {
        "CRÍTICA": "🔴",
        "ALTA": "🟠",
        "MÉDIA": "🟡"
    }

    @classmethod
    def calculate_compatibility(cls, blood_type: str, estado: str, cidade: str = None) -> Dict[str, Any]:
        all_donors = db.get_donors()
        compatible_donors = MatchingService.filter_compatible_donors(
            donors=all_donors,
            patient_blood_type=blood_type,
            estado=estado,
            cidade=cidade,
            require_opt_in=True
        )
        compatible_types = MatchingService.get_compatible_donor_types(blood_type)

        return {
            "tipoReceptor": blood_type,
            "tiposCompativeis": compatible_types,
            "estado": estado,
            "cidade": cidade,
            "totalAptos": len(compatible_donors),
            "doadoresIds": [d.get("id") for d in compatible_donors]
        }

    @classmethod
    def create_emergency(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        blood_type = data.get("tipo", "O+").strip().upper().replace("−", "-")
        estado = data.get("estado", "").upper()
        cidade = data.get("cidade", "")
        urgencia = data.get("urgencia", "ALTA").upper()
        emoji = cls.EMOJI_URGENCIA.get(urgencia, "🔴")
        qtd = str(data.get("quantidade", 1))
        paciente = data.get("paciente", "Paciente em atendimento emergencial")
        contato = data.get("contato", "")
        detalhes = data.get("mensagem", "")

        # Filtra doadores compatíveis
        matching_info = cls.calculate_compatibility(blood_type, estado, cidade)
        
        # Gera texto formatado para WhatsApp
        message_lines = [
            f"{emoji} *ALERTA DE EMERGÊNCIA — HEMOALERTA*",
            f"Tipo sanguíneo necessário: *{blood_type}*",
            f"Quantidade: *{qtd} bolsa(s)*",
            f"Instituição/Paciente: *{paciente}*",
            f"Local: *{cidade} - {estado}*",
            f"Contato de Emergência: *{contato}*",
        ]
        if detalhes:
            message_lines.append(f"Detalhes: _{detalhes}_")
        
        message_lines.extend([
            "",
            "🩸 *Você é um doador compatível cadastrado!*",
            "Sua doação faz a diferença agora. Por favor, compareça ao hemocentro mais próximo ou responda esta mensagem."
        ])

        full_message = "\n".join(message_lines)
        encoded_message = urllib.parse.quote(full_message)
        whatsapp_direct_link = f"https://api.whatsapp.com/send?text={encoded_message}"

        emergency_record = {
            "id": f"SOS-{int(datetime.now().timestamp())}",
            "tipo": blood_type,
            "quantidade": qtd,
            "paciente": paciente,
            "cidade": cidade,
            "estado": estado,
            "urgencia": urgencia,
            "contato": contato,
            "detalhes": detalhes,
            "doadoresAptosNotificados": matching_info["totalAptos"],
            "tiposCompativeis": matching_info["tiposCompativeis"],
            "mensagemTexto": full_message,
            "whatsappShareLink": whatsapp_direct_link,
            "criadoEm": datetime.utcnow().isoformat() + "Z"
        }

        db.add_emergency(emergency_record)
        return emergency_record
