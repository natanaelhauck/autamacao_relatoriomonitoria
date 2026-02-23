from __future__ import annotations

import re
import requests
from typing import Dict, List, Union

FORM_VIEW_URL = "https://docs.google.com/forms/d/e/1FAIpQLScqJcE8_wd3NrCdaP36TyotY8b9LMk1mRI6ceAZ8symajfz7g/viewform"

# seus entry ids
ENTRY_NOME = "entry.615656428"
ENTRY_MATRICULA = "entry.531507362"

# Data no Forms dividido
ENTRY_DATA_YEAR = "entry.1496596961_year"
ENTRY_DATA_MONTH = "entry.1496596961_month"
ENTRY_DATA_DAY = "entry.1496596961_day"

ENTRY_AGENTE = "entry.1608308280"
ENTRY_STATUS = "entry.5905294"

ENTRY_RELATORIO = "entry.1761763556"
ENTRY_LINK = "entry.1753304014"

# Checkbox "Visto no Ava"
ENTRY_CURSO = "entry.1419043947"


def view_to_form_response(view_url: str) -> str:
    # troca /viewform por /formResponse
    if "viewform" in view_url:
        return view_url.split("viewform")[0] + "formResponse"
    # se já vier formResponse, devolve
    if "formResponse" in view_url:
        return view_url
    # fallback: tenta apenas adicionar /formResponse
    if view_url.endswith("/"):
        return view_url + "formResponse"
    return view_url + "/formResponse"


def split_yyyy_mm_dd(data_yyyy_mm_dd: str):
    # espera "YYYY-MM-DD"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", data_yyyy_mm_dd.strip())
    if not m:
        raise ValueError(f"Data inválida (use YYYY-MM-DD): {data_yyyy_mm_dd}")
    return m.group(1), m.group(2), m.group(3)


def enviar_forms_http(dados: Dict[str, Union[str, List[str]]]) -> requests.Response:
    """
    dados esperados:
      nome, matricula, data (YYYY-MM-DD), agente, status, relatorio, link
      curso: str OU list[str] (checkbox)
      url: FORM_VIEW_URL (viewform)
    """
    url_view = str(dados.get("url") or FORM_VIEW_URL)
    url_post = view_to_form_response(url_view)

    y, mo, d = split_yyyy_mm_dd(str(dados["data"]))

    # monta payload base
    payload: Dict[str, Union[str, List[str]]] = {
        ENTRY_NOME: str(dados.get("nome", "")),
        ENTRY_MATRICULA: str(dados.get("matricula", "")),

        ENTRY_DATA_YEAR: y,
        ENTRY_DATA_MONTH: mo,
        ENTRY_DATA_DAY: d,

        ENTRY_AGENTE: str(dados.get("agente", "")),
        ENTRY_STATUS: str(dados.get("status", "")),

        ENTRY_RELATORIO: str(dados.get("relatorio", "")),
        ENTRY_LINK: str(dados.get("link", "")),
    }

    # checkbox: pode ser string ou lista
    curso_val = dados.get("curso", "Não consumiu")
    if isinstance(curso_val, list):
        payload[ENTRY_CURSO] = curso_val  # requests manda repetido: entry=op1&entry=op2
    else:
        payload[ENTRY_CURSO] = str(curso_val)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
        "Referer": url_view,
    }

    # não precisa cookies pra envio público (na maioria dos forms)
    # allow_redirects=False é ok, mas pode deixar True também
    resp = requests.post(url_post, data=payload, headers=headers, timeout=30, allow_redirects=False)
    return resp

