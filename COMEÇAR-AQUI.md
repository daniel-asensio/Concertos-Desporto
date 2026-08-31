# Começar aqui

Três passos e o arquivo fica a funcionar sozinho.

## 1. Dar acesso ao radar (token de leitura)

O repositório `radar-desportivo` é privado, por isso o workflow precisa de um
token para ler o `docs/events.json`:

1. GitHub → foto de perfil → **Settings** → **Developer settings** →
   **Personal access tokens** → **Fine-grained tokens** → *Generate new token*;
2. Nome: `arquivo-desportivo`; validade: a mais longa que quiseres;
3. **Repository access** → *Only select repositories* → `radar-desportivo`;
4. **Permissions** → *Repository permissions* → **Contents: Read-only**;
5. Gera e copia o token;
6. Neste repositório (`Concertos-Desporto`) → **Settings** → **Secrets and
   variables** → **Actions** → *New repository secret*:
   - Nome: `RADAR_TOKEN`
   - Valor: o token copiado.

> Alternativa sem token: se o painel do radar estiver publicado no GitHub
> Pages, o `events.json` é público nesse URL. Nesse caso basta criar a
> *variable* (não secret) `RADAR_EVENTS_URL` com
> `https://daniel-asensio.github.io/radar-desportivo/events.json`.

## 2. Activar o GitHub Pages

Neste repositório → **Settings** → **Pages** → *Build and deployment*:

- **Source**: Deploy from a branch
- **Branch**: `main`, pasta `/docs`

O painel fica em `https://daniel-asensio.github.io/Concertos-Desporto/`.
Podes "instalá-lo" no telemóvel (Adicionar ao ecrã principal).

## 3. Primeira execução

Depois de fazer merge para `main`:

- **Actions** → **Arquivo Desportivo** → *Run workflow*.

A partir daí corre sozinho de hora a hora (minuto 22, logo a seguir às
passagens do radar) e faz commit apenas quando há novidades.

## Manutenção

- Novos atletas/clubes/competições: basta editar `config/entidades.yaml`.
  Na execução seguinte o arquivo inteiro é re-enriquecido, por isso as
  alterações aplicam-se também aos itens antigos.
- O arquivo nunca apaga nada; cada mês vive em `docs/dados/AAAA-MM.json`.
