"""Testes do memory de aprendizado."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestAprendizado(unittest.TestCase):
    def setUp(self):
        # Sandbox: aponta MEMORY_FILE pra um temp file
        from memory import aprendizado
        self._orig_dir = aprendizado.MEMORY_DIR
        self._orig_file = aprendizado.MEMORY_FILE
        self.tmpdir = Path(tempfile.mkdtemp())
        aprendizado.MEMORY_DIR = self.tmpdir
        aprendizado.MEMORY_FILE = self.tmpdir / "classif_aprendizadas.jsonl"
        self.apr = aprendizado

    def tearDown(self):
        self.apr.MEMORY_DIR = self._orig_dir
        self.apr.MEMORY_FILE = self._orig_file
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_carregar_vazio(self):
        self.assertEqual(self.apr.carregar_regras(), [])

    def test_adicionar_e_aplicar(self):
        r = self.apr.adicionar_regra(
            padrao_regex=r"PRESIDENTE\s+DA\s+TNU",
            classif_correta="DECISAO_MONOCRATICA_PRESIDENTE_TNU",
            razao_jp="Presidente TNU não cabe agravo interno",
            exemplo_paj_origem="2026/039-01708",
        )
        self.assertTrue(len(self.apr.carregar_regras()) == 1)

        classif, regra = self.apr.aplicar_regras_aprendidas(
            blob_decisao="Despacho do Presidente da TNU nega seguimento."
        )
        self.assertEqual(classif, "DECISAO_MONOCRATICA_PRESIDENTE_TNU")
        self.assertEqual(regra.id, r.id)

    def test_nao_aplica_se_inativa(self):
        r = self.apr.adicionar_regra(
            padrao_regex=r"TESTE", classif_correta="X", razao_jp="t"
        )
        self.apr.desativar_regra(r.id)
        classif, _ = self.apr.aplicar_regras_aprendidas(blob_decisao="TESTE")
        self.assertIsNone(classif)

    def test_match_count_incrementa(self):
        r = self.apr.adicionar_regra(
            padrao_regex=r"X", classif_correta="C", razao_jp="t"
        )
        self.apr.aplicar_regras_aprendidas(blob_decisao="X aparece aqui")
        self.apr.aplicar_regras_aprendidas(blob_decisao="X de novo")
        regras = self.apr.carregar_regras()
        self.assertEqual(regras[0].matches_count, 2)

    def test_padrao_alvo_diferente(self):
        self.apr.adicionar_regra(
            padrao_regex=r"OUTRO_PADRAO",
            classif_correta="Y",
            razao_jp="t",
            padrao_alvo="desc_caixa",
        )
        classif, _ = self.apr.aplicar_regras_aprendidas(
            blob_decisao="OUTRO_PADRAO no blob"
        )
        # Não casa porque alvo é desc_caixa, não blob_decisao
        self.assertIsNone(classif)
        classif, _ = self.apr.aplicar_regras_aprendidas(
            desc_caixa="OUTRO_PADRAO na caixa"
        )
        self.assertEqual(classif, "Y")

    def test_primeira_regra_que_casa_vence(self):
        self.apr.adicionar_regra(
            padrao_regex=r"PRESIDENTE", classif_correta="A", razao_jp="t1"
        )
        self.apr.adicionar_regra(
            padrao_regex=r"PRESIDENTE.*TNU", classif_correta="B", razao_jp="t2"
        )
        classif, _ = self.apr.aplicar_regras_aprendidas(
            blob_decisao="Presidente da TNU decidiu"
        )
        self.assertEqual(classif, "A")  # ordem do arquivo


if __name__ == "__main__":
    unittest.main()
