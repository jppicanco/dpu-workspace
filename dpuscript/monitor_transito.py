#!/usr/bin/env python3
"""
Monitor de trânsito em julgado — verifica periodicamente os processos
na watchlist pra detectar trânsito/baixa e alertar o Defensor.

Uso:
    .venv\\Scripts\\python.exe monitor_transito.py          # roda verificacao
    .venv\\Scripts\\python.exe monitor_transito.py --list   # mostra watchlist
    .venv\\Scripts\\python.exe monitor_transito.py --force  # verifica todos, ignora proxima_verificacao

Watchlist em: dpuscript/watchlist.json
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MCP_DIR = SCRIPT_DIR / "mcp_servers"
WATCHLIST_FILE = SCRIPT_DIR / "watchlist.json"
NOTIFICAR_SCRIPT = SCRIPT_DIR / "notificar_telegram.py"

# Carrega cliente TNU publico (consulta sem login)
sys.path.insert(0, str(MCP_DIR / "sisdpu"))


def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def _carregar_tnu_client():
    spec = importlib.util.spec_from_file_location(
        "tnu_client", str(MCP_DIR / "tnu" / "client.py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tnu_client"] = mod
    spec.loader.exec_module(mod)
    return mod


def carregar_watchlist() -> dict:
    if not WATCHLIST_FILE.exists():
        return {"itens": {}, "atualizada_em": None}
    try:
        return json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"itens": {}, "atualizada_em": None}


def salvar_watchlist(wl: dict) -> None:
    wl["atualizada_em"] = datetime.now().isoformat()
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_FILE.write_text(
        json.dumps(wl, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


# Padroes que indicam transito/baixa/arquivamento definitivo
PADROES_TRANSITO = [
    re.compile(r"tr[âa]nsit(?:ou|o)\s+em\s+julgado", re.IGNORECASE),
    re.compile(r"certid[ãa]o\s+de\s+tr[âa]nsito", re.IGNORECASE),
    re.compile(r"baixa\s+(?:definitiva|do\s+processo|a\s+origem)", re.IGNORECASE),
    re.compile(r"remetid[oa]s?\s+(?:a|para)\s+origem", re.IGNORECASE),
    re.compile(r"arquivamento\s+definitivo", re.IGNORECASE),
    re.compile(r"devolvid[oa]s?\s+a\s+origem", re.IGNORECASE),
]


def detectar_transito(eventos: list[dict]) -> dict | None:
    """Procura nos eventos sinais de transito/baixa. Retorna dict com o sinal
    encontrado ou None."""
    for ev in eventos:
        descricao = (ev.get("descricao") or ev.get("titulo") or "") + " " + (ev.get("nome") or "")
        for pat in PADROES_TRANSITO:
            m = pat.search(descricao)
            if m:
                return {
                    "evento": ev.get("numero") or ev.get("seq") or "?",
                    "data": ev.get("data", ""),
                    "sinal": m.group(0),
                    "trecho": descricao[:200],
                }
    return None


async def verificar_paj(paj: str, item: dict, tnu_client) -> dict:
    """Verifica 1 PAJ no e-Proc publico TNU. Retorna item atualizado."""
    cnj = item.get("cnj", "")
    if not cnj:
        item["ultimo_erro"] = "sem CNJ"
        return item

    _log(f"  consultando {paj} (CNJ {cnj})")
    try:
        proc = await tnu_client.consultar_processo(cnj)
    except Exception as e:
        item["ultimo_erro"] = f"consulta falhou: {e}"
        item["ultima_verificacao"] = datetime.now().isoformat()
        return item

    if proc.get("erro"):
        item["ultimo_erro"] = proc["erro"]
        item["ultima_verificacao"] = datetime.now().isoformat()
        return item

    eventos = proc.get("eventos", [])
    sinal = detectar_transito(eventos)

    item["ultima_verificacao"] = datetime.now().isoformat()
    item["ultimo_erro"] = None
    item["total_eventos_na_consulta"] = len(eventos)

    if sinal:
        item["status"] = "transitou"
        item["transitou_em"] = datetime.now().isoformat()
        item["sinal_detectado"] = sinal
        item.setdefault("historico", []).append({
            "data": datetime.now().isoformat(),
            "evento": "DETECTADO_TRANSITO",
            "sinal": sinal,
        })
        _log(f"  >>> TRANSITO DETECTADO em {paj}: {sinal['sinal']}")
    else:
        # Agenda proxima verificacao
        freq = int(item.get("frequencia_dias", 15))
        proxima = datetime.now() + timedelta(days=freq)
        item["proxima_verificacao"] = proxima.date().isoformat()
        _log(f"  ainda nao transitou, proxima em {item['proxima_verificacao']}")

    return item


def enviar_telegram(mensagem: str) -> None:
    """Envia mensagem via notificar_telegram.py."""
    if not NOTIFICAR_SCRIPT.exists():
        _log("notificar_telegram.py nao encontrado — ignorando alerta")
        return
    try:
        import subprocess
        subprocess.run(
            [sys.executable, str(NOTIFICAR_SCRIPT), mensagem],
            timeout=15, capture_output=True,
        )
    except Exception as e:
        _log(f"erro ao enviar telegram: {e}")


async def rodar_monitor(force: bool = False) -> int:
    wl = carregar_watchlist()
    itens = wl.get("itens", {})
    if not itens:
        _log("watchlist vazia")
        return 0

    tnu = _carregar_tnu_client()

    hoje = datetime.now().date()
    a_verificar = []
    for paj, item in itens.items():
        if item.get("status") not in (None, "ativo"):
            continue  # ja transitou ou removido
        if force:
            a_verificar.append(paj)
            continue
        prox = item.get("proxima_verificacao")
        if not prox:
            a_verificar.append(paj)
            continue
        try:
            if datetime.fromisoformat(prox).date() <= hoje:
                a_verificar.append(paj)
        except Exception:
            a_verificar.append(paj)

    _log(f"watchlist: {len(itens)} total, {len(a_verificar)} a verificar agora")

    alertas = []
    for paj in a_verificar:
        item = itens[paj]
        novo = await verificar_paj(paj, item, tnu)
        itens[paj] = novo
        if novo.get("status") == "transitou":
            alertas.append((paj, novo))
        await asyncio.sleep(1)  # rate limit suave

    wl["itens"] = itens
    salvar_watchlist(wl)

    # Envia alerta Telegram se houver transitos novos
    if alertas:
        linhas = [f"<b>Monitor de transito — {len(alertas)} detectado(s)</b>\n"]
        for paj, item in alertas:
            sinal = item.get("sinal_detectado", {})
            linhas.append(
                f"• <b>{paj}</b> ({item.get('cnj', '?')})\n"
                f"  Sinal: <i>{sinal.get('sinal', '?')}</i>\n"
                f"  Finalize o arquivamento."
            )
        enviar_telegram("\n\n".join(linhas))

    _log(f"FIM: {len(a_verificar)} verificados, {len(alertas)} transitou")
    return 0


def listar() -> None:
    wl = carregar_watchlist()
    itens = wl.get("itens", {})
    if not itens:
        print("Watchlist vazia.")
        return
    print(f"Watchlist — {len(itens)} itens")
    print("-" * 80)
    for paj, item in itens.items():
        print(f"{paj:20} [{item.get('status','?')}] CNJ {item.get('cnj','?')}")
        print(f"  motivo: {item.get('motivo','?')}")
        print(f"  adicionado: {item.get('adicionado_em','?')[:10]}")
        print(f"  proxima: {item.get('proxima_verificacao','?')}")
        if item.get("ultimo_erro"):
            print(f"  ERRO: {item['ultimo_erro']}")
        if item.get("status") == "transitou":
            print(f"  TRANSITOU em {item.get('transitou_em', '?')[:10]}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor de transito em julgado")
    parser.add_argument("--list", action="store_true", help="Lista watchlist")
    parser.add_argument("--force", action="store_true", help="Verifica todos, ignora agenda")
    args = parser.parse_args()

    if args.list:
        listar()
        return 0

    return asyncio.run(rodar_monitor(force=args.force))


if __name__ == "__main__":
    sys.exit(main())
