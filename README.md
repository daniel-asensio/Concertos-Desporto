# Concertos & Desporto

Organizador de espetáculos em Portugal. Pega nos eventos recolhidos pelo
[monitor de alertas](https://github.com/daniel-asensio/alertas-concertos-portugal)
(que envia novidades por Telegram) e transforma-os numa base de consulta com
histórico, pesquisável por **data**, **local**, **cidade**, **artista** e
**categoria** — na linha de comandos ou num site estático.

Só usa a biblioteca standard do Python 3; não há dependências para instalar.

## Como funciona

```
alertas-concertos-portugal          este repositório
┌──────────────────────────┐   ┌─────────────────────────────────────────┐
│ monitoriza 21 fontes     │   │ importar   → dados/eventos.json         │
│ de hora a hora           │──▶│ enriquecer → datas, salas, artistas     │
│ (eventos_oficiais_vistos)│   │ site       → docs/index.html (consulta) │
└──────────────────────────┘   └─────────────────────────────────────────┘
```

Ao contrário do ficheiro do monitor (uma fotografia que é substituída a cada
execução), o armazém `dados/eventos.json` preserva histórico: cada evento tem
`primeira_vez`, `ultima_vez` e um estado `ativo`; nada é apagado quando
desaparece de uma agenda.

## Comandos

```bash
# Importar o snapshot do monitor (por omissão vai buscar o raw ao GitHub)
python -m concertos importar
python -m concertos importar caminho/para/eventos_oficiais_vistos.json

# Visitar as páginas dos eventos e extrair data, hora, sala, cidade,
# artista, link de bilhetes e imagem (JSON-LD → Open Graph → texto)
python -m concertos enriquecer --limite 60

# Consultar
python -m concertos consultar                        # resumo geral
python -m concertos consultar --artista "sigur"
python -m concertos consultar --cidade porto --mes 2026-10
python -m concertos consultar --categoria ópera --de 2026-09-01 --ate 2026-12-31
python -m concertos consultar --local "casa da música"
python -m concertos consultar --sem-data             # ainda sem data confirmada
python -m concertos consultar --texto turandot --json

# Gerar o site de consulta
python -m concertos site
```

As pesquisas ignoram maiúsculas e acentos ("opera" encontra "Ópera").

## Site de consulta

`docs/index.html` é um ficheiro único com filtros por texto, cidade, sala,
categoria e mês. Para o publicar: **Settings → Pages → Deploy from a branch**,
escolhendo o branch principal e a pasta `/docs`.

## Atualização automática

O workflow `.github/workflows/atualizar.yml` corre diariamente: importa o
snapshot mais recente do monitor, enriquece até 60 eventos por dia e
regenera o site, fazendo commit das alterações. Também pode ser lançado à
mão no separador Actions (workflow_dispatch).

Os eventos onde o enriquecimento falha 3 vezes deixam de ser tentados
(`--forcar` ignora esse limite).

## Estrutura

```
concertos/
├── __main__.py      # CLI: importar | enriquecer | consultar | site
├── modelo.py        # armazém dados/eventos.json (histórico e estado)
├── importar.py      # importação do snapshot do monitor
├── enriquecer.py    # JSON-LD / Open Graph / datas em texto
├── consultar.py     # filtros e listagem
├── site.py          # gerador do docs/index.html
├── fontes.py        # sala/cidade/distrito conhecidos de cada fonte
├── datas.py         # datas em português e ISO
├── heuristicas.py   # artista, títulos compostos, categoria
└── texto.py         # normalização (acentos, maiúsculas)
tests/               # python -m unittest discover -s tests
```

## Limitações conhecidas

- A deduplicação continua a ser por URL: o mesmo espetáculo visto em duas
  fontes (por exemplo, uma sala e a Agenda do Pedro) aparece duas vezes.
- A categoria e o artista são heurísticos e podem falhar em títulos ambíguos.
- Muitos eventos só ganham data depois de o enriquecimento correr — e há
  páginas sem dados estruturados onde a data não é extraível.
