"""Módulo de detecção e cálculo de prazos processuais — DPU Categoria Especial.

Adaptado do fork de tuliorm/DPU-script-SIS pra realidade JP:
- Atua em TNU + STJ (não 1ª instância como o colega)
- TNU/STJ: SEM dobra DPU (JEF), dias úteis
- e-Proc: +10 dias corridos de ciência ficta antes da contagem do prazo
"""
from .prazo_processual import (
    Rito,
    calcular_data_alvo,
    dias_restantes,
    eh_dia_util,
    feriados_nacionais,
    inferir_rito,
    proximo_dia_util,
)
from .detector import detectar_prazos_novos

__all__ = [
    "Rito",
    "calcular_data_alvo",
    "dias_restantes",
    "eh_dia_util",
    "feriados_nacionais",
    "inferir_rito",
    "proximo_dia_util",
    "detectar_prazos_novos",
]
