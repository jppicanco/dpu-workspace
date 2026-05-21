"""Detector de prazos processuais a partir de movimentações do SISDPU.

Adaptado de tuliorm/DPU-script-SIS pra realidade JP (TNU + STJ).

Compara movimentações antes/depois da sync e identifica intimações/citações
novas. Para cada uma, tenta extrair um prazo em dias e calcular a data-alvo
APLICANDO AS REGRAS PROCESSUAIS via `prazos.prazo_processual`.

Heurísticas conservadoras — melhor falso positivo (usuário descarta) do
que falso negativo (perde prazo).
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable

from .prazo_processual import (
    Rito,
    calcular_data_alvo,
    inferir_rito,
    rito_usa_eproc,
)


# Padrões que indicam intimação/citação/prazo
_RGX_INTIMACAO = re.compile(
    r"intima[cç][aã]o|cita[cç][aã]o|notifica[cç][aã]o|expedida.*intima",
    re.IGNORECASE,
)
_RGX_DIAS = re.compile(
    r"prazo\s+d[eoa]?\s*(\d{1,3})\s*(?:dias?|\(\s*\d+\s*\))?",
    re.IGNORECASE,
)
_RGX_DIAS_SIMPLES = re.compile(
    r"\b(\d{1,3})\s*dias?\s*(?:uteis|úteis)?\b",
    re.IGNORECASE,
)
_RGX_DATA = re.compile(r"\bat[ée]\s+(\d{2}/\d{2}/\d{4})\b", re.IGNORECASE)


def _parse_data_br(s: str) -> dt.date | None:
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _extrair_prazo_dias(descricao: str) -> int | None:
    """Extrai prazo em dias da descrição da movimentação."""
    m = _RGX_DIAS.search(descricao or "")
    if m:
        try:
            n = int(m.group(1))
            if 1 <= n <= 365:
                return n
        except Exception:
            pass
    m = _RGX_DIAS_SIMPLES.search(descricao or "")
    if m:
        try:
            n = int(m.group(1))
            # Heurística conservadora
            if 1 <= n <= 60 and _RGX_INTIMACAO.search(descricao or ""):
                return n
        except Exception:
            pass
    return None


def _extrair_data_alvo_explicita(descricao: str) -> dt.date | None:
    m = _RGX_DATA.search(descricao or "")
    if not m:
        return None
    return _parse_data_br(m.group(1))


def _id_prazo(paj_norm: str, seq: int | str) -> str:
    agora_iso = dt.datetime.now().replace(microsecond=0).isoformat()
    return f"{agora_iso}-{paj_norm}-seq{seq}"


def detectar_prazos_novos(
    paj_norm: str,
    movs_antigas: Iterable[dict],
    movs_novas: Iterable[dict],
    assistido: str = "",
    foro: str = "",
    classificacao: str = "",
    aplicar_ciencia_ficta_eproc: bool = True,
) -> list[dict]:
    """Compara movimentações e retorna lista de prazos novos detectados.

    Args:
        paj_norm: PAJ normalizado (ex: '2026-039-07596')
        movs_antigas: movimentações já conhecidas (set de seqs)
        movs_novas: movimentações atuais
        assistido: nome do assistido (pra título do prazo)
        foro: foro/tribunal
        classificacao: classificação da PAJ
        aplicar_ciencia_ficta_eproc: se True, adiciona +10 dias e-Proc quando
            rito é JEF/TNU (default True — comportamento JP padrão)

    Returns:
        Lista de prazos novos. Cada item:
            {
                "id": str,
                "paj_norm": str,
                "titulo": str,
                "descricao": str,
                "data_mov": "YYYY-MM-DD",
                "prazo_dias": int | None,
                "data_alvo": "YYYY-MM-DD",
                "rito": Rito (value),
                "em_dobro": bool,
                "ciencia_ficta_aplicada": bool,
                "assistido": str,
                "fonte_mov_seq": int,
                "status": "pendente",
                "detectado_em": ISO,
            }
    """
    seqs_antigas = set()
    for m in (movs_antigas or []):
        try:
            seqs_antigas.add(int(m.get("seq", 0) or 0))
        except Exception:
            continue

    novos: list[dict] = []
    for m in (movs_novas or []):
        try:
            seq = int(m.get("seq", 0) or 0)
        except Exception:
            continue
        if seq in seqs_antigas:
            continue

        desc = m.get("descricao", "") or ""
        if not _RGX_INTIMACAO.search(desc):
            continue

        data_mov = _parse_data_br(
            m.get("data_original") or m.get("data") or ""
        )

        rito = inferir_rito(
            area_paj=classificacao or "",
            descricao_mov=desc,
            foro=foro or "",
        )

        data_alvo_explicita = _extrair_data_alvo_explicita(desc)
        dias = (
            _extrair_prazo_dias(desc)
            if data_alvo_explicita is None
            else None
        )

        # JP: dobra só em Cível/Admin
        em_dobro = rito in (Rito.CIVEL, Rito.ADMINISTRATIVO)
        # Ciência ficta e-Proc: aplicável a TNU/JEF
        ciencia_ficta = (
            aplicar_ciencia_ficta_eproc and rito_usa_eproc(rito)
        )

        data_alvo: dt.date | None = data_alvo_explicita
        if data_alvo is None and dias is not None and data_mov is not None:
            data_alvo = calcular_data_alvo(
                data_mov,
                dias,
                rito,
                em_dobro=em_dobro,
                ciencia_ficta_eproc=ciencia_ficta,
            )

        titulo = (
            f"[Prazo {dias}d] {paj_norm}"
            if dias else f"[Intimacao] {paj_norm}"
        )
        if assistido:
            titulo += f" — {assistido[:60]}"

        novos.append({
            "id": _id_prazo(paj_norm, seq),
            "paj_norm": paj_norm,
            "titulo": titulo,
            "descricao": desc[:500],
            "data_mov": data_mov.isoformat() if data_mov else "",
            "prazo_dias": dias,
            "data_alvo": data_alvo.isoformat() if data_alvo else "",
            "rito": rito.value,
            "em_dobro": em_dobro,
            "ciencia_ficta_aplicada": ciencia_ficta,
            "assistido": assistido,
            "fonte_mov_seq": seq,
            "status": "pendente",
            "detectado_em": dt.datetime.now().isoformat(timespec="seconds"),
        })

    return novos
