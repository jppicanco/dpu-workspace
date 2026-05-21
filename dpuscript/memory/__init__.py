"""Memory de aprendizado — regras aprendidas com feedback do JP.

Cada correção manual do JP vira regra. Regras se aplicam a casos similares
no futuro, reduzindo erros recorrentes.
"""
from .aprendizado import (
    Regra,
    adicionar_regra,
    aplicar_regras_aprendidas,
    carregar_regras,
    desativar_regra,
)

__all__ = [
    "Regra",
    "adicionar_regra",
    "aplicar_regras_aprendidas",
    "carregar_regras",
    "desativar_regra",
]
