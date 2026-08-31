"""Gera docs/index.html: um site estático de consulta dos espetáculos,
publicado automaticamente no GitHub Pages pelo workflow "Atualizar
espetáculos" (job "publicar", via GitHub Actions)."""

import json
from datetime import date

from . import modelo

DESTINO = modelo.RAIZ / "docs" / "index.html"

MODELO_HTML = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Espetáculos em Portugal</title>
<style>
:root{
  --fundo:#faf8f4; --cartao:#ffffff; --tinta:#1d1c1a; --suave:#6d6a63;
  --linha:#e7e2d9; --realce:#8a4b26; --realce-suave:#f3e8df; --pill:#efece5;
}
@media (prefers-color-scheme: dark){:root{
  --fundo:#171614; --cartao:#201f1c; --tinta:#ece9e2; --suave:#a09c93;
  --linha:#33312c; --realce:#d99a6c; --realce-suave:#33261d; --pill:#2a2926;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
.envelope{max-width:880px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:8px 0 2px}
.sub{color:var(--suave);margin:0 0 18px;font-size:14px}
.filtros{position:sticky;top:0;background:var(--fundo);padding:10px 0 12px;z-index:5;
  display:flex;flex-wrap:wrap;gap:8px;border-bottom:1px solid var(--linha)}
.filtros input,.filtros select{background:var(--cartao);color:var(--tinta);
  border:1px solid var(--linha);border-radius:8px;padding:8px 10px;font:inherit;font-size:14px}
.filtros input{flex:1 1 200px;min-width:160px}
.filtros label{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--suave)}
.contagem{color:var(--suave);font-size:13px;margin:14px 0 4px}
.mes{font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--realce);margin:26px 0 8px;border-bottom:1px solid var(--linha);padding-bottom:4px}
.nav-irmao{margin:0 0 14px}
.nav-irmao a{color:var(--realce);text-decoration:none;font-size:13px;font-weight:600}
.nav-irmao a:hover{text-decoration:underline}
.evento{background:var(--cartao);border:1px solid var(--linha);border-radius:10px;
  padding:12px 14px;margin:8px 0}
.evento a{color:inherit;text-decoration:none}
.evento a:hover .titulo{color:var(--realce)}
.titulo{font-weight:600;margin-bottom:2px}
.detalhe{color:var(--suave);font-size:13px;display:flex;flex-wrap:wrap;gap:4px 14px}
.badge{display:inline-block;background:var(--pill);border-radius:20px;
  padding:1px 9px;font-size:12px}
.badge.data{background:var(--realce-suave);color:var(--realce);font-weight:600}
.vazio{color:var(--suave);text-align:center;padding:40px 0}
footer{margin-top:40px;color:var(--suave);font-size:12px;border-top:1px solid var(--linha);padding-top:12px}
</style>
</head>
<body>
<div class="envelope">
<h1>🎭 Espetáculos em Portugal</h1>
<p class="sub">__SUBTITULO__</p>
<p class="nav-irmao"><a href="desporto/">🏟️ Ver o Arquivo Desportivo →</a></p>
<div class="filtros">
  <input id="pesquisa" type="search" placeholder="Pesquisar artista, espetáculo, sala…">
  <select id="cidade"><option value="">Cidade</option></select>
  <select id="local"><option value="">Sala / fonte</option></select>
  <select id="categoria"><option value="">Categoria</option></select>
  <select id="mes"><option value="">Mês</option></select>
  <label><input id="so-com-data" type="checkbox"> só com data</label>
</div>
<div class="contagem" id="contagem"></div>
<div id="lista"></div>
<footer>Dados recolhidos automaticamente das agendas oficiais pelo
<a href="https://github.com/daniel-asensio/alertas-concertos-portugal">monitor de alertas</a>;
datas e locais podem mudar — confirme sempre no site da sala.</footer>
</div>
<script id="dados" type="application/json">__DADOS__</script>
<script>
const EVENTOS = JSON.parse(document.getElementById("dados").textContent);
const MESES = ["janeiro","fevereiro","março","abril","maio","junho",
  "julho","agosto","setembro","outubro","novembro","dezembro"];
const DIAS = ["dom","seg","ter","qua","qui","sex","sáb"];
const norm = t => (t||"").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"");
const $ = id => document.getElementById(id);

