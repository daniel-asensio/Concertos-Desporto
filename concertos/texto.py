"""Utilidades de normalização de texto."""

import html
import re
import unicodedata


def limpar(valor):
    valor = re.sub(r"<[^>]+>", " ", valor or "")
    return re.sub(r"\s+", " ", html.unescape(valor)).strip(" -|\t\r\n")


def sem_acentos(texto):
    decomposto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def chave(texto):
    """Forma canónica para comparações: minúsculas, sem acentos, espaços únicos."""
    return re.sub(r"\s+", " ", sem_acentos((texto or "").casefold())).strip()


def contem(texto, procurado):
    """Pesquisa por substring insensível a maiúsculas e acentos."""
    return chave(procurado) in chave(texto)
