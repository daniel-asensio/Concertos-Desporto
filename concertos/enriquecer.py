"""Enriquece eventos visitando a página de cada um e extraindo dados
estruturados: primeiro JSON-LD (schema.org Event, que muitas salas publicam),
depois metadados Open Graph e, por fim, datas em texto corrido.

Pensado para correr no GitHub Actions; falhas individuais não interrompem o
lote e cada evento guarda o número de tentativas para não insistir para
sempre em páginas que não têm dados.
"""

import json
import re
import time
from collections import Counter
from html.parser import HTMLParser
from urllib.request import Request, urlopen

from . import modelo
from .datas import de_iso_jsonld, extrair_data
from .texto import chave, limpar

AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ConcertosPortugal/2.0"
MAX_TENTATIVAS = 3
PAUSA_SEGUNDOS = 0.4

_RE_JSONLD = re.compile(
    r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.S | re.I,
)


def descarregar(url):
    pedido = Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "pt-PT,pt;q=0.9"})
    with urlopen(pedido, timeout=20) as resposta:
        return resposta.read().decode("utf-8", errors="replace")


def _achatar_jsonld(no):
    """Percorre um documento JSON-LD (incluindo listas e @graph) e devolve nós."""
    if isinstance(no, list):
        for item in no:
            yield from _achatar_jsonld(item)
    elif isinstance(no, dict):
        yield no
        for filho in (no.get("@graph"), no.get("itemListElement")):
            if filho:
                yield from _achatar_jsonld(filho)
        if isinstance(no.get("item"), dict):
            yield no["item"]


def eventos_jsonld(html_pagina):
    """Todos os nós schema.org com um tipo *Event encontrados na página."""
    resultados = []
    for bloco in _RE_JSONLD.findall(html_pagina):
        try:
            documento = json.loads(bloco.strip())
        except ValueError:
            continue
        for no in _achatar_jsonld(documento):
            tipos = no.get("@type") or []
            if isinstance(tipos, str):
                tipos = [tipos]
            if any("event" in str(t).casefold() for t in tipos):
                resultados.append(no)
    return resultados


def _primeiro(valor):
    if isinstance(valor, list):
        return valor[0] if valor else None
    return valor


def _nome(valor):
    valor = _primeiro(valor)
    if isinstance(valor, dict):
        return limpar(valor.get("name", ""))
    if isinstance(valor, str):
        return limpar(valor)
    return None


def dados_de_no(no):
    """Extrai os campos úteis de um nó schema.org Event."""
    dados = {}
    data, hora = de_iso_jsonld(no.get("startDate"))
    if data:
        dados["data"], dados["hora"] = data, hora
    local = _primeiro(no.get("location"))
    if isinstance(local, dict):
        if _nome(local.get("name") or local):
            dados["sala"] = _nome(local.get("name") or local)
        morada = local.get("address")
        if isinstance(morada, dict) and morada.get("addressLocality"):
            dados["cidade"] = limpar(str(morada["addressLocality"]))
        elif isinstance(morada, str) and morada.strip():
            dados["cidade"] = limpar(morada)
    elif isinstance(local, str) and local.strip():
        dados["sala"] = limpar(local)
    artista = _nome(no.get("performer"))
    if artista:
        dados["artista"] = artista
    ofertas = _primeiro(no.get("offers"))
    if isinstance(ofertas, dict) and ofertas.get("url"):
        dados["bilhetes"] = str(ofertas["url"])
    imagem = _primeiro(no.get("image"))
    if isinstance(imagem, dict):
        imagem = imagem.get("url")
    if isinstance(imagem, str) and imagem.startswith("http"):
        dados["imagem"] = imagem
    if _nome(no.get("name")):
        dados["titulo_ld"] = _nome(no.get("name"))
    return dados


class _TextoVisivel(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignorar, self.partes = 0, []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.ignorar += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.ignorar:
            self.ignorar -= 1

    def handle_data(self, dados):
        if not self.ignorar:
            valor = limpar(dados)
            if valor:
                self.partes.append(valor)


def texto_visivel(html_pagina):
    parser = _TextoVisivel()
    parser.feed(html_pagina)
    return " ".join(parser.partes)


def _escolher_no(nos, titulo):
    """Se a página tem vários eventos JSON-LD, tenta o que corresponde ao título."""
    if len(nos) == 1:
        return nos[0]
    titulo_chave = chave(titulo)
    for no in nos:
        nome = _nome(no.get("name"))
        if nome and (chave(nome) in titulo_chave or titulo_chave in chave(nome)):
            return no
    return None


def enriquecer_evento(evento, link_partilhado=False):
    """Preenche os campos em falta de um evento. Devolve os campos alterados."""
    html_pagina = descarregar(evento["link"])
    nos = eventos_jsonld(html_pagina)
    no = _escolher_no(nos, evento["titulo"])
    alterados = {}
    if no:
        dados = dados_de_no(no)
        for campo in ("data", "hora", "sala", "cidade", "artista", "bilhetes", "imagem"):
            if dados.get(campo) and not evento.get(campo):
                evento[campo] = dados[campo]
                alterados[campo] = dados[campo]
    # Recurso final para a data: procurar no texto da página. Só é seguro em
    # páginas dedicadas a um único evento; em páginas de agenda partilhadas
    # apanharia a data de outro espetáculo.
    if not evento.get("data") and not link_partilhado and not nos:
        data, hora = extrair_data(texto_visivel(html_pagina))
        if data:
            evento["data"], alterados["data"] = data, data
            if hora and not evento.get("hora"):
                evento["hora"], alterados["hora"] = hora, hora
    return alterados


def executar(argumentos):
    eventos = modelo.carregar()
    contagem_links = Counter(e["link"] for e in eventos.values())
    pendentes = [
        e for e in eventos.values()
        if e.get("ativo")
        and e.get("link", "").startswith("http")
        and (not e.get("data") or not e.get("sala"))
        and (not e.get("data") or e["data"] >= modelo.hoje())
        and e.get("tentativas_enriquecimento", 0) < (999 if argumentos.forcar else MAX_TENTATIVAS)
    ]
    # Primeiro os que nunca foram tentados.
    pendentes.sort(key=lambda e: (e.get("tentativas_enriquecimento", 0), e["id"]))
    if argumentos.limite:
        pendentes = pendentes[: argumentos.limite]

    melhorados, falhados = 0, 0
    for evento in pendentes:
        evento["tentativas_enriquecimento"] = evento.get("tentativas_enriquecimento", 0) + 1
        try:
            alterados = enriquecer_evento(evento, contagem_links[evento["link"]] > 1)
        except Exception as erro:
            falhados += 1
            print(f"  AVISO {evento['titulo'][:60]}: {type(erro).__name__}: {erro}")
        else:
            evento["enriquecido_em"] = modelo.hoje()
            if alterados:
                melhorados += 1
                resumo = ", ".join(f"{campo}={valor}" for campo, valor in alterados.items())
                print(f"  + {evento['titulo'][:60]}: {resumo[:120]}")
        time.sleep(PAUSA_SEGUNDOS)

    modelo.guardar(eventos)
    com_data = sum(1 for e in eventos.values() if e.get("data"))
    print(f"Processados {len(pendentes)} eventos: {melhorados} melhorados, {falhados} falharam.")
    print(f"Eventos com data no armazém: {com_data}/{len(eventos)}.")
