import unittest

from concertos.enriquecer import dados_de_no, eventos_jsonld, texto_visivel

PAGINA_JSONLD = """
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MusicEvent",
  "name": "Evanescence 2026 World Tour",
  "startDate": "2026-11-04T20:30:00+00:00",
  "location": {
    "@type": "Place",
    "name": "MEO Arena",
    "address": {"@type": "PostalAddress", "addressLocality": "Lisboa"}
  },
  "performer": [{"@type": "MusicGroup", "name": "Evanescence"}],
  "offers": {"@type": "Offer", "url": "https://bilhetes.exemplo/ev"},
  "image": ["https://cdn.exemplo/ev.jpg"]
}
</script>
</head><body></body></html>
"""

PAGINA_GRAFO = """
<script type='application/ld+json'>
{"@graph": [
  {"@type": "WebSite", "name": "Sala"},
  {"@type": ["TheaterEvent"], "name": "Turandot", "startDate": "2026-10-31"}
]}
</script>
"""

PAGINA_INVALIDA = """
<script type="application/ld+json">{isto não é json}</script>
<p>Concerto a 5 de dezembro de 2026, 21h30, no grande auditório.</p>
<script>var x = "3 de janeiro de 1999";</script>
"""


class TestJsonLd(unittest.TestCase):
    def test_extrai_evento_completo(self):
        nos = eventos_jsonld(PAGINA_JSONLD)
        self.assertEqual(len(nos), 1)
        dados = dados_de_no(nos[0])
        self.assertEqual(dados["data"], "2026-11-04")
        self.assertEqual(dados["hora"], "20:30")
        self.assertEqual(dados["sala"], "MEO Arena")
        self.assertEqual(dados["cidade"], "Lisboa")
        self.assertEqual(dados["artista"], "Evanescence")
        self.assertEqual(dados["bilhetes"], "https://bilhetes.exemplo/ev")
        self.assertEqual(dados["imagem"], "https://cdn.exemplo/ev.jpg")

    def test_grafo_e_tipo_em_lista(self):
        nos = eventos_jsonld(PAGINA_GRAFO)
        self.assertEqual(len(nos), 1)
        self.assertEqual(dados_de_no(nos[0])["data"], "2026-10-31")

    def test_json_invalido_nao_rebenta(self):
        self.assertEqual(eventos_jsonld(PAGINA_INVALIDA), [])


class TestTextoVisivel(unittest.TestCase):
    def test_ignora_scripts(self):
        texto = texto_visivel(PAGINA_INVALIDA)
        self.assertIn("5 de dezembro de 2026", texto)
        self.assertNotIn("1999", texto)


if __name__ == "__main__":
    unittest.main()
