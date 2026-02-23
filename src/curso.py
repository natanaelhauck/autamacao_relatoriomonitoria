from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

CURSOS = [
    "Scratch",
    "No Code",
    "Introdução à Web",
    "Linux",
    "Python I",
    "JavaScript",
    "Banco de Dados",
    "Programação Orientada a Objetos",
    "Python II",
    "Fundamentos de interface",
    "React JS",
    "Desenvolvimento de websites com mentalidade ágil",
    "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "Programação Multiplataforma com React Native",
    "Programação Multiplataforma com Flutter",
    "Padrão de Projeto de Software",
    "Desenvolvimento de APIs RESTful",
    "Desenvolvimento Nativo para Android",
    "Banco de Dados não relacional",
    "Framework Full Stack para Web",
    "Teste de Software para Web",
    "Teste de Software para Mobile",
    "Não consumiu",
]

ALIAS = {
    # Front-end / frameworks
    "framework front end": "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "framework frontend": "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "frameworks front end": "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "front end frameworks": "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "web frameworks front end": "Desenvolvimento de Interfaces Web Frameworks Front-End",
    "framework front-end": "Desenvolvimento de Interfaces Web Frameworks Front-End",

    # React
    "react": "React JS",
    "reactjs": "React JS",
    "react com javascript": "React JS",

    # APIs
    "api": "Desenvolvimento de APIs RESTful",
    "apis": "Desenvolvimento de APIs RESTful",
    "api rest": "Desenvolvimento de APIs RESTful",
    "rest": "Desenvolvimento de APIs RESTful",
    "restful": "Desenvolvimento de APIs RESTful",

    # Banco
    "banco de dados": "Banco de Dados",
    "sql": "Banco de Dados",
    "nosql": "Banco de Dados não relacional",
    "nao relacional": "Banco de Dados não relacional",
    "não relacional": "Banco de Dados não relacional",

    # POO
    "poo": "Programação Orientada a Objetos",
    "orientado a objetos": "Programação Orientada a Objetos",

    # Web / Intro
    "introducao web": "Introdução à Web",
    "introducao a web": "Introdução à Web",
    "introdução web": "Introdução à Web",
    "introdução à web": "Introdução à Web",
    "html": "Introdução à Web",
    "css": "Introdução à Web",

    # Outros
    "android": "Desenvolvimento Nativo para Android",
    "react native": "Programação Multiplataforma com React Native",
    "flutter": "Programação Multiplataforma com Flutter",
    "padrao de projeto": "Padrão de Projeto de Software",
    "padroes de projeto": "Padrão de Projeto de Software",
    "padrões de projeto": "Padrão de Projeto de Software",
    "testes web": "Teste de Software para Web",
    "teste web": "Teste de Software para Web",
    "testes mobile": "Teste de Software para Mobile",
    "teste mobile": "Teste de Software para Mobile",

    # Python (muito citado)
    "python": "Python I",
    "python 1": "Python I",
    "python i": "Python I",
    "python 2": "Python II",
    "python ii": "Python II",
    "python basico": "Python I",
    "python básico": "Python I",
    "python intermediario": "Python II",
    "python intermediário": "Python II",
}

STOPWORDS = {
    "curso", "cursos", "modulo", "módulo", "aula", "aulas",
    "lição", "licao", "atividade", "atividades",
    "meta", "semanal", "semana", "conteudo", "conteúdo",
}

# Gatihos de "META PASSADA / CONSUMO"
CONCLUSAO_PATTERNS = [
    r"\bconcluiu\b",
    r"\bconcluiu a meta\b",
    r"\bcumpriu\b",
    r"\bcumpriu a meta\b",
    r"\bfez a meta\b",
    r"\bfez\b",
    r"\bfinalizou\b",
    r"\bterminou\b",
    r"\bentregou\b",
    r"\benviou\b",
    r"\bmandou\b",
    r"\bcompletou\b",
    r"\bconseguiu\b",
    r"\bdeu conta\b",
    r"\brealizou\b",
    r"\bseguiu\b",
    r"\bviu\b",
    r"\bassistiu\b",
    r"\bconsumiu\b",
    r"\bmeta da semana passada\b",
    r"\bsemana passada\b",
    r"\bpergunta(?:ou)? se\b.*\bmeta\b",  # "questionou se cumpriu a meta"
    r"\bquestion(?:ou)?\b.*\bmeta\b",
    r"\bpergunt(?:ou)?\b.*\bmeta\b",
]

