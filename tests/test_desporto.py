import unittest

from desporto.enrich import Entidades
from desporto.harvest import CONFIG_ENTIDADES, fundir, mes_do_item

AGORA = "2026-08-31T18:00:00+00:00"


def item(**campos) -> dict:
    base = {
        "title": "", "url": "https://exemplo.pt/x", "source": "Teste",
        "published": "2026-08-30T17:00:00+00:00", "summary": "", "sport": "geral",
        "kind": "news", "start": None, "end": None, "location": "",
        "score": 5, "reasons": [], "where_to_watch": [], "id": "aaaa",
    }
    base.update(campos)
    return base


class TestEnriquecimento(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entidades = Entidades.carregar(CONFIG_ENTIDADES)

    def test_atleta_por_alias_sem_acentos(self):
        enriquecido = self.entidades.enriquecer(item(title="Pogacar vence etapa da Vuelta a España"))
        self.assertIn("Tadej Pogačar", enriquecido["atletas"])
        self.assertIn("Vuelta a España", enriquecido["competicoes"])

    def test_fronteira_de_palavra(self):
        # "marcou" contém "arco" mas não pode contar como tiro com arco.
        enriquecido = self.entidades.enriquecer(item(title="Pedro Neto marcou um dos golos"))
        self.assertNotIn(enriquecido["modalidade"], ("arco", "tiro com arco"))

    def test_sporting_sem_confundir_com_braga(self):
        so_braga = self.entidades.enriquecer(item(title="Sporting de Braga vence na Europa"))
        self.assertNotIn("Sporting CP", so_braga["clubes"])
        jogo = self.entidades.enriquecer(item(title="Sporting bate SC Braga em Alvalade"))
        self.assertIn("Sporting CP", jogo["clubes"])

    def test_seleccao_portuguesa(self):
        enriquecido = self.entidades.enriquecer(item(title="Portugal termina em sétimo do medalheiro"))
        self.assertIn("Portugal (selecções)", enriquecido["clubes"])

    def test_modalidade_do_campo_sport(self):
        enriquecido = self.entidades.enriquecer(item(title="Nada a assinalar", sport="ciclismo"))
        self.assertEqual(enriquecido["modalidade"], "ciclismo")

    def test_modalidade_da_atleta(self):
        enriquecido = self.entidades.enriquecer(item(title="Patrícia Mamona em grande forma"))
        self.assertEqual(enriquecido["modalidade"], "atletismo")


class TestFusao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entidades = Entidades.carregar(CONFIG_ENTIDADES)

    def test_novo_e_reencontro(self):
        arquivo = {}
        novos, actualizados = fundir(arquivo, [item(id="aaaa")], self.entidades, AGORA)
        self.assertEqual((novos, actualizados), (1, 0))
        self.assertEqual(arquivo["aaaa"]["arquivado_em"], AGORA)

        # O mesmo item volta no snapshot seguinte: mantém a data de arquivo.
        novos, actualizados = fundir(arquivo, [item(id="aaaa")], self.entidades, "2026-09-01T00:00:00+00:00")
        self.assertEqual((novos, actualizados), (0, 0))
        self.assertEqual(arquivo["aaaa"]["arquivado_em"], AGORA)

    def test_noticia_com_id_novo_substitui_pela_url(self):
        arquivo = {}
        fundir(arquivo, [item(id="aaaa")], self.entidades, AGORA)
        # O fingerprint muda (dia diferente), mas o URL é o mesmo.
        fundir(arquivo, [item(id="bbbb", published="2026-08-31T09:00:00+00:00")],
               self.entidades, "2026-09-01T00:00:00+00:00")
        self.assertEqual(list(arquivo), ["bbbb"])
        self.assertEqual(arquivo["bbbb"]["arquivado_em"], AGORA)

    def test_mes_usa_data_do_evento(self):
        evento = item(kind="event", start="2026-09-12T10:00:00+00:00")
        self.assertEqual(mes_do_item(evento), "2026-09")
        self.assertEqual(mes_do_item(item()), "2026-08")


if __name__ == "__main__":
    unittest.main()
