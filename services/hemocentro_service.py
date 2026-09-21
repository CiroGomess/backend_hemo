from typing import List, Dict, Any, Optional
from config.database import db

class HemocentroService:
    @classmethod
    def list_hemocentros(
        cls,
        estado: Optional[str] = None,
        tipo: Optional[str] = None,
        cidade: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        items = db.get_hemocentros()

        if estado:
            items = [h for h in items if h.get("estado", "").upper() == estado.upper()]

        if tipo:
            items = [h for h in items if h.get("tipo", "").lower() == tipo.lower()]

        if cidade:
            items = [h for h in items if cidade.lower() in h.get("cidade", "").lower()]

        return items
