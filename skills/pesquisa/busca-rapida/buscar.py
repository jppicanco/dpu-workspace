#!/usr/bin/env python3
"""Busca rápida jurisprudencial — versão light pra triagem.

Diferente de `pesquisa-juridica/pesquisar.py` (Claude full no PC):
- Sem Banco de Fontes Verificadas
- Sem síntese, sem [Fxxx]
- Saída: lista bruta de precedentes encontrados
- Roda no M4 (Grok) ou PC; rápido (~5-10s por query)

Uso:
    python buscar.py "tema 384 TNU complementação contribuição"
    python buscar.py "REsp 1600453" --max 5
    python buscar.py "EMEN[aposentadoria]" --tribunais STJ,TNU

Output: JSON com lista de {tribunal, relator, data, ementa_curta, url}.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

# Path setup — encontra mcp_servers do dpu-workspace
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parents[2]  # skills/pesquisa/busca-rapida/ -> workspace
# Tenta 2 locais: dpuscript/mcp_servers/ ou raiz/mcp_servers/
MCP_CJF_CANDIDATES = [
    WORKSPACE / "dpuscript" / "mcp_servers" / "cjf-jurisprudencia",
    Path("/Users/macmini/jarbas/mcp_servers/cjf-jurisprudencia"),
    Path.home() / "jarbas" / "mcp_servers" / "cjf-jurisprudencia",
]


def _carregar_cjf():
    """Carrega módulo CJF do primeiro path que existir. Retorna função busca."""
    for cand in MCP_CJF_CANDIDATES:
        if cand.exists() and (cand / "server.py").exists():
            sys.path.insert(0, str(cand.parent))  # pra shared/
            sys.path.insert(0, str(cand))
            spec = importlib.util.spec_from_file_location(
                "cjf_server", str(cand / "server.py")
            )
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return getattr(mod, "buscar_jurisprudencia_cjf", None)
            except Exception as e:
                print(
                    f"[busca-rapida] erro carregando CJF de {cand}: {e}",
                    file=sys.stderr,
                )
                continue
    return None


def _parse_xml_para_json(xml_str: str) -> list[dict]:
    """Extrai lista simples de resultados do XML formatado da CJF."""
    import re

    resultados = []
    blocos = re.findall(
        r"<resultado>(.*?)</resultado>",
        xml_str,
        re.DOTALL,
    )
    for bloco in blocos:
        def tag(t: str) -> str:
            m = re.search(rf"<{t}>(.*?)</{t}>", bloco, re.DOTALL)
            return (m.group(1) if m else "").strip()

        ementa = tag("ementa")
        resultados.append({
            "tribunal": tag("tribunal"),
            "relator": tag("relator"),
            "data": tag("data_decisao") or tag("data"),
            "orgao": tag("orgao_julgador"),
            "processo": tag("processo") or tag("numero"),
            "ementa_curta": ementa[:300] + ("..." if len(ementa) > 300 else ""),
            "url": tag("url"),
        })
    return resultados


def buscar(query: str, tribunais: str = "STF,STJ,TNU,TRF1,TRF2,TRF3,TRF4,TRF5,TRF6", max_resultados: int = 10) -> dict:
    cjf_func = _carregar_cjf()
    if not cjf_func:
        return {
            "ok": False,
            "erro": "CJF MCP não encontrado em nenhum path",
            "candidatos_tentados": [str(p) for p in MCP_CJF_CANDIDATES],
            "resultados": [],
        }
    try:
        xml = cjf_func(busca=query, tribunais=tribunais, max_resultados=max_resultados)
        if isinstance(xml, str) and xml.strip().startswith("<"):
            resultados = _parse_xml_para_json(xml)
        else:
            resultados = []
        return {
            "ok": True,
            "query": query,
            "tribunais": tribunais,
            "total": len(resultados),
            "resultados": resultados,
            "raw_first_500": (xml[:500] if isinstance(xml, str) else str(xml)[:500]),
        }
    except Exception as e:
        return {
            "ok": False,
            "erro": f"{type(e).__name__}: {e}",
            "resultados": [],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Query de busca (sintaxe CJF)")
    parser.add_argument(
        "--tribunais",
        default="STF,STJ,TNU,TRF1,TRF2,TRF3,TRF4,TRF5,TRF6",
        help="Tribunais separados por vírgula",
    )
    parser.add_argument("--max", type=int, default=10, help="Máximo de resultados")
    parser.add_argument("--json", action="store_true", help="Saída JSON crua")
    args = parser.parse_args()

    r = buscar(args.query, tribunais=args.tribunais, max_resultados=args.max)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["ok"] else 1

    # Saída legível
    if not r["ok"]:
        print(f"ERRO: {r.get('erro')}", file=sys.stderr)
        return 1
    print(f"Query: {r['query']}")
    print(f"Tribunais: {r['tribunais']}")
    print(f"Total: {r['total']}\n")
    for i, item in enumerate(r["resultados"], 1):
        print(f"--- {i} ---")
        print(f"  tribunal: {item['tribunal']}  orgao: {item['orgao']}")
        print(f"  processo: {item['processo']}  relator: {item['relator']}  data: {item['data']}")
        print(f"  ementa: {item['ementa_curta']}")
        if item["url"]:
            print(f"  url: {item['url']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
