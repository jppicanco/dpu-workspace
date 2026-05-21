"""Cálculo determinístico de prazos processuais — DPU Categoria Especial.

Adaptado de tuliorm/DPU-script-SIS para realidade JP (TNU + STJ).

Regras:

Cível/Administrativo (1ª instância — JP NÃO atua em regra):
  - Dias úteis (CPC art. 219).
  - Exclui o dia da intimação, inclui o dia final.
  - Termo final em fim de semana/feriado prorroga pro próximo dia útil.
  - Suspensão 20/12 a 20/01 (recesso forense).
  - Prazo em DOBRO pra DPU (art. 186 CPC, art. 44, I, LC 80/94).

JEF / TNU (Turma Nacional de Uniformização):
  - Dias úteis e regras gerais do CPC, MAS sem prazo em dobro pra DPU.
  - Recesso forense suspende.
  - Lei 10.259/2001 — sistema dos Juizados Especiais Federais.

STJ (Superior Tribunal de Justiça):
  - Dias úteis (CPC art. 219).
  - Sem prazo em dobro pra DPU em recurso especial (Súmula 116 STJ não
    se aplica à DPU; LC 80/94 art. 44 I vigente para todas as instâncias,
    mas regra prática observada: DPU usa o prazo simples na cultura JP).
    REVISAR: confirmar regra interna DPU JP.
  - Recesso forense suspende.

Penal:
  - Dias corridos (sabado, domingo e feriado contam).
  - SEM dobra DPU em prazo penal.
  - Recesso forense NÃO suspende prazo penal.

Ciência ficta e-Proc (+10 dias corridos):
  Sistema e-Proc da TNU/JEF abre intimação automaticamente após 10 dias
  corridos da disponibilização. Se JP não abre formalmente:
    prazo efetivo = 10 dias corridos (ciência ficta) + prazo processual em dias úteis
  Tratado via parâmetro `ciencia_ficta_eproc_dias` em `calcular_data_alvo`.

Sem dependência externa: feriados nacionais + Carnaval/Páscoa/Corpus Christi
calculados a partir do algoritmo de Gauss para a data da Páscoa.
"""

from __future__ import annotations

import datetime as dt
import unicodedata
from enum import Enum
from functools import lru_cache


class Rito(str, Enum):
    CIVEL = "civel"
    JEF = "jef"
    TNU = "tnu"
    STJ = "stj"
    PENAL = "penal"
    ADMINISTRATIVO = "administrativo"


# Recesso forense (CPC art. 220): 20/12 a 20/01, inclusivos.
RECESSO_INICIO_MES_DIA = (12, 20)
RECESSO_FIM_MES_DIA = (1, 20)

# Ciência ficta e-Proc TNU/JEF — Lei 11.419/2006 art. 5 §3
CIENCIA_FICTA_EPROC_DIAS = 10


def _domingo_pascoa(ano: int) -> dt.date:
    """Algoritmo de Gauss/Meeus pra data da Páscoa no calendário gregoriano."""
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    mes = (h + L - 7 * m + 114) // 31
    dia = ((h + L - 7 * m + 114) % 31) + 1
    return dt.date(ano, mes, dia)


@lru_cache(maxsize=64)
def feriados_nacionais(ano: int) -> frozenset[dt.date]:
    """Feriados federais brasileiros + Carnaval/Sexta-feira Santa/Corpus Christi.

    Não inclui feriados estaduais/municipais. Para fins de prazo processual
    federal isso é suficiente; o sistema judiciário federal segue feriados
    nacionais.
    """
    fixos = {
        dt.date(ano, 1, 1),    # Confraternização
        dt.date(ano, 4, 21),   # Tiradentes
        dt.date(ano, 5, 1),    # Trabalho
        dt.date(ano, 9, 7),    # Independência
        dt.date(ano, 10, 12),  # N. Sra. Aparecida
        dt.date(ano, 11, 2),   # Finados
        dt.date(ano, 11, 15),  # Proclamação da República
        dt.date(ano, 11, 20),  # Consciência Negra (federal a partir de 2024)
        dt.date(ano, 12, 25),  # Natal
    }
    pascoa = _domingo_pascoa(ano)
    moveis = {
        pascoa - dt.timedelta(days=48),  # Segunda de Carnaval
        pascoa - dt.timedelta(days=47),  # Terça de Carnaval
        pascoa - dt.timedelta(days=2),   # Sexta-feira Santa
        pascoa + dt.timedelta(days=60),  # Corpus Christi
    }
    return frozenset(fixos | moveis)


def eh_recesso_forense(d: dt.date) -> bool:
    """True se a data está entre 20/12 e 20/01 (inclusivos)."""
    if (d.month, d.day) >= RECESSO_INICIO_MES_DIA:
        return True
    if (d.month, d.day) <= RECESSO_FIM_MES_DIA:
        return True
    return False


def eh_dia_util(d: dt.date) -> bool:
    """Cível/JEF/TNU/STJ/Admin: não é sáb/dom, não é feriado, não é recesso."""
    if d.weekday() >= 5:
        return False
    if d in feriados_nacionais(d.year):
        return False
    if eh_recesso_forense(d):
        return False
    return True


def eh_dia_util_penal(d: dt.date) -> bool:
    """Penal: ignora recesso forense (mas considera sáb/dom/feriado)."""
    if d.weekday() >= 5:
        return False
    if d in feriados_nacionais(d.year):
        return False
    return True


