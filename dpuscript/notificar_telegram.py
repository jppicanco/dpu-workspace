#!/usr/bin/env python3
"""
Envia mensagem via Telegram Bot API.

Uso standalone:
    .venv\\Scripts\\python.exe notificar_telegram.py "Mensagem aqui"
    echo "Mensagem" | .venv\\Scripts\\python.exe notificar_telegram.py

Uso como modulo:
    from notificar_telegram import enviar
    enviar("Pipeline concluido: 5 PAJs processados")

Requer no .env:
    TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
    TELEGRAM_CHAT_ID=123456789
"""

from __future__ import annotations

import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def enviar(mensagem: str, parse_mode: str = "HTML") -> dict:
    """Envia mensagem pro Telegram. Retorna resposta da API ou dict com erro."""
    import httpx

    env = _load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        return {"ok": False, "erro": "TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausente no .env"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = httpx.post(url, json=payload, timeout=15)
        data = resp.json()
        if not data.get("ok"):
            return {"ok": False, "erro": data.get("description", "erro desconhecido")}
        return {"ok": True, "message_id": data["result"]["message_id"]}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


def main() -> int:
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        msg = sys.stdin.read().strip()
    else:
        print("Uso: notificar_telegram.py 'mensagem'", file=sys.stderr)
        return 1

    if not msg:
        print("Mensagem vazia", file=sys.stderr)
        return 1

    result = enviar(msg)
    if result.get("ok"):
        print(f"OK (msg_id={result.get('message_id')})")
        return 0
    else:
        print(f"ERRO: {result.get('erro')}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
