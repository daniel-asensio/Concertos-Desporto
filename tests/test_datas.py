import unittest

from concertos.datas import de_iso_jsonld, extrair_data


class TestExtrairData(unittest.TestCase):
    def test_extenso_com_hora(self):
        self.assertEqual(extrair_data("13 setembro 2026, 21h00"), ("2026-09-13", "21:00"))

    def test_extenso_com_de(self):
        self.assertEqual(extrair_data("31 de outubro de 2026, 21h30"), ("2026-10-31", "21:30"))

    def test_intervalo_devolve_primeiro_dia(self):
        self.assertEqual(extrair_data("11 e 12 setembro 2026"), ("2026-09-11", None))

    def test_sem_hora(self):
        self.assertEqual(extrair_data("17 janeiro 2027"), ("2027-01-17", None))

    def test_numerica(self):
        self.assertEqual(extrair_data("Estreia: 05/10/2026 às 19:30"), ("2026-10-05", "19:30"))

    def test_iso_no_texto(self):
        self.assertEqual(extrair_data("evento a 2026-11-02"), ("2026-11-02", None))

    def test_mes_abreviado(self):
        self.assertEqual(extrair_data("21 SET 2026"), ("2026-09-21", None))

    def test_sem_data(self):
        self.assertEqual(extrair_data("bilhetes já à venda"), (None, None))

    def test_data_invalida(self):
        self.assertEqual(extrair_data("45 setembro 2026"), (None, None))


class TestJsonLd(unittest.TestCase):
    def test_com_hora_e_fuso(self):
        self.assertEqual(de_iso_jsonld("2026-09-13T21:00:00+01:00"), ("2026-09-13", "21:00"))

    def test_so_data(self):
        self.assertEqual(de_iso_jsonld("2026-09-13"), ("2026-09-13", None))

    def test_meia_noite_sem_hora(self):
        self.assertEqual(de_iso_jsonld("2026-09-13T00:00:00"), ("2026-09-13", None))

    def test_invalido(self):
        self.assertEqual(de_iso_jsonld("brevemente"), (None, None))


if __name__ == "__main__":
    unittest.main()
