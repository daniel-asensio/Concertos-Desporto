"""Armazém de eventos: um JSON versionado em git que, ao contrário do
ficheiro do monitor, preserva histórico (primeira/última observação, estado
ativo) e campos estruturados (data, hora, sala, cidade, artista, categoria).
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

from .datas import extrair_data
from .fontes import info_fonte
from .heuristicas import classificar_categoria, extrair_artista, interpretar_titulo

RAIZ = Path(__file__).resolve().parent.parent
FICHEIRO_EVENTOS = RAIZ / "dados" / "eventos.json"

# Ao fim de quantos dias sem aparecer no snapshot um evento é dado como inativo.
# Evita marcar como desaparecidos eventos de fontes que falham temporariamente.
DIAS_ATE_INATIVO = 14


def hoje():
    return date.today().isoformat()


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def carregar():
    if not FICHEIRO_EVENTOS.exists():
        return {}
    return json.loads(FICHEIRO_EVENTOS.read_text(encoding="utf-8"))


def guardar(eventos):
    FICHEIRO_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
    ordenados = dict(sorted(eventos.items()))
    FICHEIRO_EVENTOS.write_text(
        json.dumps(ordenados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def novo_evento(bruto):
    """Cria um registo estruturado a partir de um evento do monitor."""
    fonte = info_fonte(bruto.get("source", ""))
    data_texto = bruto.get("date")
    data_iso, hora = extrair_data(data_texto) if data_texto else (None, None)
    titulo_original = bruto.get("title", "")
    titulo, sala_embutida, data_titulo, hora_titulo = interpretar_titulo(titulo_original)
    if not data_iso and data_titulo:
        data_iso, hora = data_titulo, hora_titulo
    sala, cidade, distrito = fonte.get("sala"), fonte.get("cidade"), fonte.get("distrito")
    if sala_embutida and sala_embutida != sala:
        # O evento acontece noutra sala; a cidade da fonte deixa de ser fiável.
        sala, cidade, distrito = sala_embutida, None, None
    evento = {
        "id": bruto["id"],
        "titulo": titulo,
        "link": bruto.get("link"),
        "fonte": bruto.get("source"),
        "kind": bruto.get("kind"),
        "artista": extrair_artista(titulo),
        "categoria": classificar_categoria(titulo, bruto.get("kind")),
        "data": data_iso,
        "hora": hora,
        "data_texto": data_texto,
        "sala": sala,
        "cidade": cidade,
        "distrito": distrito,
        "bilhetes": None,
        "imagem": None,
        "primeira_vez": hoje(),
        "ultima_vez": hoje(),
        "ativo": True,
        "enriquecido_em": None,
        "tentativas_enriquecimento": 0,
    }
    if titulo != titulo_original:
        evento["titulo_original"] = titulo_original
    return evento


def atualizar_de_snapshot(evento, bruto):
    """Atualiza um registo existente com o que o snapshot traz de novo."""
    evento["ultima_vez"] = hoje()
    evento["ativo"] = True
    for campo, chave_bruto in (("link", "link"), ("kind", "kind")):
        if bruto.get(chave_bruto):
            evento[campo] = bruto[chave_bruto]
    titulo_bruto = bruto.get("title", "")
    if titulo_bruto and titulo_bruto not in (evento.get("titulo"), evento.get("titulo_original")):
        titulo, sala_embutida, data_titulo, hora_titulo = interpretar_titulo(titulo_bruto)
        evento["titulo"] = titulo
        if titulo != titulo_bruto:
            evento["titulo_original"] = titulo_bruto
        if data_titulo and not evento.get("data"):
            evento["data"], evento["hora"] = data_titulo, hora_titulo
        if sala_embutida and sala_embutida != evento.get("sala"):
            evento["sala"] = sala_embutida
    data_texto = bruto.get("date")
    if data_texto and data_texto != evento.get("data_texto"):
        evento["data_texto"] = data_texto
        data_iso, hora = extrair_data(data_texto)
        if data_iso:
            evento["data"] = data_iso
            evento["hora"] = hora or evento.get("hora")
    if not evento.get("artista"):
        evento["artista"] = extrair_artista(evento["titulo"])
    return evento


def marcar_desaparecidos(eventos, ids_presentes):
    """Passa a inativo o que já não aparece no snapshot há DIAS_ATE_INATIVO."""
    limite = (date.fromordinal(date.today().toordinal() - DIAS_ATE_INATIVO)).isoformat()
    alterados = 0
    for evento in eventos.values():
        if evento["id"] in ids_presentes or not evento.get("ativo"):
            continue
        if evento.get("ultima_vez", "") < limite:
            evento["ativo"] = False
            alterados += 1
    return alterados
