"""Heurísticas para extrair o artista, interpretar títulos compostos e
classificar a categoria de um evento."""

import re

from .datas import extrair_data
from .texto import chave, limpar

_SEPARADORES = re.compile(r"\s+(?:—|–|\|)\s+|\s+-\s+")
_RUIDO_ARTISTA = re.compile(
    r"\b(?:world tour|tour \d{4}|em concerto|ao vivo|live in [a-z ]+|digress[ãa]o"
    r"|apresenta|20\d\d)\b.*$",
    re.I,
)
_PREFIXOS = re.compile(r"^(?:concerto|espet[áa]culo|[óo]pera|ballet|bailado|festival)\s+(?:de\s+|com\s+)?", re.I)

_CATEGORIAS = [
    ("ópera", r"\b[óo]pera\b|\bturandot\b|\bpuccini\b|\bverdi\b|\bl[íi]rica\b"),
    ("ballet", r"\bballet\b|\bbailado\b|\bquebra-?nozes\b|\blago dos cisnes\b"),
    ("dança", r"\bdan[çc]a\b"),
    ("teatro", r"\bteatro\b|\bcom[ée]dia\b|\bstand[ -]?up\b"),
    ("clássica", r"\borquestra\b|\bsinf[óo]nic[ao]\b|\bcoro\b|\brecital\b|\bbarroca?\b|\bpiano\b"),
    ("festival", r"\bfestival\b|\bfest\b"),
    ("desporto", r"\bwrestling\b|\bboxe\b|\bpadel\b|\bfutsal\b|\bdesporto\b|\bgin[áa]stica\b"),
]


def extrair_artista(titulo):
    """Melhor palpite para o artista/grupo a partir do título do evento."""
    parte = _SEPARADORES.split(limpar(titulo), maxsplit=1)[0]
    parte = re.split(r'\s*[:(«"]\s*', parte, maxsplit=1)[0]
    parte = _RUIDO_ARTISTA.sub("", parte)
    sem_prefixo = _PREFIXOS.sub("", parte)
    # Só vale a pena tirar o prefixo se sobrar um nome próprio
    # ("Concerto de Rodrigo Leão" sim, "Concerto inaugural" não).
    if sem_prefixo != parte and sem_prefixo[:1].isupper():
        parte = sem_prefixo
    parte = limpar(parte).strip(" ,;:.")
    if len(parte) < 2 or len(parte) > 80 or not re.search(r"[a-zá-ú]", parte, re.I):
        return None
    if chave(parte) in {"agenda", "programacao", "eventos", "novidades"}:
        return None
    return parte


# Títulos no formato "«sala» «dia mês ano» [«hora»] «título»", usados por
# fontes como o Teatro Nacional de São Carlos.
_RE_COMPOSTO = re.compile(
    r"^(?P<sala>.{3,60}?)\s+(?P<data>\d{1,2}\s+[A-Za-zçãéÇ]+\.?\s+\d{4})"
    r"\s+(?P<hora>\d{1,2}:\d{2}\s+)?(?P<titulo>.{3,})$"
)
# Títulos que começam logo pela data, como os da Companhia Nacional de
# Bailado ("26 Set 2026 21:30 Os Maias").
_RE_DATA_INICIO = re.compile(
    r"^(?P<data>\d{1,2}\s+[A-Za-zçãéÇ]+\.?\s+\d{4})"
    r"\s+(?P<hora>\d{1,2}:\d{2}\s+)?(?P<titulo>.{3,})$"
)


def interpretar_titulo(titulo):
    """Separa um título composto em (título, sala, data, hora).

    Se o título não embutir sala e data, devolve-o intacto; se apenas contiver
    uma data reconhecível, aproveita-a.
    """
    titulo = limpar(titulo)
    encontrado = _RE_DATA_INICIO.match(titulo)
    if encontrado:
        data, _ = extrair_data(encontrado.group("data"))
        titulo_real = limpar(encontrado.group("titulo"))
        if data and re.search(r"[a-zá-ú]", titulo_real, re.I):
            hora = limpar(encontrado.group("hora") or "") or None
            return titulo_real, None, data, hora
    encontrado = _RE_COMPOSTO.match(titulo)
    if encontrado:
        data, _ = extrair_data(encontrado.group("data"))
        titulo_real = limpar(encontrado.group("titulo"))
        if data and re.search(r"[a-zá-ú]", titulo_real, re.I):
            hora = limpar(encontrado.group("hora") or "") or None
            return titulo_real, limpar(encontrado.group("sala")), data, hora
    data, hora = extrair_data(titulo)
    return titulo, None, data, hora


def classificar_categoria(titulo, kind):
    """Categoria simples com base no rótulo da fonte e em palavras do título."""
    referencia = f"{kind or ''} {titulo or ''}"
    for categoria, padrao in _CATEGORIAS:
        if re.search(padrao, referencia, re.I):
            return categoria
    return "música"