function opcoes(select, valores){
  [...new Set(valores.filter(Boolean))].sort((a,b)=>a.localeCompare(b,"pt"))
    .forEach(v => select.append(new Option(v, v)));
}
opcoes($("cidade"), EVENTOS.map(e => e.cidade));
opcoes($("local"), EVENTOS.map(e => e.sala || e.fonte));
opcoes($("categoria"), EVENTOS.map(e => e.categoria));
[...new Set(EVENTOS.filter(e=>e.data).map(e => e.data.slice(0,7)))].sort()
  .forEach(m => {
    const [ano, mes] = m.split("-");
    $("mes").append(new Option(`${MESES[+mes-1]} ${ano}`, m));
  });

function dataLegivel(e){
  if(!e.data) return e.data_texto || null;
  const d = new Date(e.data + "T12:00:00");
  let s = `${DIAS[d.getDay()]} ${d.getDate()} ${MESES[d.getMonth()].slice(0,3)} ${d.getFullYear()}`;
  if(e.hora) s += ` · ${e.hora}`;
  return s;
}

function cartao(e){
  const detalhes = [];
  const quando = dataLegivel(e);
  if(quando) detalhes.push(`<span class="badge data">${quando}</span>`);
  let onde = e.sala || e.fonte;
  if(e.cidade && e.cidade !== onde) onde += ", " + e.cidade;
  detalhes.push(`<span>📍 ${onde}</span>`);
  if(e.categoria) detalhes.push(`<span class="badge">${e.categoria}</span>`);
  if(e.artista && norm(e.artista) !== norm(e.titulo)) detalhes.push(`<span>🎤 ${e.artista}</span>`);
  return `<div class="evento"><a href="${e.link}" target="_blank" rel="noopener">
    <div class="titulo">${e.titulo}</div>
    <div class="detalhe">${detalhes.join("")}</div></a></div>`;
}

function atualizar(){
  const q = norm($("pesquisa").value);
  const fc = $("cidade").value, fl = $("local").value,
        fk = $("categoria").value, fm = $("mes").value,
        soData = $("so-com-data").checked;
  const vistos = EVENTOS.filter(e => {
    if(q && !norm([e.titulo, e.artista, e.sala, e.cidade, e.fonte].join(" ")).includes(q)) return false;
    if(fc && e.cidade !== fc) return false;
    if(fl && (e.sala || e.fonte) !== fl) return false;
    if(fk && e.categoria !== fk) return false;
    if(fm && (!e.data || !e.data.startsWith(fm))) return false;
    if(soData && !e.data) return false;
    return true;
  });
  const comData = vistos.filter(e => e.data)
    .sort((a,b) => (a.data + (a.hora||"")).localeCompare(b.data + (b.hora||"")));
  const semData = vistos.filter(e => !e.data)
    .sort((a,b) => a.titulo.localeCompare(b.titulo, "pt"));
  let html = "", mesAtual = "";
  for(const e of comData){
    const m = e.data.slice(0,7);
    if(m !== mesAtual){
      mesAtual = m;
      const [ano, mes] = m.split("-");
      html += `<div class="mes">${MESES[+mes-1]} ${ano}</div>`;
    }
    html += cartao(e);
  }
  if(semData.length && !soData){
    html += `<div class="mes">Sem data confirmada (${semData.length})</div>`;
    html += semData.map(cartao).join("");
  }
  $("lista").innerHTML = html || `<div class="vazio">Nenhum espetáculo corresponde aos filtros.</div>`;
  $("contagem").textContent =
    `${vistos.length} espetáculos · ${comData.length} com data confirmada`;
}
["pesquisa","cidade","local","categoria","mes","so-com-data"].forEach(id =>
  $(id).addEventListener(id === "pesquisa" ? "input" : "change", atualizar));
atualizar();
</script>
</body>
</html>
"""

CAMPOS_SITE = ("titulo", "link", "artista", "categoria", "data", "hora",
               "data_texto", "sala", "cidade", "fonte")


def executar(argumentos):
    eventos = modelo.carregar()
    ativos = [
        {campo: e.get(campo) for campo in CAMPOS_SITE}
        for e in sorted(eventos.values(), key=lambda e: e["id"])
        if e.get("ativo")
    ]
    com_data = sum(1 for e in ativos if e["data"])
    subtitulo = (f"{len(ativos)} espetáculos em cartaz · {com_data} com data confirmada · "
                 f"atualizado a {date.today().strftime('%d/%m/%Y')}")
    dados = json.dumps(ativos, ensure_ascii=False).replace("<", "\\u003c")
    pagina = MODELO_HTML.replace("__SUBTITULO__", subtitulo).replace("__DADOS__", dados)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(pagina, encoding="utf-8")
    print(f"Site gerado em {DESTINO} com {len(ativos)} eventos.")
