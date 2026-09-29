import unittest
from jotak_licitacoes.filtro import classificar
from jotak_licitacoes.leitores import ler_licitanet, ler_petronect

BOLETIM = """Prezado FORNECEDOR, confira o boletim de publicações.
DISPENSA ELETRÔNICA: 018 - MUNICÍPIO DE HELIÓPOLIS/BA / Heliópolis - Bahia
Inicio da Sessão: 17/09/2026 08:00:00
Descrição do(s) objeto(s): CONTRATAÇÃO DE EMPRESA ESPECIALIZADA PARA PRESTAÇÃO DE SERVIÇOS DE COMUNICAÇÃO INSTITUCIONAL, COMPREENDENDO ASSESSORIA DE IMPRENSA, GESTÃO DE MÍDIAS SOCIAIS E PRODUÇÃO AUDIOVISUAL.
PREGÃO ELETRÔNICO: 44 - MUNICÍPIO DE SEABRA/BA / Seabra - Bahia
Inicio da Sessão: 29/09/2026 09:00:00
Descrição do(s) objeto(s): AQUISIÇÃO DE BANNER EM LONA, CAMISAS E CRACHÁS
Caso necessite, entre em contato
"""


class Testes(unittest.TestCase):
    def test_produtos_da_jotak(self):
        for t in ["Banner Lona", "camisetas de algodão", "Bandeira do Brasil",
                  "Faixa em lona 3x1", "Crachá com cordão", "Placa PS 2mm",
                  "Adesivos de vinil"]:
            self.assertEqual(classificar(t)[0], "relevante", t)

    def test_ruido(self):
        for t in ["faixa etária de 5 a 10 anos", "placa de veículo", "bandeira de cartão",
                  "assessoria de imprensa e mídias sociais"]:
            self.assertEqual(classificar(t)[0], "descartar", t)

    def test_proximo_vira_talvez(self):
        self.assertEqual(classificar("serviços de plotagem")[0], "talvez")

    def test_licitanet(self):
        ops = ler_licitanet(BOLETIM)
        self.assertEqual(len(ops), 2)
        self.assertEqual(classificar(ops[0].objeto)[0], "descartar")
        self.assertEqual(classificar(ops[1].objeto)[0], "relevante")
        self.assertEqual(ops[1].sessao, "29/09/2026 09:00:00")

    def test_petronect(self):
        op, = ler_petronect(
            "Oportunidade Publicada ID 7004654440 - SERVICO DE IDENTIFICACAO VISUAL, SERVICOS DE IMPRESSAO GRAFICA, PLOTAGEM, ADESIVAGEM",
            'da ""MM-RGN-UTE-BLS-BF"".')
        self.assertEqual(op.id, "7004654440")
        self.assertEqual(op.orgao, "MM-RGN-UTE-BLS-BF")
        self.assertEqual(classificar(op.objeto)[0], "relevante")


unittest.main() if __name__ == "__main__" else None
