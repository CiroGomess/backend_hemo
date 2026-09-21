import sqlite3
import json
from typing import List, Dict, Any, Optional
from config.settings import DB_PATH, SEED_FILE

class SQLiteDatabase:
    def __init__(self):
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabela de Doadores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doadores (
                    id TEXT PRIMARY KEY,
                    nome_completo TEXT NOT NULL,
                    tipo_sanguineo TEXT NOT NULL,
                    data_nascimento TEXT,
                    cidade TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    whatsapp TEXT NOT NULL,
                    whatsapp_e164 TEXT,
                    email TEXT,
                    ultima_doacao TEXT,
                    opt_in_alertas INTEGER NOT NULL DEFAULT 1,
                    consentimento_lgpd INTEGER NOT NULL DEFAULT 1,
                    data_consentimento_lgpd TEXT,
                    status TEXT NOT NULL DEFAULT 'ativo',
                    data_cadastro TEXT NOT NULL
                )
            """)

            # Tabela de Emergências SOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergencias (
                    id TEXT PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    quantidade TEXT NOT NULL,
                    paciente TEXT NOT NULL,
                    cidade TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    urgencia TEXT NOT NULL,
                    contato TEXT NOT NULL,
                    detalhes TEXT,
                    doadores_notificados INTEGER DEFAULT 0,
                    tipos_compativeis TEXT,
                    mensagem_texto TEXT,
                    whatsapp_share_link TEXT,
                    criado_em TEXT NOT NULL
                )
            """)

            # Tabela de Hemocentros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hemocentros (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    cidade TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    endereco TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    horario TEXT NOT NULL
                )
            """)
            conn.commit()

        self._seed_initial_data()

    def _seed_initial_data(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de doadores agora opera exclusivamente com cadastros reais
            # (Sem dados mockados pré-carregados)

            # Popula hemocentros se vazia
            cursor.execute("SELECT COUNT(*) FROM hemocentros")
            if cursor.fetchone()[0] == 0:
                initial_hemos = [
                    ("HEMO-SP-01", "Fundação Pró-Sangue - Posto Clínicas", "hemocentro", "São Paulo", "SP", "Av. Dr. Enéas Carvalho de Aguiar, 155", "(11) 4573-7800", "Seg-Sex: 8h-17h, Sáb: 8h-16h"),
                    ("HEMO-SP-02", "Hemocentro de Campinas (Unicamp)", "hemocentro", "Campinas", "SP", "R. Carlos Chagas, 480 - Barão Geraldo", "(19) 3521-8705", "Seg-Sáb: 7h30-15h"),
                    ("HEMO-SP-03", "Hospital das Clínicas de Ribeirão Preto", "hospital", "Ribeirão Preto", "SP", "Campus Universitário Monte Alegre", "(16) 3602-1000", "24h (Doação 7h-13h)"),
                    ("HEMO-RJ-01", "HEMORIO - Instituto Estadual de Hematologia", "hemocentro", "Rio de Janeiro", "RJ", "Rua Frei Caneca, 8 - Centro", "(21) 3916-8300", "Diariamente: 7h-18h"),
                    ("HEMO-MG-01", "Fundação Hemominas - Hemocentro BH", "hemocentro", "Belo Horizonte", "MG", "Alameda Ezequiel Dias, 321 - Santa Efigênia", "(31) 3768-4500", "Seg-Sáb: 7h-18h"),
                    ("HEMO-BA-01", "HEMOBA - Fundação de Hematologia", "hemocentro", "Salvador", "BA", "Ladeira do HGE, s/n - Brotas", "(71) 3116-5664", "Seg-Sex: 7h30-18h, Sáb: 7h-12h30"),
                    ("HEMO-DF-01", "Fundação Hemocentro de Brasília", "hemocentro", "Brasília", "DF", "SMHN Quadra 3 Conjunto A Bloco 3", "(61) 3327-4447", "Seg-Sáb: 7h15-18h"),
                    ("HEMO-PR-01", "HEMEPAR Curitiba", "hemocentro", "Curitiba", "PR", "Travessa João Prosdócimo, 145 - Alto da XV", "(41) 3281-4000", "Seg-Sex: 7h30-18h30, Sáb: 8h-17h"),
                    ("HEMO-RS-01", "Hemocentro do RS (HEMORGS)", "hemocentro", "Porto Alegre", "RS", "Av. Bento Gonçalves, 3722 - Partenon", "(51) 3336-6755", "Seg-Sex: 8h-16h"),
                    ("HEMO-PE-01", "HEMOPE - Hemocentro do Recife", "hemocentro", "Recife", "PE", "R. Joaquim Nabuco, 171 - Graças", "(81) 3182-4600", "Seg-Sáb: 7h15-18h30"),
                    ("HEMO-CE-01", "HEMOCE - Centro de Hemoterapia", "hemocentro", "Fortaleza", "CE", "Av. José Bastos, 3390 - Rodolfo Teófilo", "(85) 3101-2296", "Seg-Sex: 7h-18h30, Sáb: 7h-17h30")
                ]
                cursor.executemany("""
                    INSERT INTO hemocentros (id, nome, tipo, cidade, estado, endereco, telefone, horario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, initial_hemos)
                conn.commit()

    @staticmethod
    def _row_to_donor(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "nomeCompleto": row["nome_completo"],
            "tipoSanguineo": row["tipo_sanguineo"],
            "dataNascimento": row["data_nascimento"],
            "cidade": row["cidade"],
            "estado": row["estado"],
            "whatsapp": row["whatsapp"],
            "whatsappE164": row["whatsapp_e164"],
            "email": row["email"],
            "ultimaDoacao": row["ultima_doacao"],
            "optInAlertas": bool(row["opt_in_alertas"]),
            "consentimentoLGPD": bool(row["consentimento_lgpd"]),
            "dataConsentimentoLGPD": row["data_consentimento_lgpd"],
            "status": row["status"],
            "dataCadastro": row["data_cadastro"]
        }

    # ==========================
    # MÉTODOS DE DOADORES
    # ==========================
    def get_donors(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doadores ORDER BY data_cadastro DESC")
            return [self._row_to_donor(r) for r in cursor.fetchall()]

    def get_donor_by_id(self, donor_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doadores WHERE id = ?", (donor_id,))
            row = cursor.fetchone()
            return self._row_to_donor(row) if row else None

    def add_donor(self, d: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO doadores (
                    id, nome_completo, tipo_sanguineo, data_nascimento, cidade, estado,
                    whatsapp, whatsapp_e164, email, ultima_doacao, opt_in_alertas,
                    consentimento_lgpd, data_consentimento_lgpd, status, data_cadastro
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["id"],
                d["nomeCompleto"],
                d["tipoSanguineo"],
                d.get("dataNascimento"),
                d["cidade"],
                d["estado"],
                d["whatsapp"],
                d.get("whatsappE164"),
                d.get("email"),
                d.get("ultimaDoacao"),
                1 if d.get("optInAlertas", True) else 0,
                1 if d.get("consentimentoLGPD", True) else 0,
                d.get("dataConsentimentoLGPD"),
                d.get("status", "ativo"),
                d["dataCadastro"]
            ))
            conn.commit()

    def update_donor(self, donor_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        field_mapping = {
            "nomeCompleto": "nome_completo",
            "tipoSanguineo": "tipo_sanguineo",
            "dataNascimento": "data_nascimento",
            "cidade": "cidade",
            "estado": "estado",
            "whatsapp": "whatsapp",
            "whatsappE164": "whatsapp_e164",
            "email": "email",
            "ultimaDoacao": "ultima_doacao",
            "optInAlertas": "opt_in_alertas",
            "status": "status"
        }

        sql_sets = []
        params = []
        for k, v in updates.items():
            if k in field_mapping:
                col = field_mapping[k]
                sql_sets.append(f"{col} = ?")
                if k == "optInAlertas":
                    params.append(1 if v else 0)
                else:
                    params.append(v)

        if not sql_sets:
            return self.get_donor_by_id(donor_id)

        params.append(donor_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE doadores SET {', '.join(sql_sets)} WHERE id = ?", params)
            conn.commit()

        return self.get_donor_by_id(donor_id)

    def delete_donor(self, donor_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doadores WHERE id = ?", (donor_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==========================
    # MÉTODOS DE EMERGÊNCIAS
    # ==========================
    def add_emergency(self, em: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO emergencias (
                    id, tipo, quantidade, paciente, cidade, estado, urgencia, contato,
                    detalhes, doadores_notificados, tipos_compativeis, mensagem_texto,
                    whatsapp_share_link, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                em["id"],
                em["tipo"],
                str(em["quantidade"]),
                em["paciente"],
                em["cidade"],
                em["estado"],
                em["urgencia"],
                em["contato"],
                em.get("detalhes", ""),
                em.get("doadoresAptosNotificados", 0),
                json.dumps(em.get("tiposCompativeis", [])),
                em.get("mensagemTexto", ""),
                em.get("whatsappShareLink", ""),
                em["criadoEm"]
            ))
            conn.commit()
            return em

    def get_emergencies(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emergencias ORDER BY criado_em DESC")
            items = []
            for r in cursor.fetchall():
                items.append({
                    "id": r["id"],
                    "tipo": r["tipo"],
                    "quantidade": r["quantidade"],
                    "paciente": r["paciente"],
                    "cidade": r["cidade"],
                    "estado": r["estado"],
                    "urgencia": r["urgencia"],
                    "contato": r["contato"],
                    "detalhes": r["detalhes"],
                    "doadoresAptosNotificados": r["doadores_notificados"],
                    "tiposCompativeis": json.loads(r["tipos_compativeis"] or "[]"),
                    "mensagemTexto": r["mensagem_texto"],
                    "whatsappShareLink": r["whatsapp_share_link"],
                    "criadoEm": r["criado_em"]
                })
            return items

    # ==========================
    # MÉTODOS DE HEMOCENTROS
    # ==========================
    def get_hemocentros(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hemocentros ORDER BY estado, nome")
            items = []
            for r in cursor.fetchall():
                items.append({
                    "id": r["id"],
                    "nome": r["nome"],
                    "tipo": r["tipo"],
                    "cidade": r["cidade"],
                    "estado": r["estado"],
                    "endereco": r["endereco"],
                    "telefone": r["telefone"],
                    "horario": r["horario"]
                })
            return items

db = SQLiteDatabase()
