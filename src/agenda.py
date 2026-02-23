"""
agenda.py
Responsável por:
- Conectar à Google Calendar API
- Listar eventos do dia
- Extrair dados das monitorias (nome, matrícula, agente, meet_id)
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = BASE_DIR / "credentials" / "agenda.json"

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

MEET_RE = re.compile(r"https?://meet\.google\.com/([a-z]{3}-[a-z]{4}-[a-z]{3})", re.I)

def conectar_agenda():
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH, SCOPES
    )
    creds = flow.run_local_server(port=0)
    service = build('calendar', 'v3', credentials=creds)
    return service

TZ = ZoneInfo("America/Sao_Paulo")

def eventos_do_dia(service):
    # 🔧 TESTE: buscar monitorias de ONTEM
    agora = datetime.now(TZ)
    inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = inicio + timedelta(days=1)

    eventos = service.events().list(
        calendarId="primary",
        timeMin=inicio.isoformat(),  # ✅ com -03:00 embutido
        timeMax=fim.isoformat(),     # ✅ com -03:00 embutido
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return eventos.get("items", [])

def extrair_dados(summary: str):
    s = (summary or "").strip()

    partes = s.split(" and ", 1)
    aluno_texto = partes[0].strip()
    agente = partes[1].strip() if len(partes) > 1 else ""
    m = re.search(r"\b([A-Z]{2,10}\d{2,10})\b$", aluno_texto)
    if m:
        matricula = m.group(1)
        nome_aluno = aluno_texto[:m.start()].strip()
    else:
        nome_aluno = aluno_texto.strip()
        matricula = ""

    return nome_aluno, matricula, agente


def extrair_meet_id(evento: dict) -> str | None:
    # 1) hangoutLink (muito comum)
    link = evento.get("hangoutLink")
    if link:
        m = MEET_RE.search(link)
        if m:
            return m.group(1).lower()

    # 2) conferenceData.entryPoints (às vezes vem aqui)
    conf = evento.get("conferenceData", {})
    for ep in conf.get("entryPoints", []):
        uri = ep.get("uri") or ""
        m = MEET_RE.search(uri)
        if m:
            return m.group(1).lower()

    # 3) description (às vezes alguém cola link lá)
    desc = evento.get("description") or ""
    m = MEET_RE.search(desc)
    if m:
        return m.group(1).lower()

    return None

def monitorias_do_dia(service):
    eventos = eventos_do_dia(service)
    monitorias = []

    for evento in eventos:
        nome, matricula, agente = extrair_dados(evento['summary'])
        data = evento['start']['dateTime'][:10]
        meet_id = extrair_meet_id(evento)
        monitorias.append({
            "nome": nome,
            "matricula": matricula,
            "agente": agente,
            "data": data,
            "meet_id": meet_id,
            "titulo": evento.get("summary", "")
        })

    return monitorias

