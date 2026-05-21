#!/usr/bin/env python3
"""CLI helper pra JP corrigir classificação de um PAJ e ensinar o sistema.

Uso:
    python -m dpuscript.memory.corrigir <PAJ> <CLASSIF_CORRETA> "razao" [--padrao "regex"]

Exemplos:
    # Corrige PAJ específico (sem aprender regra geral):
    python -m dpuscript.memory.corrigir 2026/039-01708 DECISAO_MONOCRATICA_PRESIDENTE_TNU \
        "decisão do Presidente da TNU, não cabe agravo interno"

    # Corrige PAJ E aprende regra geral (regex casa no blob da decisão):
    python -m dpuscript.memory.corrigir 2026/039-01708 DECISAO_MONOCRATICA_PRESIDENTE_TNU \
        "Presidente TNU não cabe agravo" \
        --padrao "PRESIDENTE\\s+DA\\s+TNU.*DECIS[AO]?\\s+MONOCR"

Lista regras atuais:
    python -m dpuscript.memory.corrigir --listar

Desativa regra:
    python -m dpuscript.memory.corrigir --desativar <ID>
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DPUSCRIPT_DIR = SCRIPT_DIR.parent
WORKSPACE = DPUSCRIPT_DIR.parent
ENTRADA = WORKSPACE / "Entrada" / "dpuscript"

sys.path.insert(0, str(DPUSCRIPT_DIR))

from memory.aprendizado import (  # noqa: E402
    adicionar_regra,
    carregar_regras,
    desativar_regra,
)


def normalizar_paj(paj: str) -> str:
    """'2026/039-01708' -> '2026-039-01708'."""
    return paj.replace("/", "-")


def corrigir_paj(paj: str, classif_correta: str, razao: str) -> bool:
    """Atualiza metadata.json do PAJ + estado pajs_processados.json."""
    paj_norm = normalizar_paj(paj)
    pasta = ENTRADA / paj_norm
    meta_file = pasta / "metadata.json"
    if not meta_file.exists():
        print(f"ERRO: PAJ não encontrado em {pasta}", file=sys.stderr)
        return False

    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    velha = meta.get("classificacao", "?")
    meta["classificacao"] = classif_correta
    meta.setdefault("classificacao_historico", []).append({
        "em": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "de": velha,
        "para": classif_correta,
        "motivo": "correcao_manual_jp",
        "razao": razao,
    })
    meta_file.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Atualiza também o estado
    state_file = DPUSCRIPT_DIR / "estado" / "pajs_processados.json"
    if state_file.exists():
        estado = json.loads(state_file.read_text(encoding="utf-8"))
        if paj in estado.get("pajs", {}):
            estado["pajs"][paj]["classificacao"] = classif_correta
            state_file.write_text(
                json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    print(f"OK: {paj} {velha} -> {classif_correta}")
    return True


def listar():
    regras = carregar_regras()
    if not regras:
        print("(nenhuma regra aprendida ainda)")
        return
    print(f"REGRAS APRENDIDAS ({len(regras)}):\n")
    for r in regras:
        status = "ativa" if r.ativa else "INATIVA"
        print(f"  [{r.id}] {status}  matches={r.matches_count}")
        print(f"    alvo: {r.padrao_alvo}")
        print(f"    regex: {r.padrao_regex}")
        print(f"    -> {r.classif_correta}")
        print(f"    razão: {r.razao_jp}")
        if r.exemplo_paj_origem:
            print(f"    origem: {r.exemplo_paj_origem}")
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paj", nargs="?", help="PAJ a corrigir (ex: 2026/039-01708)")
    parser.add_argument("classif_correta", nargs="?", help="Nova classificação")
    parser.add_argument("razao", nargs="?", help="Razão da correção")
    parser.add_argument(
        "--padrao",
        help="Regex pra criar regra geral (aplica em casos similares futuros)",
    )
    parser.add_argument(
        "--alvo",
        default="blob_decisao",
        choices=["blob_decisao", "desc_caixa", "blob_recentes"],
        help="Onde a regex casa (default: blob_decisao = texto das peças)",
    )
    parser.add_argument("--listar", action="store_true", help="Lista regras aprendidas")
    parser.add_argument("--desativar", help="Desativa regra pelo ID")
    args = parser.parse_args()

    if args.listar:
        listar()
        return 0

    if args.desativar:
        if desativar_regra(args.desativar):
            print(f"Regra {args.desativar} desativada.")
            return 0
        else:
            print(f"Regra {args.desativar} não encontrada.", file=sys.stderr)
            return 1

    if not (args.paj and args.classif_correta and args.razao):
        parser.print_help()
        return 1

    # 1. Corrige o PAJ específico
    if not corrigir_paj(args.paj, args.classif_correta, args.razao):
        return 1

    # 2. Se --padrao foi dado, cria regra geral
    if args.padrao:
        r = adicionar_regra(
            padrao_regex=args.padrao,
            classif_correta=args.classif_correta,
            razao_jp=args.razao,
            exemplo_paj_origem=args.paj,
            padrao_alvo=args.alvo,
        )
        print(f"Regra geral aprendida: id={r.id}")
        print(f"  alvo={r.padrao_alvo}  regex={r.padrao_regex}")
        print(f"  -> {r.classif_correta}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
