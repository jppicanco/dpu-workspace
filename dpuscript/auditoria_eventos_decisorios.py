#!/usr/bin/env python3
"""Auditoria: PAJs com evento decisório no e-Proc mas classificados como
'aguardar julgamento' / DESPACHO — universo afetado pelo bug de eventos_tnu
ignorado no PROMPT_MAX (corrigido em 2026-06-17).

Uso: python auditoria_eventos_decisorios.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

WORKSPACE = Path(os.getenv("DPU_WORKSPACE", "/Users/macmini/dpu-workspace"))
ENTRADA = WORKSPACE / "Entrada" / "dpuscript"

TERMOS = (
    "negado seguimento", "nego seguimento", "negar seguimento",
    "negado provimento", "nego provimento", "improvido", "improcedente",
    "não conhecido", "nao conhecido", "não conheço", "nao conheco",
    "inadmitido", "inadmissão", "inadmissao", "não admitido", "nao admitido",
    "indeferido", "indefiro", "denegado", "denego", "extinto",
    "extinção", "extincao", "prejudicado", "transitado em julgado",
)


def termos_decisorios(eventos_json: dict) -> list[str]:
    achados = []
    consulta = (eventos_json or {}).get("consulta") or {}
    for ev in consulta.get("eventos") or []:
        desc = (ev.get("descricao") or "")
        low = desc.lower()
        for t in TERMOS:
            if t in low:
                achados.append(f"ev{ev.get('numero','?')} ({ev.get('data','?')}): {desc.splitlines()[0][:60]}")
                break
    return achados


def main() -> int:
    if not ENTRADA.exists():
        print(f"ENTRADA nao existe: {ENTRADA}")
        return 1

    suspeitos = []
    total_com_eventos = 0
    for pasta in sorted(ENTRADA.iterdir()):
        if not pasta.is_dir():
            continue
        etf = pasta / "eventos_tnu.json"
        if not etf.exists():
            continue
        try:
            ev = json.loads(etf.read_text(encoding="utf-8"))
        except Exception:
            continue
        total_com_eventos += 1
        achados = termos_decisorios(ev)
        if not achados:
            continue
        # tem evento decisorio — como foi classificado?
        atf = pasta / "atuacao.json"
        tipo = status = ofazer = "?"
        if atf.exists():
            try:
                a = json.loads(atf.read_text(encoding="utf-8"))
                tipo = a.get("tipo", "?")
                status = a.get("status", "?")
                ofazer = (a.get("o_que_fazer", "") or "")[:80]
            except Exception:
                pass
        # suspeito = tem decisao terminativa mas classificado como DESPACHO
        flag = "⚠️ SUSPEITO" if tipo == "DESPACHO" else "  ok-ish"
        suspeitos.append((flag, pasta.name, tipo, status, achados[0], ofazer))

    print(f"PAJs com eventos_tnu.json: {total_com_eventos}")
    print(f"PAJs com evento DECISÓRIO no e-Proc: {len(suspeitos)}\n")
    # ordena: suspeitos primeiro
    suspeitos.sort(key=lambda x: (0 if "SUSPEITO" in x[0] else 1, x[1]))
    for flag, paj, tipo, status, achado, ofazer in suspeitos:
        print(f"{flag} | {paj} | tipo={tipo} status={status}")
        print(f"         evento: {achado}")
        if "SUSPEITO" in flag:
            print(f"         o_que_fazer: {ofazer}")
    n_susp = sum(1 for s in suspeitos if "SUSPEITO" in s[0])
    print(f"\n=== TOTAL SUSPEITOS (DESPACHO com evento decisório): {n_susp} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