# Gatilhos de "META FUTURA / NÃO MARCAR"
FUTURO_PATTERNS = [
    r"\bsemana que vem\b",
    r"\bproxima semana\b",
    r"\bpr[oó]xima semana\b",
    r"\bmeta pra semana que vem\b",
    r"\bmeta para semana que vem\b",
    r"\bmeta da proxima semana\b",
    r"\bmeta da pr[oó]xima semana\b",
    r"\bpara a proxima semana\b",
    r"\bpara a pr[oó]xima semana\b",
    r"\bcomo meta\b.*\bsemana que vem\b",
    r"\bcomo meta\b.*\bproxima semana\b",
    r"\bvai (?:ver|fazer|assistir|consumir|iniciar|comecar|começar)\b",
    r"\bdeve (?:ver|fazer|assistir|consumir|iniciar|comecar|começar)\b",
    r"\bprecisa (?:ver|fazer|assistir|consumir|iniciar|comecar|começar)\b",
]

# Regex útil: "módulo 6 de python", "modulo 2 python"
MOD_PY_RE = re.compile(r"\bmodul[oa]\s*(\d+)\s*(?:de\s*)?python\b", re.I)

def _norm(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[.\n;:!?]+", text)
    return [p.strip() for p in parts if p.strip()]

def _tem_padrao(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text) for p in patterns)

def _limpar_stopwords(text: str) -> str:
    t = " " + text + " "
    for w in sorted(STOPWORDS, key=len, reverse=True):
        t = re.sub(rf"\b{re.escape(_norm(w))}\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def _extrair_cursos_no_texto(text_norm: str) -> set[str]:
    achados: set[str] = set()

    # 0) Heurística: módulo X de Python -> Python I/II
    m = MOD_PY_RE.search(text_norm)
    if m:
        mod = int(m.group(1))
        # ajuste se você quiser outra regra; aqui: 1-6 => Python I, 7+ => Python II
        achados.add("Python I" if mod <= 6 else "Python II")

    # 1) alias (frases curtas)
    for apelido, curso in ALIAS.items():
        if _norm(apelido) in text_norm:
            achados.add(curso)

    # 2) nome do curso direto (com normalização)
    for curso in CURSOS:
        if curso == "Não consumiu":
            continue
        c = _norm(curso)
        if c and c in text_norm:
            achados.add(curso)

    return achados

def _score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def _fuzzy_um_curso(text_norm: str, limiar: float = 0.78) -> str | None:
    """
    Fallback: tenta escolher 1 curso se o texto estiver "perto" de um nome.
    Usa limiar alto pra evitar falso positivo.
    """
    best = None
    best_sc = 0.0
    for curso in CURSOS:
        if curso == "Não consumiu":
            continue
        sc = _score(text_norm, _norm(curso))
        if sc > best_sc:
            best_sc = sc
            best = curso
    if best and best_sc >= limiar:
        return best
    return None

def inferir_cursos_do_summary(summary: str) -> list[str]:
    """
    Marca o curso como "Visto no Ava" somente quando:
    - aparece em contexto de meta passada / consumo / conclusão (ou pergunta sobre conclusão)
    - e NÃO aparece apenas como meta futura

    Implementação:
    - varre frases
    - quando encontra gatilho de CONCLUSAO, abre uma janela (frase atual + próximas 2)
    - quando encontra gatilho de FUTURO, abre janela (frase atual + próximas 2) e bloqueia cursos dali
    - resultado final = (cursos_conclusao) - (cursos_apenas_futuro)
    """
    full = _norm(summary)
    frases = _split_sentences(full)

    cursos_concluidos: set[str] = set()
    cursos_futuros: set[str] = set()

    # janela de contexto (quantas frases depois “contam”)
    JANELA = 2

    for i, f in enumerate(frases):
        f_clean = _limpar_stopwords(f)

        is_conc = _tem_padrao(f_clean, CONCLUSAO_PATTERNS)
        is_fut = _tem_padrao(f_clean, FUTURO_PATTERNS)

        if not (is_conc or is_fut):
            continue

        # monta trecho da janela: frase atual + próximas JANELA
        trecho = " ".join(frases[i : i + 1 + JANELA])
        trecho = _limpar_stopwords(trecho)

        achados = _extrair_cursos_no_texto(trecho)

        # fallback fuzzy só se não achou nada e tem palavras-chave (evita marcar à toa)
        if not achados:
            possivel = _fuzzy_um_curso(trecho)
            if possivel:
                achados.add(possivel)

        if is_conc:
            cursos_concluidos |= achados
        elif is_fut:
            cursos_futuros |= achados

    # marca somente o que foi concluído / consumido (mesmo que também apareça em futuro)
    cursos_final = set(cursos_concluidos)
    cursos_final.discard("Não consumiu")

    if not cursos_final:
        return ["Não consumiu"]

    return sorted(cursos_final)


