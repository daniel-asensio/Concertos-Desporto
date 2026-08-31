"""Interpretação de datas em português e de datas ISO (JSON-LD)."""

import re

from .texto import chave

MESES = {
    "janeiro": 1, "jan": 1, "fevereiro": 2, "fev": 2, "marco": 3, "mar": 3,
    "abril": 4, "abr": 4, "maio": 5, "mai": 5, "junho": 6, "jun": 6,
    "julho": 7, "jul": 7, "agosto": 8, "ago": 8, "setembro": 9, "set": 9,
    "outubro": 10, "out": 10, "novembro": 11, "nov": 11, "dezembro": 12, "dez": 12,
}

_NOME_MES = r"[a-zçãé]+\.?"
# "13 setembro 2026", "13 de setembro de 2026", "11 e 12 setembro 2026"
_RE_EXTENSO = re.compile(
    rf"\b(\d{{1,2}})(?:\s*(?:,|e|a|até)\s*\d{{1,2}})?\s+(?:de\s+)?({_NOME_MES})\s+(?:de\s+)?(\d{{4}})",
    re.I,
)
# "31/10/2026", "31.10.2026", "31-10-2026"
_RE_NUMERICA = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b|\b(\d{1,2})-(\d{1,2})-(\d{4})\b")
_RE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_RE_HORA = re.compile(r"\b(\d{1,2})[h:](\d{2})?(?!\d)", re.I)


def _valida(ano, mes, dia):
    if 2000 <= ano <= 2100 and 1 <= mes <= 12 and 1 <= dia <= 31:
        return f"{ano:04d}-{mes:02d}-{dia:02d}"
    return None


def extrair_hora(texto):
    encontrado = _RE_HORA.search(texto or "")
    if not encontrado:
        return None
    hora = int(encontrado.group(1))
    minuto = int(encontrado.group(2) or 0)
    if 0 <= hora <= 23 and 0 <= minuto <= 59 and (hora, minuto) != (0, 0):
        return f"{hora:02d}:{minuto:02d}"
    return None


def extrair_data(texto):
    """Devolve (data_iso, hora) a partir de texto livre em português.

    Em intervalos ("11 e 12 setembro") devolve o primeiro dia.
    """
    texto = texto or ""
    encontrado = _RE_ISO.search(texto)
    if encontrado:
        data = _valida(int(encontrado.group(1)), int(encontrado.group(2)), int(encontrado.group(3)))
        if data:
            return data, extrair_hora(texto)
    encontrado = _RE_EXTENSO.search(texto)
    if encontrado:
        mes = MESES.get(chave(encontrado.group(2)).rstrip("."))
        if mes:
            data = _valida(int(encontrado.group(3)), mes, int(encontrado.group(1)))
            if data:
                return data, extrair_hora(texto)
    encontrado = _RE_NUMERICA.search(texto)
    if encontrado:
        grupos = [g for g in encontrado.groups() if g is not None]
        data = _valida(int(grupos[2]), int(grupos[1]), int(grupos[0]))
        if data:
            return data, extrair_hora(texto)
    return None, None


def de_iso_jsonld(valor):
    """Devolve (data_iso, hora) de um startDate JSON-LD ("2026-09-13T21:00:00+01:00")."""
    encontrado = re.match(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?", str(valor or ""))
    if not encontrado:
        return None, None
    data = _valida(int(encontrado.group(1)), int(encontrado.group(2)), int(encontrado.group(3)))
    if not data:
        return None, None
    hora = None
    if encontrado.group(4) and encontrado.group(4) + ":" + encontrado.group(5) != "00:00":
        hora = f"{encontrado.group(4)}:{encontrado.group(5)}"
    return data, hora
