from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional
from config.database import db

class DonorService:
    @staticmethod
    def generate_id() -> str:
        short_uuid = uuid.uuid4().hex[:6].upper()
        time_part = hex(int(datetime.now().timestamp()))[2:].upper()
        return f"DOA-{time_part}-{short_uuid}"

    @staticmethod
    def mask_phone(phone: Optional[str]) -> str:
        if not phone:
            return "•••••••••••"
        digits = "".join(filter(str.isdigit, phone))
        if len(digits) < 4:
            return "•••••••••••"
        return "••••••••" + digits[-4:]

    @classmethod
    def apply_lgpd_mask(cls, donor: Dict[str, Any], full_access: bool = False) -> Dict[str, Any]:
        """Aplica mascaramento de privacidade conforme LGPD para visualizações públicas/tabela"""
        if full_access:
            return donor.copy()
        
        safe = donor.copy()
        # Telefone mascarado para listagens gerais
        safe["whatsappExibicao"] = cls.mask_phone(safe.get("whatsapp"))
        # Email parcialmente oculto se existir
        if safe.get("email"):
            parts = safe["email"].split("@")
            if len(parts) == 2:
                safe["emailExibicao"] = parts[0][:2] + "••••@" + parts[1]
            else:
                safe["emailExibicao"] = "••••@••••"
        else:
            safe["emailExibicao"] = None

        return safe

    @classmethod
    def list_donors(
        cls,
        search: Optional[str] = None,
        blood_type: Optional[str] = None,
        state: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        full_access: bool = False
    ) -> Dict[str, Any]:
        all_donors = db.get_donors()
        filtered = all_donors

        if blood_type:
            bt_clean = blood_type.strip().upper().replace("−", "-")
            filtered = [d for d in filtered if (d.get("tipoSanguineo") or "").strip().upper().replace("−", "-") == bt_clean]

        if state:
            filtered = [d for d in filtered if d.get("estado", "").upper() == state.upper()]

        if search:
            s_term = search.strip().lower()
            filtered = [
                d for d in filtered
                if s_term in (d.get("nomeCompleto") or "").lower() or s_term in (d.get("cidade") or "").lower()
            ]

        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = [cls.apply_lgpd_mask(d, full_access=full_access) for d in filtered[start_idx:end_idx]]

        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": (total + page_size - 1) // page_size if total > 0 else 1,
            "items": items
        }

    @classmethod
    def create_donor(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        now_iso = datetime.utcnow().isoformat() + "Z"
        raw_phone = data.get("whatsapp", "")
        digits_phone = "".join(filter(str.isdigit, raw_phone))
        e164 = f"+55{digits_phone}" if digits_phone else None

        # Validação de duplicata de WhatsApp
        existing = [d for d in db.get_donors() if d.get("whatsappE164") == e164]
        if existing:
            raise ValueError("Este número de WhatsApp já possui cadastro no HemoAlerta.")

        donor_record = {
            "id": cls.generate_id(),
            "nomeCompleto": data.get("nomeCompleto", "").strip(),
            "tipoSanguineo": data.get("tipoSanguineo", "").strip().upper().replace("−", "-"),
            "dataNascimento": data.get("dataNascimento") or None,
            "cidade": data.get("cidade", "").strip(),
            "estado": data.get("estado", "").strip().upper(),
            "whatsapp": raw_phone,
            "whatsappE164": e164,
            "email": data.get("email") or None,
            "ultimaDoacao": data.get("ultimaDoacao") or None,
            "optInAlertas": bool(data.get("optInAlertas", True)),
            "consentimentoLGPD": bool(data.get("consentimentoLGPD", True)),
            "dataConsentimentoLGPD": now_iso if data.get("consentimentoLGPD") else None,
            "status": "ativo",
            "dataCadastro": now_iso
        }

        db.add_donor(donor_record)
        return donor_record

    @classmethod
    def find_for_auth(cls, email: str, phone: str) -> Optional[Dict[str, Any]]:
        clean_phone = "".join(filter(str.isdigit, phone))
        clean_email = email.strip().lower()

        for d in db.get_donors():
            donor_digits = "".join(filter(str.isdigit, d.get("whatsapp") or ""))
            donor_email = (d.get("email") or "").strip().lower()
            if donor_email == clean_email and donor_digits == clean_phone:
                return d
        return None

    @classmethod
    def update_donor(cls, donor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "whatsapp" in updates:
            digits = "".join(filter(str.isdigit, updates["whatsapp"]))
            updates["whatsappE164"] = f"+55{digits}" if digits else None

        if "tipoSanguineo" in updates:
            updates["tipoSanguineo"] = updates["tipoSanguineo"].strip().upper().replace("−", "-")

        return db.update_donor(donor_id, updates)

    @classmethod
    def delete_donor(cls, donor_id: str) -> bool:
        return db.delete_donor(donor_id)

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        donors = db.get_donors()
        total = len(donors)
        active = len([d for d in donors if d.get("optInAlertas") and d.get("status") != "inativo"])
        universal_donors = len([d for d in donors if (d.get("tipoSanguineo") or "").replace("−", "-") == "O-"])
        
        # Estados com doadores
        state_distribution: Dict[str, int] = {}
        for d in donors:
            uf = d.get("estado", "").upper()
            if uf:
                state_distribution[uf] = state_distribution.get(uf, 0) + 1

        blood_types_count: Dict[str, int] = {}
        for d in donors:
            bt = (d.get("tipoSanguineo") or "NS").replace("−", "-")
            blood_types_count[bt] = blood_types_count.get(bt, 0) + 1

        return {
            "totalDoadores": total,
            "doadoresAtivos": active,
            "vidasSalvasEstimadas": total * 4,
            "doadoresUniversais": universal_donors,
            "estadosAtivos": len(state_distribution),
            "distribuicaoPorEstado": state_distribution,
            "distribuicaoPorTipo": blood_types_count
        }
