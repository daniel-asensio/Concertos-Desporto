# Arquivo Desportivo

Arquivo histórico e consultável do [Radar Desportivo](https://github.com/daniel-asensio/radar-desportivo).

O radar envia alertas para o Telegram mas só guarda uma janela de ~1 dia para
trás e 14 para a frente (`docs/events.json`). Este repositório resolve isso:
de hora a hora vai buscar esse snapshot, enriquece cada item e **acumula tudo
para sempre**, com um painel de consulta por:

- **data** (hoje, 7 dias, 30 dias, futuro, ou um intervalo à escolha);
- **local** (quando o item tem local, tipicamente eventos de federações);
- **atleta** (Pogačar, Pichardo, Queta, …);
- **clube / selecção** (Sporting CP, Portugal);
- **modalidade**, **competição**, **fonte**, tipo (notícia/evento) e pesquisa livre.

## Como funciona

```
radar-desportivo (30/30 min)          este repositório (de hora a hora)
┌────────────────────────┐            ┌─────────────────────────────────┐
│ fontes → score → alerta│            │ arquivo/harvest.py              │
│ docs/events.json ──────┼──────────▶ │  · funde no arquivo (nunca apaga)│
│ (janela de ~15 dias)   │            │  · enriquece: atletas, clubes,  │
└────────────────────────┘            │    competições, modalidade      │
                                      │ docs/dados/AAAA-MM.json + índice│
                                      │ docs/index.html (GitHub Pages)  │
                                      └─────────────────────────────────┘
```

- `arquivo/harvest.py` — recolhe o snapshot e funde-o no arquivo. Um item
  novo fica com `arquivado_em`; um item repetido é actualizado sem perder a
  data de arquivo. Notícias são também deduplicadas por URL (o fingerprint
  do radar muda se a data mudar).
- `arquivo/enrich.py` — extrai entidades com fronteiras de palavra (ao
  contrário do radar, "m**arco**u" já não conta como a modalidade "arco").
- `config/entidades.yaml` — atletas, clubes, competições e modalidades
  reconhecidos. Cresce à vontade; é a versão de consulta da watchlist do radar.
- `docs/dados/` — um ficheiro JSON por mês + `indice.json` com contagens.
- `docs/index.html` — o painel (estático, sem dependências, PT-PT,
  fuso Europe/Lisbon, estado dos filtros no URL para partilhar pesquisas).
- `.github/workflows/arquivo.yml` — corre `22 * * * *` (depois das passagens
  do radar aos minutos 7 e 37) e faz commit do que mudou.

## Configuração

Ver [COMEÇAR-AQUI.md](COMEÇAR-AQUI.md) — são três passos: um token de
leitura para o repositório do radar, activar o GitHub Pages e correr o
workflow uma vez.

## Uso local

```bash
pip install -r requirements.txt
python -m unittest discover -s tests        # testes
python -m arquivo.harvest --from-file ../radar-desportivo/docs/events.json
python -m http.server -d docs 8000          # abrir http://localhost:8000
```
