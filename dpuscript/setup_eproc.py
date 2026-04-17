#!/usr/bin/env python3
"""
Setup único do e-Proc TNU autenticado.

Roda 1x. Abre o navegador VISÍVEL, o JP faz:
  1. Login (usuário + senha) — pode deixar o script preencher ou fazer manual
  2. Código 2FA do app autenticador
  3. **MARCA A CHECKBOX "Não usar o 2FA neste dispositivo e navegador"**
  4. Seleciona o perfil ASSISTENTE PROCURADOR (ASP<SEU_CPF>)
  5. Pressiona ENTER no terminal — script salva a sessão em eproc_state.json

Depois disso, o preparar_pajs.py pode logar silenciosamente reusando esse state,
até o e-Proc expirar o dispositivo confiável (tipicamente 30-90 dias).

Uso:
    .venv\\Scripts\\python.exe setup_eproc.py
"""

import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"
PROFILE_DIR = SCRIPT_DIR / "eproc_profile"  # diretório persistente do navegador (igual perfil do Edge)
EPROC_BASE = "https://eproctnu.cjf.jus.br/eproc/"


def _carregar_env():
    if not ENV_FILE.exists():
        return {}
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


async def main():
    env = _carregar_env()
    user = env.get("EPROC_USUARIO", "")
    senha = env.get("EPROC_SENHA", "")

    print()
    print("=" * 70)
    print("SETUP e-Proc TNU — sessão autenticada única")
    print("=" * 70)
    print()
    print(f"Usuário configurado no .env: {user[:3]}***{user[-2:] if len(user) > 5 else ''}")
    print(f"Perfil persistente (será criado): {PROFILE_DIR}")
    print()
    print("O que vai acontecer:")
    print("  1. Abre uma janela do Chromium (VISÍVEL)")
    print("  2. Campos de login PRÉ-PREENCHIDOS com .env — você só clica Entrar")
    print("  3. Digite o código 2FA do app autenticador quando pedir")
    print("  4. ⚠️  MARQUE a checkbox 'Não usar o 2FA neste dispositivo e navegador'")
    print(f"  5. Selecione o perfil ASSISTENTE PROCURADOR (ASP<SEU_CPF>)")
    print("  6. Espere chegar no 'Painel do Procurador'")
    print("  7. Volte aqui e pressione ENTER pra salvar a sessão")
    print()
    input("Pressione ENTER pra abrir o navegador...")

    print("[1/4] iniciando Playwright...", flush=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        print(f"[2/4] lançando Edge com perfil persistente em {PROFILE_DIR}...", flush=True)
        try:
            # launch_persistent_context persiste TUDO (cookies, localStorage, IndexedDB, etc)
            # num diretório real, igual o perfil padrão do Edge. Sem state loss.
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                channel="msedge",
                viewport={"width": 1366, "height": 900},
            )
        except Exception as e:
            print(f"ERRO launch Edge persistent: {type(e).__name__}: {e}")
            sys.exit(1)
        print("[3/4] contexto persistente pronto...", flush=True)
        # Usa a página existente ou cria nova
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        browser = None  # launch_persistent_context não tem browser separado

        print(f"[4/4] abrindo {EPROC_BASE} ...", flush=True)
        try:
            await page.goto(EPROC_BASE, wait_until="domcontentloaded")
        except Exception as e:
            print(f"ERRO abrindo página inicial: {e}")
            await browser.close()
            sys.exit(1)

        # Pré-preenche se credenciais estão no .env
        if user and senha:
            try:
                await page.wait_for_selector("#txtUsuario", timeout=8000)
                await page.fill("#txtUsuario", user)
                await page.fill("#pwdSenha", senha)
                print("✓ Campos de login pré-preenchidos. Clique 'Entrar' na janela do navegador.")
            except Exception:
                # Pode já estar logado (se perfil tem sessão válida)
                print("ℹ️ Form de login não apareceu — possivelmente já está logado.")
        else:
            print("⚠️ EPROC_USUARIO/EPROC_SENHA ausentes no .env — faça login manual.")

        print()
        print("=" * 70)
        print("AGUARDANDO VOCÊ FAZER O SETUP COMPLETO NO NAVEGADOR")
        print("=" * 70)
        print()
        print("Passos no navegador:")
        print("  [1] Clicar 'Entrar'")
        print("  [2] Digitar código 2FA do app autenticador")
        print("  [3] ⚠️  MARCAR checkbox 'Não usar o 2FA neste dispositivo e navegador'")
        print("  [4] Selecionar perfil ASSISTENTE PROCURADOR (ASP<SEU_CPF>)")
        print("  [5] Chegar na tela 'Painel do Procurador'")
        print()
        print("Quando estiver no Painel do Procurador, volte aqui.")
        print()
        input("Pressione ENTER quando estiver logado e no painel pra salvar a sessão...")

        # Aguarda estabilização (a página pode estar em meio a refresh/navigation)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(1500)

        # Checagem leve (tolera redirect em andamento)
        url_atual = ""
        titulo = ""
        try:
            url_atual = page.url
            titulo = await page.title()
        except Exception as e:
            print(f"(info: não consegui ler url/title por navegação em andamento — {e})")
            await page.wait_for_timeout(2500)
            try:
                url_atual = page.url
                titulo = await page.title()
            except Exception:
                url_atual = "(desconhecida)"
                titulo = "(desconhecido)"
        print()
        print(f"URL atual: {url_atual}")
        print(f"Título: {titulo}")

        if url_atual not in ("(desconhecida)", "") and (
            "login" in url_atual.lower() or "sbmEntrar" in url_atual
        ):
            print()
            print("⚠️  A URL atual ainda parece ser tela de login.")
            resp = input("    Continuar mesmo assim e salvar o state? (s/N): ").strip().lower()
            if resp != "s":
                print("Abortado — state NÃO salvo.")
                await browser.close()
                sys.exit(2)

        # Persistent context salva TUDO automaticamente quando fechar — só precisa fechar
        print()
        print("=" * 70)
        print(f"✓ Perfil persistido em: {PROFILE_DIR}")
        print(f"  Arquivos: {sum(1 for _ in PROFILE_DIR.rglob('*') if _.is_file())} arquivos")
        print("=" * 70)
        print()
        print("Próximo passo: rode `python eproc_auth_client.py` pra testar")
        print("que o login reusa o perfil sem precisar de 2FA.")
        print()

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