def proximo_dia_util(d: dt.date, *, penal: bool = False) -> dt.date:
    """Avança até cair num dia útil. Se já for útil, retorna a própria data."""
    check = eh_dia_util_penal if penal else eh_dia_util
    while not check(d):
        d = d + dt.timedelta(days=1)
    return d


def _calcular_uteis(data_inicio: dt.date, dias: int) -> dt.date:
    """Conta `dias` dias úteis a partir do dia seguinte a data_inicio."""
    cur = data_inicio + dt.timedelta(days=1)
    restantes = dias
    while restantes > 0:
        if eh_dia_util(cur):
            restantes -= 1
            if restantes == 0:
                return cur
        cur = cur + dt.timedelta(days=1)
    return cur


def _calcular_penal(data_mov: dt.date, dias: int) -> dt.date:
    """Penal: dias corridos. Início e termo prorrogam se cair em fds/feriado."""
    inicio = proximo_dia_util(data_mov + dt.timedelta(days=1), penal=True)
    final = inicio + dt.timedelta(days=dias - 1)
    return proximo_dia_util(final, penal=True)


# Ritos onde DPU TEM dobra
_DOBRA_APLICAVEL = (Rito.CIVEL, Rito.ADMINISTRATIVO)
# Ritos onde DPU NUNCA tem dobra (JEF/TNU/STJ/Penal)
_DOBRA_NAO_APLICAVEL = (Rito.JEF, Rito.TNU, Rito.STJ, Rito.PENAL)


def calcular_data_alvo(
    data_mov: dt.date,
    dias: int,
    rito: Rito,
    em_dobro: bool = True,
    ciencia_ficta_eproc: bool = False,
) -> dt.date:
    """Calcula data-alvo do prazo aplicando regras do rito.

    Args:
        data_mov: data da movimentação/disponibilização da intimação
        dias: prazo processual em dias (dado da movimentação)
        rito: Rito.CIVEL/JEF/TNU/STJ/PENAL/ADMINISTRATIVO
        em_dobro: aplica dobra DPU (art. 186 CPC). Ignorado em rito sem dobra.
        ciencia_ficta_eproc: se True, adiciona 10 dias corridos antes da
            contagem do prazo processual (ciência ficta do e-Proc).
            Aplicável a TNU e JEF tipicamente.

    Returns:
        data-alvo (data limite pra protocolar)
    """
    if dias <= 0:
        return data_mov

    if rito == Rito.PENAL:
        return _calcular_penal(data_mov, dias)

    # Ciência ficta e-Proc: +10 dias corridos antes da contagem
    inicio_contagem = data_mov
    if ciencia_ficta_eproc:
        inicio_contagem = data_mov + dt.timedelta(days=CIENCIA_FICTA_EPROC_DIAS)

    dias_efetivos = dias
    if em_dobro and rito in _DOBRA_APLICAVEL:
        dias_efetivos = dias * 2
    # JEF/TNU/STJ: sem dobra mesmo com em_dobro=True

    final = _calcular_uteis(inicio_contagem, dias_efetivos)
    return proximo_dia_util(final)


def dias_restantes(data_alvo: dt.date, hoje: dt.date | None = None) -> int:
    """Diferença em dias corridos entre hoje e data_alvo. Negativo = vencido."""
    hoje = hoje or dt.date.today()
    return (data_alvo - hoje).days


def _norm(s: str) -> str:
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def inferir_rito(area_paj: str = "", descricao_mov: str = "", foro: str = "") -> Rito:
    """Heurística pra inferir rito a partir de dados do PAJ + mov.

    Ordem (JP atua TNU + STJ, então prioriza esses):
    1. STJ se descrição/foro mencionar 'STJ' / 'recurso especial' / 'REsp'
    2. TNU se mencionar 'TNU' / 'turma nacional de uniformização' / 'PUIL'
    3. JEF se mencionar 'juizado especial federal' ou 'JEF'
    4. PENAL se área criminal ou termos penais
    5. ADMINISTRATIVO se área administrativa
    6. CIVEL default
    """
    area = _norm(area_paj)
    desc = _norm(descricao_mov)
    foro_n = _norm(foro)
    combo = f" {desc} {foro_n} "

    # STJ
    if "stj" in combo or "superior tribunal de justica" in combo:
        return Rito.STJ
    if "recurso especial" in combo or " resp " in combo or " aresp " in combo:
        return Rito.STJ

    # TNU
    if "tnu" in combo or "turma nacional de uniformizacao" in combo:
        return Rito.TNU
    if " puil " in combo or "pedido de uniformizacao" in combo:
        return Rito.TNU

    # JEF
    if "juizado especial federal" in combo or " jef " in combo:
        return Rito.JEF
    if "e-proc" in combo or "eproc" in combo:
        # e-Proc é usado em JEF/TNU — sem outro sinal, tratar como JEF
        return Rito.JEF

    # Penal
    if area in ("criminal", "penal"):
        return Rito.PENAL
    if any(t in desc for t in (
        "denuncia", "alegacoes finais", "habeas corpus", "cautelar penal",
    )):
        return Rito.PENAL

    if area == "administrativo":
        return Rito.ADMINISTRATIVO

    return Rito.CIVEL


def rito_usa_eproc(rito: Rito) -> bool:
    """Retorna True se o rito tipicamente usa e-Proc (sujeito a ciência ficta)."""
    return rito in (Rito.JEF, Rito.TNU)
