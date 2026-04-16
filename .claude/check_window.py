#!/usr/bin/env python3
"""
Hook SessionStart: verifica se a sessao esta ficando grande.
Injeta aviso no contexto do Claude quando o JSONL passa de 400KB.
"""
import sys
import os
import glob

PROJECT_DIR = r"C:\Users\JP\.claude\projects\E--DPU-dpu-workspace"

def main():
    # Encontra o JSONL mais recente do projeto
    pattern = os.path.join(PROJECT_DIR, "*.jsonl")
    files = glob.glob(pattern)
    if not files:
        sys.exit(0)

    # Ordena por data de modificacao (mais recente primeiro)
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    latest = files[0]
    size_kb = os.path.getsize(latest) / 1024

    # Conta linhas (cada linha = 1 evento)
    try:
        with open(latest, "r", encoding="utf-8", errors="replace") as f:
            lines = sum(1 for _ in f)
    except Exception:
        lines = 0

    # Aviso escalonado
    if size_kb > 800 or lines > 400:
        print(f"[JANELA CRITICA] Sessao atual: {size_kb:.0f}KB / {lines} eventos. "
              f"MUITO GRANDE — sugira imediatamente nova sessao com resumo de estado.")
    elif size_kb > 400 or lines > 200:
        print(f"[JANELA GRANDE] Sessao atual: {size_kb:.0f}KB / {lines} eventos. "
              f"Avise Joao apos o turno atual e ofereça resumo + nova sessao.")
    elif size_kb > 200 or lines > 100:
        print(f"[JANELA MEDIA] Sessao atual: {size_kb:.0f}KB. "
              f"Monitore — proximo aviso em ~{400 - lines} eventos.")
    # Abaixo de 200KB: silencio

if __name__ == "__main__":
    main()
