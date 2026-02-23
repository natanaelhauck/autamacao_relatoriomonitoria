from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# ✅ pega a raiz do projeto (um nível acima de /src)
BASE_DIR = Path(__file__).resolve().parent.parent

# tenta alguns lugares comuns
CANDIDATAS = [
    BASE_DIR / "read_payloads",            # projeto/read_payloads
    BASE_DIR / "data" / "read_payloads",   # projeto/data/read_payloads (se você organizar assim)
    Path.cwd() / "read_payloads",          # se você rodar na raiz
]

PASTA_READ = next((p for p in CANDIDATAS if p.exists()), BASE_DIR / "read_payloads")


def _carregar_payloads():
    payloads = []
    if not PASTA_READ.exists():
        return payloads

    for arq in PASTA_READ.glob("*.json"):
        try:
            data = json.loads(arq.read_text(encoding="utf-8"))
            data["_arquivo"] = str(arq)
            payloads.append(data)
        except Exception:
            pass
    return payloads


import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")
MAT_RE = re.compile(r"\b([A-Z]{2,10}\d{2,10})\b")

def _normalizar(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # remove acento
    s = " ".join(s.lower().split())
    return s

def _parse_iso_dt(s: str) -> datetime | None:
    if not s:
        return None
    s = s.strip()

    # ✅ trata timestamps tipo "2026-02-03T12:34:56Z"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _payload_date_local(p: dict) -> str | None:
    dt = _parse_iso_dt(p.get("start_time") or "")
    if not dt:
        return None

    # ✅ garante timezone e converte para SP
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    else:
        dt = dt.astimezone(TZ)

    return dt.date().isoformat()


def _extrair_matricula(texto: str) -> str | None:
    m = MAT_RE.search(texto or "")
    return m.group(1) if m else None

def _mais_recente(payloads: list[dict]) -> dict | None:
    def key(p):
        return _parse_iso_dt(p.get("start_time") or "") or datetime.min
    return sorted(payloads, key=key, reverse=True)[0] if payloads else None


def analisar_monitoria(titulo_agenda: str, meet_id_agenda: str | None, data_execucao: str):
    payloads = _carregar_payloads()
    payloads = [p for p in payloads if (p.get("trigger") or "").strip().lower() == "meeting_end"]

    # ✅ só payloads do dia que você está rodando
    payloads_dia = [p for p in payloads if _payload_date_local(p) == data_execucao]

    if not payloads_dia:
        return {"presenca": "Falta", "link": "", "relatorio": "", "payload": None}

    # 1) match por meet_id (melhor)
    if meet_id_agenda:
        mid = meet_id_agenda.strip().lower()
        for p in payloads_dia:
            if (p.get("platform_meeting_id") or "").strip().lower() == mid:
                return {
                    "presenca": "Presente",
                    "link": p.get("report_url", "") or "",
                    "relatorio": p.get("summary", "") or "",
                    "payload": p
                }

    # 2) match por matrícula (muito confiável)
    mat = _extrair_matricula(titulo_agenda)
    if mat:
        mat_norm = mat.lower()
        cand = []
        for p in payloads_dia:
            t = (p.get("title") or "")
            if mat_norm in (t.lower()):
                cand.append(p)
        if cand:
            p = _mais_recente(cand)
            return {
                "presenca": "Presente",
                "link": p.get("report_url", "") or "",
                "relatorio": p.get("summary", "") or "",
                "payload": p
            }

    # 3) match por título normalizado (fallback)
    t_norm = _normalizar(titulo_agenda)
    cand = [p for p in payloads_dia if _normalizar(p.get("title", "")) == t_norm]
    if cand:
        p = _mais_recente(cand)
        return {
            "presenca": "Presente",
            "link": p.get("report_url", "") or "",
            "relatorio": p.get("summary", "") or "",
            "payload": p
        }

    return {"presenca": "Falta", "link": "", "relatorio": "", "payload": None}


    # resto igual: match por meet_id, depois por título...
def debug_read_datas():
    payloads = _carregar_payloads()
    payloads = [p for p in payloads if (p.get("trigger") or "").strip().lower() == "meeting_end"]

    datas = {}
    for p in payloads:
        d = _payload_date_local(p)
        if d:
            datas[d] = datas.get(d, 0) + 1

    print("\n🧪 DEBUG READ DATAS (meeting_end)")
    print("📂 Pasta Read:", PASTA_READ)
    print("📦 Total:", len(payloads))
    print("📅 Datas encontradas:")
    for k in sorted(datas.keys()):
        print(f"  {k}: {datas[k]}")
    print("🧪 FIM DEBUG\n")


