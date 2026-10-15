import unittest

from afiliados_ml import alertas, comissao, ml_api, posts
from afiliados_ml.db import conectar

ITEM = {"id": "MLB123", "title": "Organizador de Gaveta", "price": 40.0, "original_price": 50.0,
        "permalink": "https://produto.mercadolivre.com.br/MLB-123-x", "category_id": "C1",
        "sold_quantity": 300, "shipping": {"free_shipping": True}}


def fake(preco):
    def get(caminho, params=None):
        if caminho.startswith("/items/"):
            return {**ITEM, "price": preco}
        if caminho.startswith("/categories/"):
            return {"path_from_root": [{"name": "Casa, Móveis e Decoração"}]}
        return {"results": [ITEM]}
    return get


class T(unittest.TestCase):
    def test_busca_e_categoria(self):
        p = ml_api.buscar("x", get=fake(40))[0]
        self.assertEqual((p.id, p.vendidos, p.desconto, p.frete_gratis), ("MLB123", 300, 20, True))
        self.assertEqual(ml_api.categoria_raiz("C1", fake(40)), "Casa, Móveis e Decoração")

    def test_extrair_id(self):
        self.assertEqual(ml_api.extrair_id("https://x.com/MLB-3456789-foo"), "MLB3456789")
        with self.assertRaises(ValueError):
            ml_api.extrair_id("sem codigo")

    def test_comissao(self):
        self.assertEqual(comissao.taxa("Beleza e Cuidado Pessoal"), (0.16, 0.08))
        self.assertEqual(comissao.taxa("Alimentos e Bebidas"), (0.0, 0.0))
        self.assertEqual(comissao.taxa("Celulares e Telefones"), (0.05, 0.025))
        self.assertEqual(comissao.estimar(100, "Casa, Móveis e Decoração"), (12.0, 6.0))

    def test_posts(self):
        p = ml_api.buscar("x", get=fake(40))[0]
        w = posts.gerar(p, "https://meu.link", "whatsapp")
        self.assertIn("R$ 40,00", w); self.assertIn("20% OFF", w); self.assertIn("https://meu.link", w)
        self.assertIn("#publi", posts.gerar(p, "l", "instagram"))
        self.assertIn("ROTEIRO", posts.gerar(p, "l", "tiktok"))

    def test_alertas(self):
        con = conectar(":memory:")
        alertas.adicionar(con, "MLB-123", 30, fake(40))
        self.assertEqual(alertas.checar(con, fake(40)), [])        # sem mudança
        self.assertEqual(len(alertas.checar(con, fake(35))), 1)    # caiu
        self.assertEqual(alertas.checar(con, fake(35)), [])        # já avisado
        self.assertEqual(len(alertas.checar(con, fake(29))), 1)    # bateu o alvo


if __name__ == "__main__":
    unittest.main()


class TelegramT(unittest.TestCase):
    def test_envio_e_divisao(self):
        import os
        from afiliados_ml import telegram
        enviados = []
        os.environ["TELEGRAM_BOT_TOKEN"] = "tok"
        telegram.enviar("a" * 8500, "@canal", lambda t, c, x: enviados.append((t, c, len(x))))
        self.assertEqual(enviados, [("tok", "@canal", 4000), ("tok", "@canal", 4000), ("tok", "@canal", 500)])

    def test_sem_config(self):
        import os
        from afiliados_ml import telegram
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        with self.assertRaises(telegram.ErroTelegram):
            telegram.enviar("oi", "@canal")
