"""Informação fixa sobre cada fonte do monitor: sala, cidade e distrito.

As fontes que são salas de espetáculos têm localização conhecida à partida;
as promotoras e agendas agregadoras não, e a localização desses eventos só
pode vir do enriquecimento das páginas.
"""

from .texto import chave

FONTES = {
    "Casa da Música": {"sala": "Casa da Música", "cidade": "Porto", "distrito": "Porto"},
    "Super Bock Arena": {"sala": "Super Bock Arena", "cidade": "Porto", "distrito": "Porto"},
    "Hard Club": {"sala": "Hard Club", "cidade": "Porto", "distrito": "Porto"},
    "Coliseu Porto Ageas": {"sala": "Coliseu Porto Ageas", "cidade": "Porto", "distrito": "Porto"},
    "Teatro Nacional São João": {"sala": "Teatro Nacional São João", "cidade": "Porto", "distrito": "Porto"},
    "Teatro Municipal do Porto": {"sala": "Teatro Municipal do Porto", "cidade": "Porto", "distrito": "Porto"},
    "Europarque": {"sala": "Europarque", "cidade": "Santa Maria da Feira", "distrito": "Aveiro"},
    "Teatro Aveirense": {"sala": "Teatro Aveirense", "cidade": "Aveiro", "distrito": "Aveiro"},
    "Cineteatro António Lamoso": {"sala": "Cineteatro António Lamoso", "cidade": "Santa Maria da Feira", "distrito": "Aveiro"},
    "Casa da Criatividade": {"sala": "Casa da Criatividade", "cidade": "São João da Madeira", "distrito": "Aveiro"},
    "MEO Arena": {"sala": "MEO Arena", "cidade": "Lisboa", "distrito": "Lisboa"},
    "Coliseu dos Recreios": {"sala": "Coliseu dos Recreios", "cidade": "Lisboa", "distrito": "Lisboa"},
    "Teatro Nacional de São Carlos": {"sala": "Teatro Nacional de São Carlos", "cidade": "Lisboa", "distrito": "Lisboa"},
    "Companhia Nacional de Bailado": {"sala": "Teatro Camões", "cidade": "Lisboa", "distrito": "Lisboa"},
    "Centro Cultural de Belém": {"sala": "Centro Cultural de Belém", "cidade": "Lisboa", "distrito": "Lisboa"},
    "Everything Is New": {"sala": None, "cidade": None, "distrito": None, "promotora": True},
    "PEV Entertainment": {"sala": None, "cidade": None, "distrito": None, "promotora": True},
    "House of Fun": {"sala": None, "cidade": None, "distrito": None, "promotora": True},
    "Música no Coração": {"sala": None, "cidade": None, "distrito": None, "promotora": True},
    "Agenda do Pedro": {"sala": None, "cidade": "Porto", "distrito": "Porto", "agregador": True},
    "BLITZ Agenda": {"sala": None, "cidade": None, "distrito": None, "agregador": True},
}

_POR_CHAVE = {chave(nome): info for nome, info in FONTES.items()}


def info_fonte(nome):
    """Localização conhecida da fonte; aceita nomes compostos como
    "Sigur Rós / Coliseu Porto Ageas" (eventos prioritários do monitor)."""
    exata = _POR_CHAVE.get(chave(nome))
    if exata:
        return exata
    nome_chave = chave(nome)
    for fonte_chave, info in _POR_CHAVE.items():
        if fonte_chave in nome_chave:
            return info
    return {"sala": None, "cidade": None, "distrito": None}
