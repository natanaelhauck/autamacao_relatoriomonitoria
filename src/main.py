"""
main.py
Orquestrador do projeto.

Fluxo:
- Lê monitorias do dia no Google Calendar
- Cruza com payloads do Read IA
- Envia registros para Google Forms via HTTP
"""

from datetime import date
from agenda import conectar_agenda, monitorias_do_dia
from read_ia import analisar_monitoria
from forms_http import enviar_forms_http
from curso import inferir_cursos_do_summary
from read_ia import debug_read_datas
from read_ia import PASTA_READ
print("📂 Pasta Read IA:", PASTA_READ)



def normalizar_agente(agente: str) -> str:
    a = (agente or "").strip().lower()
    if "natanael" in a:
        return "Natanael"
    if "douglas" in a:
        return "Douglas"
    if "pedro" in a:
        return "Pedro"
    if "alex" in a:
        return "Alex"
    # fallback (se vier certinho já)
    return (agente or "").strip()


def main():
    print("🔄 Iniciando automação de monitorias...\n")

    # Data de hoje (aceita yyyy-mm-dd no forms_http.py)
    data_execucao = date.today().strftime("%Y-%m-%d")
    print("📆 Data execução:", data_execucao)
    debug_read_datas()
    # 1) Conecta à agenda
    print("📅 Conectando ao Google Calendar...")
    service = conectar_agenda()

    # 2) Busca monitorias do dia
    monitorias = monitorias_do_dia(service)
    print(f"📌 Monitorias encontradas hoje: {len(monitorias)}\n")

    if not monitorias:
        print("⚠️ Nenhuma monitoria encontrada para hoje.")
        return

    # 3) Processa cada monitoria
    for idx, m in enumerate(monitorias, start=1):
        print(f"➡️ [{idx}/{len(monitorias)}] Processando aluno: {m['nome']}")

        # 3.1) Consulta Read IA (presença, relatório, link)
        read = analisar_monitoria(
            titulo_agenda=m['titulo'],
            meet_id_agenda=m.get('meet_id'),
            data_execucao=data_execucao
        )
        cursos = inferir_cursos_do_summary(read["relatorio"])
        status = read.get("presenca") or "Falta"
 
        # 3.2) Monta dados para o Forms
        dados_forms = {
            "nome": m["nome"],
            "matricula": m["matricula"],
            "data": data_execucao,
            "agente": normalizar_agente(m.get("agente")),
            "status": status,                   # "Presente" / "Falta"
            "relatorio": read.get("relatorio", ""),
            "link": read.get("link", ""),
            "curso":cursos,    # checkbox 
        }

        # 3.3) Envia para o Google Forms
        try:
            resp = enviar_forms_http(dados_forms)
            if resp.ok:
                print(f"   ✅ Enviado com sucesso ({resp.status_code})")
            else:
                print(f"   ❌ Erro ao enviar ({resp.status_code})")
                # se quiser, loga um pedacinho pra debug:
                # print("   ↳", resp.text_snippet)

        except Exception as e:
            print(f"   ❌ Falha ao enviar: {e}")

        print("-" * 50)

    print("\n🏁 Automação finalizada.")


if __name__ == "__main__":
    main()
   