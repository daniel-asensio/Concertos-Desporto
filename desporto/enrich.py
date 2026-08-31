"""Enriquecimento dos itens do radar com entidades para consulta.

Acrescenta a cada item os campos ``atletas``, ``clubes``, ``competicoes``,
``modalidade`` e ``local``, extraídos do texto com correspondência por
fronteiras de palavra (ao contrário do radar, "marcou" não conta como "arco").
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml


def normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", value.lower()).strip()


def _padrao(alias: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(normalise(alias)) + r"(?![a-z0-9])")


def _padroes(nomes: list[str]) -> list[re.Pattern]:
    return [_padrao(nome) for nome in nomes if nome]


class Entidades:
    def __init__(self, config: dict):
        self.atletas = [
            (a["nome"], a.get("modalidade", "geral"), _padroes([a["nome"], *a.get("alias", [])]))
            for a in config.get("atletas", [])
        ]
        self.clubes = [
            (c["nome"], _padroes([c["nome"], *c.get("alias", [])]), _padroes(c.get("ignorar_se", [])))
            for c in config.get("clubes", [])
        ]
        self.competicoes = [
            (c["nome"], _padroes([c["nome"], *c.get("alias", [])]))
            for c in config.get("competicoes", [])
        ]
        self.modalidades = [
            (nome, _padroes(alias)) for nome, alias in config.get("modalidades", {}).items()
        ]

    @classmethod
    def carregar(cls, caminho: Path) -> "Entidades":
        return cls(yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {})

    def enriquecer(self, item: dict) -> dict:
        texto = normalise(
            f"{item.get('title', '')} {item.get('summary', '')} {item.get('location', '')}"
        )

        item["atletas"] = [nome for nome, _, padroes in self.atletas
                           if any(p.search(texto) for p in padroes)]

        clubes = []
        for nome, padroes, ignorar in self.clubes:
            limpo = texto
            for p in ignorar:
                limpo = p.sub("§", limpo)
            if any(p.search(limpo) for p in padroes):
                clubes.append(nome)
        item["clubes"] = clubes

        item["competicoes"] = [nome for nome, padroes in self.competicoes
                               if any(p.search(texto) for p in padroes)]

        item["modalidade"] = self._modalidade(item, texto)
        item["local"] = (item.get("location") or "").strip()
        return item

    def _modalidade(self, item: dict, texto: str) -> str:
        sport = (item.get("sport") or "geral").strip().lower()
        if sport and sport != "geral":
            return sport
        das_atletas = {mod for nome, mod, _ in self.atletas if nome in item["atletas"]}
        if len(das_atletas) == 1:
            return das_atletas.pop()
        for nome, padroes in self.modalidades:
            if any(p.search(texto) for p in padroes):
                return nome
        return "geral"
