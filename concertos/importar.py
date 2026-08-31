"""Importa o snapshot do monitor (eventos_oficiais_vistos.json) para o armazém.

Aceita um caminho local ou um URL (por exemplo o raw do GitHub do repositório
alertas-concertos-portugal). A importação é aditiva: eventos novos entram,
eventos conhecidos são atualizados e nada é apagado — o que desaparece do
snapshot fica marcado como inativo passado algum tempo.
"""

import json
from urllib.request import Request, urlopen

from . import modelo

URL_SNAPSHOT = (
    "https://raw.githubusercontent.com/daniel-asensio/"
    "alertas-concertos-portugal/main/eventos_oficiais_vistos.json"
)

# Entradas "Programação atualizada — ..." são avisos de alteração de página,
# não eventos; o id delas muda a cada alteração e só acumularia lixo.
_PREFIXO_AVISO = "Programação atualizada —"


def ler_snapshot(origem):
    if origem.startswith(("http://", "https://")):
        pedido = Request(origem, headers={"User-Agent": "ConcertosDesporto/1.0"})
        with urlopen(pedido, timeout=30) as resposta:
            return json.load(resposta)
    with open(origem, encoding="utf-8") as ficheiro:
        return json.load(ficheiro)


def importar(origem=URL_SNAPSHOT):
    snapshot = ler_snapshot(origem)
    eventos = modelo.carregar()
    novos, atualizados, ignorados = 0, 0, 0
    ids_presentes = set()
    for id_evento, bruto in snapshot.items():
        if bruto.get("title", "").startswith(_PREFIXO_AVISO):
            ignorados += 1
            continue
        ids_presentes.add(id_evento)
        if id_evento in eventos:
            modelo.atualizar_de_snapshot(eventos[id_evento], bruto)
            atualizados += 1
        else:
            eventos[id_evento] = modelo.novo_evento(bruto)
            novos += 1
    inativados = modelo.marcar_desaparecidos(eventos, ids_presentes)
    modelo.guardar(eventos)
    return {
        "novos": novos,
        "atualizados": atualizados,
        "ignorados": ignorados,
        "inativados": inativados,
        "total": len(eventos),
    }


def executar(argumentos):
    origem = argumentos.origem or URL_SNAPSHOT
    resultado = importar(origem)
    print(f"Importados: {resultado['novos']} novos, {resultado['atualizados']} atualizados, "
          f"{resultado['inativados']} passaram a inativos, {resultado['ignorados']} avisos ignorados.")
    print(f"Total no armazém: {resultado['total']} eventos.")
