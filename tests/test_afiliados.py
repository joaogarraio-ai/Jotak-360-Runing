import unittest

from afiliados_ml.db import conectar, resumo
from afiliados_ml.importar import importar_csv, numero
from afiliados_ml.web import render


CSV = """Data da venda;Produto;Valor da venda;Comissão;Status
10/09/2026;Fone Bluetooth;R$ 1.200,00;R$ 96,00;Paga
11/09/2026;Mouse;R$ 80,00;R$ 6,40;Pendente
12/09/2026;Cabo;R$ 30,00;R$ 2,00;Cancelada
"""


class T(unittest.TestCase):
    def setUp(self):
        self.con = conectar(":memory:")

    def test_numero(self):
        self.assertEqual(numero("R$ 1.234,56"), 1234.56)
        self.assertEqual(numero("12,5"), 12.5)

    def test_importa_e_nao_duplica(self):
        self.assertEqual(importar_csv(self.con, CSV), (3, 0))
        self.assertEqual(importar_csv(self.con, CSV), (0, 3))

    def test_resumo_ignora_canceladas(self):
        importar_csv(self.con, CSV)
        meses, _, a_receber = resumo(self.con)
        self.assertAlmostEqual(meses[0]["comissao"], 102.40)
        self.assertAlmostEqual(a_receber, 6.40)

    def test_colunas_faltando(self):
        with self.assertRaises(ValueError):
            importar_csv(self.con, "foo;bar\n1;2\n")

    def test_paginas_renderizam(self):
        importar_csv(self.con, CSV)
        for p in ("/", "/links", "/vendas", "/importar"):
            self.assertIn("Afiliado", render(self.con, p))


if __name__ == "__main__":
    unittest.main()
