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
        hospital = data.get("hospital", "Hemocentro / Hospital de Referência")
        contato = data.get("contato", "")
        detalhes = data.get("mensagem", "")

        # Filtra doadores compatíveis
        matching_info = cls.calculate_compatibility(blood_type, estado, cidade)
        
        # Gera texto formatado para WhatsApp oficial
        message_lines = [
            f"{emoji} *ALERTA DE EMERGÊNCIA — HEMOALERTA*",
            f"Tipo sanguíneo urgente: *{blood_type}*",
            f"Quantidade: *{qtd} bolsa(s)*",
            f"Paciente/Instituição: *{paciente}*",
            f"🏥 Hospital/Hemocentro: *{hospital}*",
            f"Local: *{cidade} - {estado}*",
            f"Contato para Dúvidas: *{contato}*",
        ]
        if detalhes:
            message_lines.append(f"Observações: _{detalhes}_")
        
        message_lines.extend([
            "",
            "🩸 *Você é um doador compatível cadastrado!*",
            f"Por favor, dirija-se ao *{hospital}* para realizar a sua doação de sangue.",
            "Cada doação salva até 4 vidas. Contamos com você! 🙏"
        ])

        full_message = "\n".join(message_lines)
        encoded_message = urllib.parse.quote(full_message)
        whatsapp_direct_link = f"https://api.whatsapp.com/send?text={encoded_message}"

        emergency_record = {
            "id": f"SOS-{int(datetime.now().timestamp())}",
            "tipo": blood_type,
            "quantidade": qtd,
            "paciente": paciente,
            "hospital": hospital,
            "cidade": cidade,
            "estado": estado,
            "urgencia": urgencia,
            "contato": contato,
            "detalhes": detalhes,
            "status": "PENDENTE",
            "doadoresAptosNotificados": matching_info["totalAptos"],
            "tiposCompativeis": matching_info["tiposCompativeis"],
            "mensagemTexto": full_message,
            "whatsappShareLink": whatsapp_direct_link,
            "criadoEm": datetime.utcnow().isoformat() + "Z"
        }

        db.add_emergency(emergency_record)
        return emergency_record

    @classmethod
    def get_regional_availability(cls, estado: str, cidade: str = None) -> Dict[str, Any]:
        """Consulta os tipos sanguíneos com doadores reais cadastrados na UF e Cidade"""
        return db.get_doadores_summary_by_region(estado=estado, cidade=cidade)

    @classmethod
    def approve_and_broadcast_emergency(cls, emergency_id: str, admin_user: str = "admin") -> Dict[str, Any]:
        """Aprova um chamado e dispara mensagens 1 por 1 aos doadores compatíveis com arte anexada"""
        from services.whatsapp_service import WhatsAppService

        em = db.get_emergency_by_id(emergency_id)
        if not em:
            raise ValueError(f"Emergência {emergency_id} não encontrada.")

        if em.get("status") == "DISPARADO":
            return {
                "sucesso": False,
                "mensagem": f"O alerta {emergency_id} já foi disparado anteriormente.",
                "emergencia": em
            }

        # Dispara o alerta com a arte art.jpeg anexada
        broadcast_res = WhatsAppService.broadcast_alert_to_donors(
            blood_type=em["tipo"],
            estado=em["estado"],
            cidade=em["cidade"],
            hospital=em["hospital"],
            urgencia=em["urgencia"],
            custom_message=em["mensagemTexto"],
            send_art=True
        )

        sent_count = broadcast_res.get("sentCount", 0)
        fail_count = broadcast_res.get("failCount", 0)
        aprovado_em = datetime.utcnow().isoformat() + "Z"

        db.update_emergency_status(
            em_id=emergency_id,
            status="DISPARADO",
            aprovado_por=admin_user,
            aprovado_em=aprovado_em,
            sucessos=sent_count,
            falhas=fail_count
        )

        updated_em = db.get_emergency_by_id(emergency_id)
        return {
            "sucesso": True,
            "mensagem": f"Alerta {emergency_id} aprovado e disparado com sucesso!",
            "disparo": broadcast_res,
            "emergencia": updated_em
        }

    @classmethod
    def cancel_emergency(cls, emergency_id: str, admin_user: str = "admin") -> Dict[str, Any]:
        """Cancela uma solicitação de emergência"""
        em = db.get_emergency_by_id(emergency_id)
        if not em:
            raise ValueError(f"Emergência {emergency_id} não encontrada.")

        db.update_emergency_status(
            em_id=emergency_id,
            status="CANCELADO",
            aprovado_por=admin_user,
            aprovado_em=datetime.utcnow().isoformat() + "Z"
        )
        return {"sucesso": True, "mensagem": f"Emergência {emergency_id} cancelada com sucesso."}
