from datetime import datetime, date
from typing import List, Dict, Any, Optional

# Matriz de doadores compatíveis para o tipo do paciente
# Chave: Tipo do Paciente que precisa de sangue
# Valor: Lista de tipos sanguíneos que PODEM DOAR para esse paciente
COMPATIBILIDADE_RECEPTOR = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
}

class MatchingService:
    @staticmethod
    def get_compatible_donor_types(patient_blood_type: str) -> List[str]:
        patient_type = patient_blood_type.strip().upper().replace("−", "-")
        return COMPATIBILIDADE_RECEPTOR.get(patient_type, [patient_type])

    @staticmethod
    def is_donor_interval_valid(last_donation_str: Optional[str], min_days: int = 60) -> bool:
        """Verifica se já se passaram ao menos min_days desde a última doação."""
        if not last_donation_str:
            return True # Nunca doou ou sem registro recente -> apto
        try:
            # Formato esperado: YYYY-MM-DD
            last_date = datetime.strptime(last_donation_str[:10], "%Y-%m-%d").date()
            days_passed = (date.today() - last_date).days
            return days_passed >= min_days
        except Exception:
            return True

    @classmethod
    def filter_compatible_donors(
        cls,
        donors: List[Dict[str, Any]],
        patient_blood_type: str,
        estado: Optional[str] = None,
        cidade: Optional[str] = None,
        require_opt_in: bool = True
    ) -> List[Dict[str, Any]]:
        compatible_types = set(cls.get_compatible_donor_types(patient_blood_type))
        result = []

        for d in donors:
            # 1. Opt-in de alertas
            if require_opt_in and not d.get("optInAlertas", True):
                continue
            
            # 2. Status ativo
            if d.get("status") == "inativo":
                continue

            # 3. Tipo sanguíneo compatível
            donor_type = (d.get("tipoSanguineo") or "").strip().upper().replace("−", "-")
            if donor_type not in compatible_types:
                continue

            # 4. Filtro por Estado (obrigatório se informado)
            if estado and d.get("estado", "").upper() != estado.upper():
                continue

            # 5. Filtro por Cidade (opcional/prioritário)
            if cidade and d.get("cidade", "").strip().lower() != cidade.strip().lower():
                # Nota: ainda podemos incluir da mesma UF, mas marcamos se é mesma cidade
                pass

            # 6. Intervalo biológico de doação
            if not cls.is_donor_interval_valid(d.get("ultimaDoacao")):
                continue

            result.append(d)

        return result
