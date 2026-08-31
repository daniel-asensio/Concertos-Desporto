"""Recolhe o snapshot do Radar Desportivo e acumula-o no arquivo histórico.

O radar (repositório radar-desportivo) só guarda uma janela de ~1 dia para
trás e 14 para a frente em ``docs/events.json``. Este módulo vai lá buscar
esse snapshot com regularidade, enriquece cada item com atletas, clubes e
competições, e acumula tudo em ``docs/dados/`` — um ficheiro por mês, mais um
índice — sem nunca apagar itens antigos.

Ordem das fontes do snapshot:
  1. ``--from-file CAMINHO`` (testes e primeira carga local);
  2. variável ``RADAR_EVENTS_URL`` (por exemplo, o URL do GitHub Pages);
  3. API do GitHub com ``RADAR_TOKEN`` (repositório privado).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .enrich import Entidades

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "docs" / "dados"
CONFIG_ENTIDADES = RAIZ / "config" / "entidades.yaml"
API_SNAPSHOT = (
    "https://api.github.com/repos/daniel-asensio/radar-desportivo"
    "/contents/docs/events.json"
)


def obter_snapshot(from_file: str | None = None) -> list[dict]:
    if from_file:
        return json.loads(Path(from_file).read_text(encoding="utf-8"))
    url = os.environ.get("RADAR_EVENTS_URL")
    if url:
        pedido = urllib.request.Request(url)
    else:
        pedido = urllib.request.Request(
            API_SNAPSHOT, headers={"Accept": "application/vnd.github.raw+json"}
        )
        token = os.environ.get("RADAR_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit(
                "Sem acesso ao radar: define o secret RADAR_TOKEN "
                "(ou RADAR_EVENTS_URL, ou usa --from-file)."
            )
        pedido.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def mes_do_item(item: dict) -> str:
    return (item.get("start") or item["published"])[:7]


def carregar_arquivo(pasta: Path = PASTA_DADOS) -> dict[str, dict]:
    arquivo: dict[str, dict] = {}
    for ficheiro in sorted(pasta.glob("????-??.json")):
        for item in json.loads(ficheiro.read_text(encoding="utf-8")):
            arquivo[item["id"]] = item
    return arquivo


def fundir(arquivo: dict[str, dict], snapshot: list[dict],
           entidades: Entidades, agora: str) -> tuple[int, int]:
    """Junta o snapshot ao arquivo. Devolve (novos, actualizados)."""
    # O fingerprint do radar inclui o dia: se um evento ganhar data de início,
    # o id muda. Para notícias, o URL identifica o item de forma estável.
    por_url = {item["url"]: chave for chave, item in arquivo.items()
               if item.get("kind") == "news" and item.get("url")}
    novos = actualizados = 0
    for bruto in snapshot:
        item = entidades.enriquecer(dict(bruto))
        chave = item["id"]
        existente = arquivo.get(chave)
        if existente is None and item.get("kind") == "news":
            antiga = por_url.get(item.get("url", ""))
            if antiga and antiga != chave:
                existente = arquivo.pop(antiga)
        if existente is None:
            item["arquivado_em"] = agora
            arquivo[chave] = item
            novos += 1
        else:
            item["arquivado_em"] = existente.get("arquivado_em", agora)
            arquivo[chave] = item
            if item != existente:
                actualizados += 1
    return novos, actualizados


def _contar(indice: dict, campo: str, valores) -> None:
    contagem = indice.setdefault(campo, {})
    for valor in valores:
        if valor:
            contagem[valor] = contagem.get(valor, 0) + 1


def gravar(arquivo: dict[str, dict], agora: str, pasta: Path = PASTA_DADOS) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    meses: dict[str, list[dict]] = {}
    for item in arquivo.values():
        meses.setdefault(mes_do_item(item), []).append(item)

    indice: dict = {"actualizado": agora, "total": len(arquivo), "meses": {}}
    for mes, itens in sorted(meses.items()):
        itens.sort(key=lambda x: (x.get("start") or x["published"], x["id"]))
        destino = pasta / f"{mes}.json"
        conteudo = json.dumps(itens, ensure_ascii=False, indent=1) + "\n"
        if not destino.exists() or destino.read_text(encoding="utf-8") != conteudo:
            destino.write_text(conteudo, encoding="utf-8")
        indice["meses"][mes] = len(itens)

    for item in arquivo.values():
        _contar(indice, "atletas", item.get("atletas", []))
        _contar(indice, "clubes", item.get("clubes", []))
        _contar(indice, "competicoes", item.get("competicoes", []))
        _contar(indice, "modalidades", [item.get("modalidade", "geral")])
        _contar(indice, "fontes", [item.get("source", "")])
        _contar(indice, "locais", [item.get("local", "")])
    for campo in ("atletas", "clubes", "competicoes", "modalidades", "fontes", "locais"):
        indice[campo] = dict(sorted(indice.get(campo, {}).items(),
                                    key=lambda par: (-par[1], par[0])))

    (pasta / "indice.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-file", help="ler o snapshot de um ficheiro local")
    argumentos = parser.parse_args(argv)

    entidades = Entidades.carregar(CONFIG_ENTIDADES)
    snapshot = obter_snapshot(argumentos.from_file)
    arquivo = carregar_arquivo()
    # Re-enriquecer o arquivo inteiro: alterações ao entidades.yaml
    # aplicam-se assim também aos itens antigos.
    for chave, item in arquivo.items():
        arquivo[chave] = entidades.enriquecer(item)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    novos, actualizados = fundir(arquivo, snapshot, entidades, agora)
    gravar(arquivo, agora)
    print(f"Snapshot com {len(snapshot)} itens: "
          f"{novos} novos, {actualizados} actualizados, {len(arquivo)} no arquivo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
