#!/usr/bin/env python3
"""Gera PROMPT_MAX.md de um PAJ específico sob demanda.

Uso:
    python dpuscript/gerar_prompt_max.py 2026/039-07596
    python dpuscript/gerar_prompt_max.py --pasta Entrada/dpuscript/2026-039-07596

Lê metadata.json + peças/decisões do PAJ e gera PROMPT_MAX completo.
Usar antes de mandar Claude elaborar peça (ou abrir no Claude Code).
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
ENTRADA = WORKSPACE / "Entrada" / "dpuscript"

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "mcp_servers" / "sisdpu"))

# Carrega o módulo preparar_pajs (que tem gerar_prompt_max)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "preparar_pajs", str(SCRIPT_DIR / "preparar_pajs.py")
)
mod = importlib.util.module_from_spec(spec)
sys.modules["preparar_pajs"] = mod
try:
    spec.loader.exec_module(mod)
except ImportError:
    # Tolerar imports de clients que precisam de Playwright etc.
    pass


def normalizar_paj(paj: str) -> str:
    return paj.replace("/", "-")


def carregar_pecas_e_decisoes(pasta: Path) -> tuple[list[dict], list[dict]]:
    """Reconstrói as listas pecas_baixadas/stj_salvos a partir dos arquivos em disco."""
    pecas = []
    for sub in ("peças", "pecas"):
        d = pasta / sub
        if not d.exists():
            continue
        for arq in sorted(d.iterdir()):
            if arq.suffix == ".txt":
                pecas.append({
                    "arquivo": arq.name,
                    "arquivo_txt": str(arq.relative_to(pasta)),
                    "conteudo": arq.read_text(encoding="utf-8", errors="replace"),
                })
    decisoes = []
    d = pasta / "decisoes_superiores"
    if d.exists():
        for arq in sorted(d.iterdir()):
            if arq.suffix == ".txt":
                decisoes.append({
                    "arquivo": arq.name,
                    "arquivo_txt": str(arq.relative_to(pasta)),
                    "conteudo": arq.read_text(encoding="utf-8", errors="replace"),
                })
    return pecas, decisoes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paj", nargs="?", help="PAJ (ex: 2026/039-07596)")
    parser.add_argument("--pasta", help="Caminho direto pra pasta do PAJ")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Imprime no stdout em vez de salvar arquivo",
    )
    args = parser.parse_args()

    if args.pasta:
        pasta = Path(args.pasta).resolve()
    elif args.paj:
        pasta = ENTRADA / normalizar_paj(args.paj)
    else:
        parser.print_help()
        return 1

    if not pasta.exists() or not (pasta / "metadata.json").exists():
        print(f"ERRO: metadata.json não encontrado em {pasta}", file=sys.stderr)
        return 1

    metadata = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    datajud_data = None
    djf = pasta / "datajud.json"
    if djf.exists():
        try:
            datajud_data = json.loads(djf.read_text(encoding="utf-8"))
        except Exception:
            pass
    eventos_tnu = None
    etf = pasta / "eventos_tnu.json"
    if etf.exists():
        try:
            eventos_tnu = json.loads(etf.read_text(encoding="utf-8"))
        except Exception:
            pass

    pecas_baixadas, stj_salvos = carregar_pecas_e_decisoes(pasta)
    movs = metadata.get("detalhes_sisdpu", {}).get("movimentacoes", []) or []
    prazos = metadata.get("prazos_abertos", []) or []

    # Heurística simples: relevantes = primeiras 5 movs (mais recentes)
    movs_relevantes = movs[:5]
    seqs_preservar = set(str(m.get("seq", "")) for m in movs[:3])

    if not hasattr(mod, "gerar_prompt_max"):
        print("ERRO: gerar_prompt_max não disponível", file=sys.stderr)
        return 2

    prompt = mod.gerar_prompt_max(
        metadata, datajud_data, eventos_tnu,
        pecas_baixadas, stj_salvos,
        movs, movs_relevantes, seqs_preservar, prazos,
    )

    if args.stdout:
        sys.stdout.write(prompt)
    else:
        out = pasta / "PROMPT_MAX.md"
        out.write_text(prompt, encoding="utf-8")
        print(f"PROMPT_MAX gerado: {out} ({len(prompt)} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
