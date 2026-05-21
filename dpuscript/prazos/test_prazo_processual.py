"""Testes das regras de prazo processual — DPU Categoria Especial.

Roda com: python -X utf8 -m unittest dpuscript/prazos/test_prazo_processual.py
"""

import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prazos.prazo_processual import (  # noqa: E402
    CIENCIA_FICTA_EPROC_DIAS,
    Rito,
    calcular_data_alvo,
    eh_dia_util,
    feriados_nacionais,
    inferir_rito,
    rito_usa_eproc,
)


class TestFeriados(unittest.TestCase):
    def test_natal_2026(self):
        self.assertIn(dt.date(2026, 12, 25), feriados_nacionais(2026))

    def test_independencia_2026(self):
        self.assertIn(dt.date(2026, 9, 7), feriados_nacionais(2026))

    def test_dia_util_segunda_normal(self):
        # 2026-05-25 = segunda
        self.assertTrue(eh_dia_util(dt.date(2026, 5, 25)))

    def test_dia_nao_util_sabado(self):
        self.assertFalse(eh_dia_util(dt.date(2026, 5, 23)))


class TestCalculoCivelComDobra(unittest.TestCase):
    """Cível: dias úteis + dobra DPU."""
    def test_prazo_15d_civel_com_dobra(self):
        # 2026-05-21 = quinta. 15 * 2 = 30 dias úteis a partir de sexta 22/05
        data_mov = dt.date(2026, 5, 21)
        alvo = calcular_data_alvo(data_mov, 15, Rito.CIVEL, em_dobro=True)
        # 30 dias úteis depois de 21/05/2026 (excluindo dia da intimação)
        # Deve cair em julho 2026
        self.assertGreater(alvo, dt.date(2026, 6, 30))
        self.assertTrue(eh_dia_util(alvo))


class TestCalculoTNU(unittest.TestCase):
    """TNU/JEF: dias úteis, SEM dobra DPU, +10 dias e-Proc opcional."""

    def test_prazo_10d_tnu_sem_dobra(self):
        data_mov = dt.date(2026, 5, 4)  # segunda
        # 10 dias úteis sem dobra, sem ciência ficta
        # Conta a partir de 05/05: 05,06,07,08, (10,11),12,13,14,15, (17,18)
        # Dia 1=05/05, 2=06, 3=07, 4=08, 5=11, 6=12, 7=13, 8=14, 9=15, 10=18/05
        alvo = calcular_data_alvo(data_mov, 10, Rito.TNU, em_dobro=True)
        self.assertEqual(alvo, dt.date(2026, 5, 18))

    def test_prazo_10d_tnu_com_ciencia_ficta(self):
        data_mov = dt.date(2026, 5, 4)  # segunda
        # +10 dias corridos = 14/05 (quinta)
        # Depois 10 dias úteis a partir de 15/05 (sexta)
        # 15,18,19,20,21,22,25,26,27,28 — termina em 28/05
        alvo = calcular_data_alvo(
            data_mov, 10, Rito.TNU,
            em_dobro=True, ciencia_ficta_eproc=True,
        )
        self.assertEqual(alvo, dt.date(2026, 5, 28))

    def test_em_dobro_ignorado_em_tnu(self):
        data_mov = dt.date(2026, 5, 4)
        sem_dobra = calcular_data_alvo(data_mov, 10, Rito.TNU, em_dobro=False)
        com_dobra = calcular_data_alvo(data_mov, 10, Rito.TNU, em_dobro=True)
        self.assertEqual(sem_dobra, com_dobra)  # TNU ignora dobra


class TestCalculoSTJ(unittest.TestCase):
    """STJ: dias úteis, sem dobra (regra JP)."""

    def test_em_dobro_ignorado_em_stj(self):
        data_mov = dt.date(2026, 5, 4)
        sem = calcular_data_alvo(data_mov, 15, Rito.STJ, em_dobro=False)
        com = calcular_data_alvo(data_mov, 15, Rito.STJ, em_dobro=True)
        self.assertEqual(sem, com)


class TestInferirRito(unittest.TestCase):
    def test_resp_vira_stj(self):
        self.assertEqual(
            inferir_rito("", "Intimação eletrônica - REsp 12345 STJ", ""),
            Rito.STJ,
        )

    def test_recurso_especial_vira_stj(self):
        self.assertEqual(
            inferir_rito("", "Recurso Especial julgado", ""),
            Rito.STJ,
        )

    def test_tnu_vira_tnu(self):
        self.assertEqual(
            inferir_rito("", "Julgamento da TNU - Tema 384", ""),
            Rito.TNU,
        )

    def test_puil_vira_tnu(self):
        self.assertEqual(
            inferir_rito("", "PUIL 5003886-26.2022.4.04.7202", ""),
            Rito.TNU,
        )

    def test_eproc_vira_jef(self):
        self.assertEqual(
            inferir_rito("", "Decisão e-Proc disponibilizada", ""),
            Rito.JEF,
        )

    def test_default_civel(self):
        self.assertEqual(inferir_rito("", "Petição protocolada", ""), Rito.CIVEL)


class TestCienciaFicta(unittest.TestCase):
    def test_constante(self):
        self.assertEqual(CIENCIA_FICTA_EPROC_DIAS, 10)

    def test_jef_usa_eproc(self):
        self.assertTrue(rito_usa_eproc(Rito.JEF))

    def test_tnu_usa_eproc(self):
        self.assertTrue(rito_usa_eproc(Rito.TNU))

    def test_stj_nao_usa_eproc(self):
        self.assertFalse(rito_usa_eproc(Rito.STJ))

    def test_civel_nao_usa_eproc(self):
        self.assertFalse(rito_usa_eproc(Rito.CIVEL))


if __name__ == "__main__":
    unittest.main()
