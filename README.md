# Concertos & Desporto

Duas apps deste repositório partilham o mesmo objetivo: pegar em alertas que
chegam ao Telegram (via monitores separados) e transformá-los numa base de
consulta com histórico, pesquisável por data, local e outras entidades — em
vez de deixar os alertas perderem-se depois de lidos.

- **[Concertos](#concertos)** — espetáculos em Portugal, a partir do
  [monitor de alertas](https://github.com/daniel-asensio/alertas-concertos-portugal).
- **[Desporto](#desporto)** — o arquivo do [Radar Desportivo](https://github.com/daniel-asensio/radar-desportivo).

Ambas publicam o seu site em <https://daniel-asensio.github.io/Concertos-Desporto/>
(concertos na raiz, desporto em `/desporto/`), com um link de um site para o outro.

---

## Concertos

Organizador de espetáculos em Portugal. Pega nos eventos recolhidos pelo
[monitor de alertas](https://github.com/daniel-asensio/alertas-concertos-portugal)
(que envia novidades por Telegram) e transforma-os numa base de consulta com
histórico, pesquisável por **data**, **local**, **cidade**, **artista** e
**categoria** — na linha de comandos ou num site estático.

Só usa a biblioteca standard do Python 3; não há dependências para instalar.

### Como funciona

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

### Comandos

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

### Atualização automática

O workflow `.github/workflows/atualizar.yml` corre diariamente: importa o
snapshot mais recente do monitor, enriquece até 60 eventos por dia e
regenera o site, fazendo commit das alterações. Também pode ser lançado à
mão no separador Actions (workflow_dispatch).

Os eventos onde o enriquecimento falha 3 vezes deixam de ser tentados
(`--forcar` ignora esse limite).

### Estrutura

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
```

### Limitações conhecidas

- A deduplicação continua a ser por URL: o mesmo espetáculo visto em duas
  fontes (por exemplo, uma sala e a Agenda do Pedro) aparece duas vezes.
- A categoria e o artista são heurísticos e podem falhar em títulos ambíguos.
- Muitos eventos só ganham data depois de o enriquecimento correr — e há
  páginas sem dados estruturados onde a data não é extraível.

---

## Desporto

Arquivo histórico e consultável do [Radar Desportivo](https://github.com/daniel-asensio/radar-desportivo).

O radar envia alertas para o Telegram mas só guarda uma janela de ~1 dia para
trás e 14 para a frente (`docs/events.json` do radar). Este repositório
resolve isso: de hora a hora vai buscar esse snapshot, enriquece cada item e
**acumula tudo para sempre**, com um painel de consulta por:

- **data** (hoje, 7 dias, 30 dias, futuro, ou um intervalo à escolha);
- **local** (quando o item tem local, tipicamente eventos de federações);
- **atleta** (Pogačar, Pichardo, Queta, …);
- **clube / seleção** (Sporting CP, Portugal);
- **modalidade**, **competição**, **fonte**, tipo (notícia/evento) e pesquisa livre.

Usa uma dependência (`PyYAML`) para o ficheiro de configuração das entidades —
diferente da filosofia "só standard library" dos concertos, porque a lista de
atletas/clubes/competições é grande e a legibilidade do YAML compensa.

### Como funciona

```
radar-desportivo (30/30 min)          este repositório (de hora a hora)
┌────────────────────────┐            ┌──────────────────────────────────┐
│ fontes → score → alerta│            │ desporto/harvest.py              │
│ docs/events.json ──────┼──────────▶ │  · funde no arquivo (nunca apaga)│
│ (janela de ~15 dias)   │            │  · enriquece: atletas, clubes,   │
└────────────────────────┘            │    competições, modalidade       │
                                       │ docs/desporto/dados/AAAA-MM.json │
                                       │ + índice                         │
                                       │ docs/desporto/index.html         │
                                       └───────────────────────────────────┘
```

- `desporto/harvest.py` — recolhe o snapshot e funde-o no arquivo. Um item
  novo fica com `arquivado_em`; um item repetido é atualizado sem perder a
  data de arquivo. Notícias são também deduplicadas por URL (o fingerprint
  do radar muda se a data mudar). O arquivo inteiro é re-enriquecido a cada
  execução, por isso alterações a `config/entidades.yaml` aplicam-se também
  aos itens antigos.
- `desporto/enrich.py` — extrai entidades com fronteiras de palavra (ao
  contrário do radar, "m**arco**u" já não conta como a modalidade "arco").
- `config/entidades.yaml` — atletas, clubes, competições e modalidades
  reconhecidos. Cresce à vontade; é a versão de consulta da watchlist do radar.
- `docs/desporto/dados/` — um ficheiro JSON por mês + `indice.json` com contagens.
- `docs/desporto/index.html` — o painel (estático, sem dependências no
  browser, PT-PT, fuso Europe/Lisbon, estado dos filtros no URL para
  partilhar pesquisas).
- `.github/workflows/desporto.yml` — corre `22 * * * *` (depois das
  passagens do radar aos minutos 7 e 37), faz commit do que mudou e publica
  no GitHub Pages.

### Configuração

Ver [COMEÇAR-AQUI.md](COMEÇAR-AQUI.md) — resume-se a dar ao workflow acesso
de leitura ao repositório privado `radar-desportivo` (um secret) e correr o
workflow uma vez.

### Uso local

```bash
pip install -r requirements.txt
python -m unittest discover -s tests        # testes (concertos + desporto)
python -m desporto.harvest --from-file ../radar-desportivo/docs/events.json
python -m http.server -d docs 8000          # abrir http://localhost:8000/desporto/
```
