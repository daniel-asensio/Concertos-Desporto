import unittest

from concertos.heuristicas import classificar_categoria, extrair_artista


class TestArtista(unittest.TestCase):
    def test_separador_travessao(self):
        self.assertEqual(extrair_artista("Sigur Rós — The Orchestral Tour"), "Sigur Rós")

    def test_sufixo_tour(self):
        self.assertEqual(extrair_artista("Evanescence 2026 World Tour"), "Evanescence")

    def test_titulo_simples(self):
        self.assertEqual(extrair_artista("Rodrigo Leão"), "Rodrigo Leão")

    def test_generico_devolve_none(self):
        self.assertIsNone(extrair_artista("Agenda"))


class TestCategoria(unittest.TestCase):
    def test_opera_pelo_titulo(self):
        self.assertEqual(classificar_categoria("Ópera Turandot - Giacomo Puccini", "Aveiro"), "ópera")

    def test_ballet_pelo_kind(self):
        self.assertEqual(classificar_categoria("O Quebra-Nozes", "Ballet — Aveiro"), "ballet")

    def test_musica_por_omissao(self):
        self.assertEqual(classificar_categoria("Xutos & Pontapés", "Grande sala"), "música")



class TestTituloComposto(unittest.TestCase):
    def test_sao_carlos(self):
        from concertos.heuristicas import interpretar_titulo
        titulo, sala, data, hora = interpretar_titulo(
            "Centro Cultural Olga Cadaval 20 Set 2026 17:00 Concerto inaugural")
        self.assertEqual(titulo, "Concerto inaugural")
        self.assertEqual(sala, "Centro Cultural Olga Cadaval")
        self.assertEqual(data, "2026-09-20")
        self.assertEqual(hora, "17:00")

    def test_titulo_normal_fica_intacto(self):
        from concertos.heuristicas import interpretar_titulo
        titulo, sala, data, hora = interpretar_titulo("Sigur Rós — The Orchestral Tour")
        self.assertEqual(titulo, "Sigur Rós — The Orchestral Tour")
        self.assertIsNone(sala)
        self.assertIsNone(data)

    def test_data_solta_no_titulo(self):
        from concertos.heuristicas import interpretar_titulo
        titulo, sala, data, hora = interpretar_titulo("Concerto de Reis 6 de janeiro de 2027")
        self.assertEqual(data, "2027-01-06")
        self.assertIsNone(sala)



class TestDataNoInicio(unittest.TestCase):
    def test_cnb(self):
        from concertos.heuristicas import interpretar_titulo
        titulo, sala, data, hora = interpretar_titulo("26 Set 2026 21:30 Os Maias")
        self.assertEqual((titulo, sala, data, hora), ("Os Maias", None, "2026-09-26", "21:30"))


class TestArtistaPrefixo(unittest.TestCase):
    def test_prefixo_generico_nao_corta(self):
        from concertos.heuristicas import extrair_artista
        self.assertEqual(extrair_artista("Concerto inaugural"), "Concerto inaugural")

    def test_prefixo_com_nome_corta(self):
        from concertos.heuristicas import extrair_artista
        self.assertEqual(extrair_artista("Concerto de Rodrigo Leão"), "Rodrigo Leão")


if __name__ == "__main__":
    unittest.main()
