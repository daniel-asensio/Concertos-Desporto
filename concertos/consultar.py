"""Consulta dos espetáculos por data, local, cidade, artista, categoria ou texto."""

import json
from collections import Counter
from datetime import date

from . import modelo
from .texto import contem

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES_PT = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def filtrar(eventos, argumentos):
    resultado = []
    for evento in eventos.values():
        if not argumentos.todos and not evento.get("ativo"):
            continue
        if argumentos.artista and not (
            contem(evento.get("artista") or "", argumentos.artista)
            or contem(evento.get("titulo") or "", argumentos.artista)
        ):
            continue
        if argumentos.local and not (
            contem(evento.get("sala") or "", argumentos.local)
            or contem(evento.get("fonte") or "", argumentos.local)
        ):
            continue
        if argumentos.cidade and not contem(evento.get("cidade") or "", argumentos.cidade):
            continue
        if argumentos.categoria and not contem(evento.get("categoria") or "", argumentos.categoria):
            continue
        if argumentos.fonte and not contem(evento.get("fonte") or "", argumentos.fonte):
            continue
        if argumentos.texto and not any(
            contem(evento.get(campo) or "", argumentos.texto)
            for campo in ("titulo", "artista", "sala", "cidade", "fonte", "kind")
        ):
            continue
        data = evento.get("data")
        if argumentos.mes and (not data or not data.startswith(argumentos.mes)):
            continue
        if argumentos.de and (not data or data < argumentos.de):
            continue
        if argumentos.ate and (not data or data > argumentos.ate):
            continue
        if argumentos.sem_data and data:
            continue
        # Sem filtros de data explícitos, o que já passou fica fora da lista
        # (continua acessível com --passados, --todos ou um filtro de datas).
        esconder_passados = not (
            argumentos.passados or argumentos.todos
            or argumentos.de or argumentos.ate or argumentos.mes
        )
        if esconder_passados and data and data < date.today().isoformat():
            continue
        resultado.append(evento)
    return resultado


def _linha(evento):
    partes = []
    if evento.get("data"):
        dia = date.fromisoformat(evento["data"])
        quando = f"{DIAS_SEMANA[dia.weekday()]} {dia.day:2d} {MESES_PT[dia.month][:3]} {dia.year}"
        if evento.get("hora"):
            quando += f" {evento['hora']}"
        partes.append(f"📅 {quando}")
    elif evento.get("data_texto"):
        partes.append(f"📅 {evento['data_texto']}")
    onde = evento.get("sala") or evento.get("fonte")
    if evento.get("cidade") and evento.get("cidade") != onde:
        onde = f"{onde}, {evento['cidade']}"
    partes.append(f"📍 {onde}")
    if evento.get("categoria"):
        partes.append(evento["categoria"])
    linhas = [f"• {evento['titulo']}", "  " + " · ".join(partes), f"  {evento['link']}"]
    return "\n".join(linhas)


def _mostrar_lista(selecionados):
    com_data = sorted(
        (e for e in selecionados if e.get("data")),
        key=lambda e: (e["data"], e.get("hora") or "99"),
    )
    sem_data = sorted(
        (e for e in selecionados if not e.get("data")),
        key=lambda e: (e.get("fonte") or "", e["titulo"].casefold()),
    )
    mes_atual = None
    for evento in com_data:
        dia = date.fromisoformat(evento["data"])
        mes = f"{MESES_PT[dia.month]} {dia.year}"
        if mes != mes_atual:
            mes_atual = mes
            print(f"\n━━ {mes} ━━")
        print(_linha(evento))
    if sem_data:
        print(f"\n━━ sem data confirmada ({len(sem_data)}) ━━")
        for evento in sem_data:
            print(_linha(evento))
    print(f"\n{len(selecionados)} eventos ({len(com_data)} com data).")


def _mostrar_resumo(eventos):
    ativos = [e for e in eventos.values() if e.get("ativo")]
    com_data = [e for e in ativos if e.get("data")]
    print(f"Armazém: {len(eventos)} eventos, {len(ativos)} ativos, {len(com_data)} com data.")
    for rotulo, campo in (("Por cidade", "cidade"), ("Por categoria", "categoria")):
        contagem = Counter((e.get(campo) or "desconhecida") for e in ativos)
        linhas = ", ".join(f"{nome}: {total}" for nome, total in contagem.most_common(8))
        print(f"{rotulo}: {linhas}")
    proximos = sorted(
        (e for e in com_data if e["data"] >= date.today().isoformat()),
        key=lambda e: e["data"],
    )[:10]
    if proximos:
        print("\nPróximos eventos com data:")
        for evento in proximos:
            print(_linha(evento))
    print("\nUse filtros para listar: --artista, --local, --cidade, --mes 2026-09, "
          "--categoria, --texto, --sem-data. Detalhes: python -m concertos consultar --help")


def executar(argumentos):
    eventos = modelo.carregar()
    if not eventos:
        print("O armazém está vazio. Corra primeiro: python -m concertos importar")
        return
    tem_filtros = any(
        getattr(argumentos, nome)
        for nome in ("artista", "local", "cidade", "categoria", "fonte",
                     "texto", "mes", "de", "ate", "sem_data", "todos", "passados")
    )
    if not tem_filtros and not argumentos.json:
        _mostrar_resumo(eventos)
        return
    selecionados = filtrar(eventos, argumentos)
    if argumentos.json:
        print(json.dumps(selecionados, ensure_ascii=False, indent=2))
        return
    if not selecionados:
        print("Nenhum evento corresponde aos filtros.")
        return
    _mostrar_lista(selecionados)
