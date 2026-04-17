"""Cliente autenticado do e-Proc TNU — reusa eproc_state.json do setup_eproc.py.

SEMPRE perfil ASSISTENTE PROCURADOR (só-leitura), usa Edge do Windows (channel=msedge)
para evitar problemas do Chromium do Playwright com antivírus.

Regras:
1. Se eproc_state.json não existe → instrui rodar setup_eproc.py e aborta.
2. Se state existe mas expirou → mesmo comportamento (não tenta brute-force).
3. Playwright carrega o state → sessão autenticada sem pedir 2FA.
4. Se dropdown de perfil aparecer (pouco provável reusando state), exige o perfil configurado em EPROC_PERFIL no .env (ex: ASP<SEU_CPF>).
5. Log de auditoria em dpuscript/logs/eproc-auth.log
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# ----- Constantes -----

EPROC_BASE = "https://eproctnu.cjf.jus.br/eproc"
EPROC_PAINEL_URL = f"{EPROC_BASE}/controlador.php?acao=painel_assistente_procurador_listar&acao_origem=principal"
PERFIL_ASSISTENTE = os.environ.get("EPROC_PERFIL", "")  # ex: ASP<SEU_CPF> — definir no .env

TIMEOUT_NAV = 30000
SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "eproc_profile"  # perfil persistente (criado pelo setup_eproc.py)
LOG_PATH = SCRIPT_DIR / "logs" / "eproc-auth.log"

# ----- Estado global (singleton Playwright) -----

_playwright: Optional[Playwright] = None
_context: Optional[BrowserContext] = None  # persistent context (não há browser separado)
_page: Optional[Page] = None


def _log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def _profile_ok() -> bool:
    return PROFILE_DIR.is_dir() and any(PROFILE_DIR.iterdir())


_headless_mode = True  # inicia em headless; vira False se precisar 2FA interativo
_ja_tentou_reauth = False  # anti-recursão: só 1 reauth interativa por execução


async def _get_context(headless: bool | None = None) -> BrowserContext:
    """Retorna context persistente (perfil completo do Edge).

    Se headless=None, usa _headless_mode global (padrão True).
    Se mudar headless, fecha o context atual e reabre no modo pedido.
    """
    global _playwright, _context, _headless_mode
    modo_pedido = _headless_mode if headless is None else headless

    if _context:
        # Se o contexto está aberto no modo certo, reusa
        if modo_pedido == _headless_mode:
            return _context
        # Modo mudou — fecha e reabre
        try:
            await _context.close()
        except Exception:
            pass
        _context = None

    if not _profile_ok():
        raise RuntimeError(
            f"Perfil e-Proc TNU não encontrado em {PROFILE_DIR}.\n"
            "Rode primeiro: .venv\\Scripts\\python.exe setup_eproc.py"
        )

    if not _playwright:
        _playwright = await async_playwright().start()

    try:
        _context = await _playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=modo_pedido,
            channel="msedge",
            viewport={"width": 1366, "height": 900},
        )
        _headless_mode = modo_pedido
    except Exception as e:
        _log(f"LAUNCH_PERSISTENT_ERRO {e}")
        raise
    return _context


async def _reautenticar_interativo() -> None:
    global _ja_tentou_reauth
    _ja_tentou_reauth = True
    """Abre Edge VISÍVEL pro usuário digitar 2FA. Aguarda chegar no Painel.

    Usado quando o e-Proc pediu 2FA em modo headless. JP vê a janela,
    digita o código, e o script continua assim que detecta o Painel.
    """
    global _page, _context
    _log("REAUTH_INICIO abrindo navegador visivel pro 2FA")

    # Força reopen em headful
    if _context:
        try:
            await _context.close()
        except Exception:
            pass
        _context = None
    _page = None

    context = await _get_context(headless=False)
    page = context.pages[0] if context.pages else await context.new_page()
    _page = page

    # Faz login auto com .env
    usuario = os.environ.get("EPROC_USUARIO", "")
    senha = os.environ.get("EPROC_SENHA", "")
    try:
        await page.goto(f"{EPROC_BASE}/", wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        await page.wait_for_timeout(1000)
        if await _tem_form_login(page):
            await page.fill("#txtUsuario", usuario)
            await page.fill("#pwdSenha", senha)
            await page.click("#sbmEntrar")
    except Exception as e:
        _log(f"REAUTH_FORM_ERRO {e}")

    print()
    print("=" * 70)
    print("[!] e-Proc pediu 2FA. Navegador VISIVEL abriu no seu PC.")
    print("    Digite o codigo do app autenticador na janela,")
    print("    marque 'Nao usar o 2FA neste dispositivo',")
    print("    selecione o perfil ASSISTENTE se aparecer,")
    print("    e aguarde chegar no Painel.")
    print("=" * 70)
    print()

    # Aguarda JP interagir (polling até URL ser do painel autenticado)
    import time as _t
    deadline = _t.monotonic() + 300  # 5min
    ultima_url_mostrada = ""
    while _t.monotonic() < deadline:
        await page.wait_for_timeout(2000)
        url_atual = page.url
        if url_atual != ultima_url_mostrada:
            segs_restantes = int(deadline - _t.monotonic())
            print(f"  [aguardando... {segs_restantes}s] URL: {url_atual[:90]}")
            ultima_url_mostrada = url_atual
        # Critério FORTE: URL contém painel_assistente_procurador_listar ou painel_procurador_listar
        if "painel_assistente_procurador_listar" in url_atual or "painel_procurador_listar" in url_atual:
            _log(f"REAUTH_OK chegou_painel url={url_atual[:100]}")
            print("[OK] Painel detectado - continuando automaticamente")
            break
        # Tenta clicar no perfil ASSISTENTE se tela de seleção aparecer
        try:
            body = await page.inner_text("body", timeout=2000)
            if "Seleção de perfil" in body:
                await page.evaluate(f"""
                    () => {{
                        const perfil = '{PERFIL_ASSISTENTE}';
                        const els = document.querySelectorAll('[onclick*="acaoLogar"]');
                        for (const e of els) {{
                            const ctx = e.closest('tr') || e.parentElement;
                            if (ctx && ctx.textContent && ctx.textContent.includes(perfil)) {{
                                const m = (e.getAttribute('onclick')||'').match(/acaoLogar\\(['"]([^'"]+)['"]\\)/);
                                if (m && typeof window.acaoLogar === 'function') {{
                                    window.acaoLogar(m[1]);
                                    return true;
                                }}
                            }}
                        }}
                    }}
                """)
        except Exception:
            pass
    else:
        _log("REAUTH_TIMEOUT 5min sem chegar no painel")
        raise RuntimeError("Timeout de 5min aguardando login interativo — abortando.")

    # Volta pra headless pra continuar a execução
    _log("REAUTH_OK voltando_pra_headless")
    if _context:
        try:
            await _context.close()
        except Exception:
            pass
        _context = None
    _page = None
    await _get_context(headless=True)


async def _get_page() -> Page:
    global _page
    if _page and not _page.is_closed():
        return _page
    context = await _get_context()
    if context.pages:
        _page = context.pages[0]
    else:
        _page = await context.new_page()
    return _page


async def _esta_no_painel(page: Page) -> bool:
    """True se a página atual é o painel do procurador/assistente (autenticado)."""
    try:
        await page.wait_for_timeout(800)
        url = page.url.lower()
        if "login" in url or "txtusuario" in url:
            return False
        body = await page.inner_text("body", timeout=5000)
        return any(m in body for m in ("Painel do Assistente Procurador", "Painel do Procurador"))
    except Exception:
        return False


async def _tem_form_login(page: Page) -> bool:
    try:
        await page.wait_for_selector("#txtUsuario", timeout=2000)
        return True
    except Exception:
        return False


async def _selecionar_perfil_assistente(page: Page) -> None:
    """Se aparecer tela de seleção de perfil, clica no ASSISTENTE."""
    try:
        await page.wait_for_selector("text=Seleção de perfil", timeout=3000)
    except Exception:
        _log("PERFIL tela_selecao_nao_apareceu")
        return  # Já foi direto pro painel

    _log(f"PERFIL tela_selecao_detectada procurando {PERFIL_ASSISTENTE}")

    # Tenta múltiplas estratégias de click (o HTML pode ser table/div/link)
    estrategias = [
        # Estratégia 1: link/botão com texto do perfil
        f"a:has-text('{PERFIL_ASSISTENTE}')",
        f"button:has-text('{PERFIL_ASSISTENTE}')",
        # Estratégia 2: <tr> contendo o perfil
        f"tr:has-text('{PERFIL_ASSISTENTE}')",
        # Estratégia 3: qualquer <td> com o texto
        f"td:has-text('{PERFIL_ASSISTENTE}')",
        # Estratégia 4: qualquer div clicável
        f"div:has-text('{PERFIL_ASSISTENTE}'):not(:has(div))",
    ]
    clicou = False
    for seletor in estrategias:
        try:
            elem = page.locator(seletor).first
            if await elem.count() > 0:
                _log(f"PERFIL clicando via seletor: {seletor}")
                await elem.click(timeout=3000)
                clicou = True
                break
        except Exception as e:
            _log(f"PERFIL click_falhou seletor={seletor} err={str(e)[:80]}")
            continue

    if not clicou:
        # Fallback: tenta disparar via JS
        _log("PERFIL fallback JS eval")
        try:
            await page.evaluate(f"""
                () => {{
                    const perfil = '{PERFIL_ASSISTENTE}';
                    const els = document.querySelectorAll('a, tr, td, div, span, button');
                    for (const e of els) {{
                        if (e.textContent && e.textContent.trim().includes(perfil)) {{
                            e.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)
            clicou = True
        except Exception as e:
            _log(f"PERFIL fallback_falhou {e}")

    if not clicou:
        raise RuntimeError(
            f"Não consegui clicar no perfil {PERFIL_ASSISTENTE}. Abortando."
        )

    # Aguarda navegação completar
    try:
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_NAV)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    _log(f"PERFIL pos_click url={page.url[:120]}")


async def garantir_logado() -> Page:
    """Retorna page autenticada.

    Fluxo: carrega state → acessa painel. Se redirect pra login, preenche
    user+senha do .env (cookie de dispositivo confiável no state suprime o 2FA).
    """
    page = await _get_page()

    # Tenta acessar o painel direto
    try:
        await page.goto(EPROC_PAINEL_URL, wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
    except Exception as e:
        _log(f"GOTO_ERRO {e}")
    _log(f"DEBUG passo1 url={page.url[:120]}")

    if await _esta_no_painel(page):
        _log("SESSAO_ATIVA reusou cookie de sessao")
        return page

    # Caiu em erro ou redirect — SEMPRE vai pra raiz do e-Proc (mostra form)
    try:
        await page.goto(f"{EPROC_BASE}/", wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        await page.wait_for_timeout(1500)
    except Exception as e:
        _log(f"GOTO_RAIZ_ERRO {e}")
    _log(f"DEBUG passo2 url={page.url[:120]}")

    if not await _tem_form_login(page):
        body = await page.inner_text("body", timeout=3000)
        _log(f"DEBUG sem_form body_start={body[:200].replace(chr(10),'|')}")
        raise RuntimeError(
            "Não achei form de login nem painel. Sessão pode estar corrompida.\n"
            "Rode: .venv\\Scripts\\python.exe setup_eproc.py"
        )

    usuario = os.environ.get("EPROC_USUARIO", "")
    senha = os.environ.get("EPROC_SENHA", "")
    if not usuario or not senha:
        raise RuntimeError("EPROC_USUARIO / EPROC_SENHA ausentes no .env")

    _log("LOGIN_INICIO auto_via_state")
    await page.fill("#txtUsuario", usuario)
    await page.fill("#pwdSenha", senha)

    # Registra handler pra dialogs (caso "Definir usuário padrão" dispare)
    page.on("dialog", lambda d: asyncio.create_task(d.accept()))

    await page.click("#sbmEntrar")

    # Polling rápido: a tela de Seleção de perfil aparece em ~1s mas some em 3-5s
    # (auto-redirect do e-Proc). Preciso clicar ANTES que desapareça.
    import time as _t
    deadline = _t.monotonic() + 20
    ja_selecionou = False
    while _t.monotonic() < deadline:
        try:
            body = await page.inner_text("body", timeout=2000)
        except Exception:
            await page.wait_for_timeout(500)
            continue

        # 2FA? (cookie expirou → reautenticação interativa)
        if "2 fatores" in body.lower() or "autenticação em 2" in body.lower():
            if _ja_tentou_reauth:
                _log("LOGIN_2FA_APOS_REAUTH desistindo")
                raise RuntimeError(
                    "e-Proc pediu 2FA mesmo após reautenticação interativa. "
                    "Sessão/perfil podem estar corrompidos — rode setup_eproc.py"
                )
            _log("LOGIN_PEDIU_2FA acionando reautenticacao interativa")
            await _reautenticar_interativo()
            return await garantir_logado()

        # Erro de credenciais?
        if any(e in body.lower() for e in ("senha inválida", "senha invalida", "usuário inválido")):
            _log("LOGIN_FALHOU credenciais")
            raise RuntimeError("Credenciais e-Proc inválidas — confira .env")

        # Já está no painel? (caso perfil default tenha sido aplicado)
        if any(m in body for m in ("Painel do Assistente", "Painel do Procurador")):
            _log(f"LOGIN_OK direto_no_painel url={page.url[:100]}")
            return page

        # Tela de seleção de perfil? Clica ANTES que some (auto-redirect em ~5s)
        if "Seleção de perfil" in body and not ja_selecionou:
            _log(f"PERFIL tela_detectada url={page.url[:100]}")
            try:
                # Estratégia correta: chamar acaoLogar(HASH) diretamente via JS.
                # O hash é dinâmico (session-specific), extraído do onclick do <tr> do ASSISTENTE.
                resultado = await page.evaluate(f"""
                    () => {{
                        const perfil = '{PERFIL_ASSISTENTE}';
                        // Procura todo elemento com onclick contendo acaoLogar
                        const els = document.querySelectorAll('[onclick*="acaoLogar"]');
                        for (const e of els) {{
                            // Verifica se o contexto (linha/pai) tem o perfil ASSISTENTE
                            const ctx = e.closest('tr') || e.closest('div') || e.parentElement;
                            if (ctx && ctx.textContent && ctx.textContent.includes(perfil)) {{
                                const onclick = e.getAttribute('onclick') || '';
                                const m = onclick.match(/acaoLogar\\(['"]([^'"]+)['"]\\)/);
                                if (m && typeof window.acaoLogar === 'function') {{
                                    window.acaoLogar(m[1]);
                                    return {{ok: true, hash: m[1].substring(0,12) + '...'}};
                                }}
                            }}
                        }}
                        return {{ok: false, reason: 'acaoLogar nao encontrado para ' + perfil}};
                    }}
                """)
                if resultado.get("ok"):
                    ja_selecionou = True
                    _log(f"PERFIL acaoLogar chamada OK hash={resultado.get('hash')}")
                else:
                    _log(f"PERFIL acaoLogar falhou: {resultado.get('reason')}")
                await page.wait_for_timeout(2000)
            except Exception as e:
                _log(f"PERFIL click_erro {e}")

        # Caiu em "sessão encerrada"? Relogin forçado
        if "sess" in body.lower() and ("encerrada" in body.lower() or "nova sess" in body.lower()):
            if ja_selecionou:
                # Já tentamos selecionar e caiu aqui — problema real
                _log(f"SESSAO_ENCERRADA apos_selecao url={page.url[:100]}")
                raise RuntimeError(
                    f"e-Proc encerrou a sessão após seleção de perfil. URL={page.url}\n"
                    "Verifique logs em eproc-auth.log"
                )
            # Senão, tenta relogar mais uma vez
            _log("SESSAO_ENCERRADA antes_selecao reentrando")
            try:
                await page.goto(f"{EPROC_BASE}/", wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
                await page.fill("#txtUsuario", usuario)
                await page.fill("#pwdSenha", senha)
                await page.click("#sbmEntrar")
            except Exception:
                pass

        await page.wait_for_timeout(500)

    _log(f"LOGIN_LOOP_TIMEOUT url={page.url[:120]}")

    # Pós-login pode cair em index.php — vai explicitamente pro painel
    try:
        await page.goto(EPROC_PAINEL_URL, wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
        await page.wait_for_timeout(1500)
    except Exception as e:
        _log(f"GOTO_PAINEL_ERRO {e}")

    url_lower = page.url.lower()
    if not any(k in url_lower for k in ("login", "txtusuario")):
        body = await page.inner_text("body", timeout=5000)
        if any(m in body for m in ("Painel do Assistente", "Painel do Procurador",
                                   "Procurador", "Sair")):
            _log(f"SESSAO_ATIVA url={page.url}")
            return page

    raise RuntimeError(f"Login completou mas não caí no painel (url={page.url}) — ver logs em eproc-auth.log")


async def ir_para_processo(numero_cnj: str) -> Page:
    """Abre a tela do processo pelo número CNJ (apenas dígitos ou formatado)."""
    import re
    digitos = re.sub(r"\D", "", numero_cnj)
    if len(digitos) != 20:
        raise ValueError(f"CNJ inválido (esperados 20 dígitos): {numero_cnj}")

    page = await garantir_logado()
    # URL direta da consulta por número
    url = (
        f"{EPROC_BASE}/controlador.php?acao=processo_consulta_avancada"
        f"&num_processo={digitos}"
    )
    await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_NAV)
    await page.wait_for_timeout(2000)
    return page


async def abrir_processo(numero_cnj: str) -> Page:
    """Abre a tela do processo autenticado e retorna a page."""
    import re
    digitos = re.sub(r"\D", "", numero_cnj)
    if len(digitos) != 20:
        raise ValueError(f"CNJ inválido (esperados 20 dígitos): {numero_cnj}")

    page = await garantir_logado()
    # Usa o campo de busca do topo (funciona independente da URL específica)
    campo = page.locator(
        "input[placeholder*='processo'], input[name*='processo'], input[name*='NumeroUnico']"
    ).first
    if await campo.count() == 0:
        raise RuntimeError("Campo de busca de processo não encontrado no topo")
    await campo.fill(digitos)
    await campo.press("Enter")
    try:
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_NAV)
    except Exception:
        pass
    await page.wait_for_timeout(2000)
    return page


async def listar_documentos_processo(numero_cnj: str) -> list[dict]:
    """Lista TODOS os documentos acessíveis do processo (autenticado).

    Extrai metadados do evento (seq, data, descrição) junto com o link do doc.
    Formato de cada doc:
      - doc_id, evento_id, key, hash, mesmo_grau
      - nome (DESPADEC1, ACORDO1, PET1, etc — nome REAL)
      - evento_numero, evento_data, evento_descricao (do <tr> da tabela)
      - url (pra usar em baixar_documento)
    """
    page = await abrir_processo(numero_cnj)

    docs_raw = await page.evaluate("""
        () => {
            const docs = [];
            // Eventos são linhas <tr> contendo <a href="...acessar_documento...">
            const rows = document.querySelectorAll('tr');
            rows.forEach(tr => {
                const links = tr.querySelectorAll('a[href*="acessar_documento"]');
                if (!links.length) return;
                const cells = tr.querySelectorAll('td');
                // Extrai metadados do evento da linha
                let evento_numero = '', evento_data = '', evento_descricao = '';
                cells.forEach(td => {
                    const txt = (td.textContent || '').trim();
                    if (!evento_numero && /^\\d{1,4}$/.test(txt)) {
                        evento_numero = txt;
                    } else if (!evento_data && /\\d{2}\\/\\d{2}\\/\\d{4}/.test(txt)) {
                        const m = txt.match(/\\d{2}\\/\\d{2}\\/\\d{4}(?: \\d{2}:\\d{2}:\\d{2})?/);
                        if (m) evento_data = m[0];
                    }
                });
                // Descrição do evento = maior cell de texto da linha
                let max = '';
                cells.forEach(td => {
                    const t = (td.textContent || '').trim();
                    if (t.length > max.length) max = t;
                });
                evento_descricao = max.slice(0, 800);

                links.forEach(a => {
                    const href = (a.getAttribute('href') || '').replace(/&amp;/g, '&');
                    const m = href.match(/doc=([^&]+)[\\s\\S]*?evento=([^&]+)[\\s\\S]*?key=([^&]+)(?:[\\s\\S]*?mesmoGrau=([SN]))?[\\s\\S]*?hash=([^&"'\\s<>]+)/);
                    if (!m) return;
                    docs.push({
                        doc_id: m[1],
                        evento_id: m[2],
                        key: m[3],
                        mesmo_grau: m[4] || '',
                        hash: m[5],
                        nome: (a.textContent || '').trim() || ('DOC_' + m[1].slice(0, 8)),
                        evento_numero: evento_numero,
                        evento_data: evento_data,
                        evento_descricao: evento_descricao,
                    });
                });
            });
            return docs;
        }
    """)

    # Dedup por (doc_id, evento_id) + monta url completa
    docs = []
    seen = set()
    for d in docs_raw:
        chave = (d["doc_id"], d["evento_id"])
        if chave in seen:
            continue
        seen.add(chave)
        url = (
            f"{EPROC_BASE}/controlador.php?acao=acessar_documento_implementacao"
            f"&acao_origem=acessar_documento"
            f"&doc={d['doc_id']}"
            f"&evento={d['evento_id']}"
            f"&key={d['key']}"
            f"&hash={d['hash']}"
        )
        if d.get("mesmo_grau"):
            url += f"&mesmoGrau={d['mesmo_grau']}"
        d["url"] = url
        docs.append(d)

    _log(f"LISTAR_DOCS cnj={numero_cnj} encontrados={len(docs)}")
    return docs


_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _ocr_pdf_fitz(pdf_doc) -> str:
    """Roda Tesseract OCR em cada página do PDF (já aberto via fitz).

    Só é chamado quando PyMuPDF não extraiu texto (PDF scan/imagem).
    Retorna o texto concatenado; string vazia se OCR falhar em tudo.
    """
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError as e:
        _log(f"OCR_IMPORT_ERRO {e}")
        return ""
    # Configura o path do binário (nosso shell do Python não tem no PATH)
    if Path(_TESSERACT_PATH).exists():
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH

    paginas_txt: list[str] = []
    for i, page in enumerate(pdf_doc):
        try:
            # Renderiza página como imagem (DPI 200 é bom equilíbrio qualidade/tempo)
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            txt = pytesseract.image_to_string(img, lang="por")
            if txt.strip():
                paginas_txt.append(txt)
        except Exception as e:
            _log(f"OCR_PAGINA_{i}_ERRO {str(e)[:100]}")
            continue
    total = "\n\n".join(paginas_txt)
    _log(f"OCR_CONCLUIDO paginas={len(paginas_txt)}/{len(pdf_doc)} chars={len(total)}")
    return total


async def baixar_pdf_bytes(doc: dict) -> dict:
    """Fase A: SÓ baixa bytes do doc, sem processar.

    Mantém sessão e-Proc aberta o mínimo possível. Processar (extrair texto,
    OCR) fica pra depois, com conexão já fechada.

    Retorna {bytes: bytes, content_type: str, erro: str|None}.
    """
    context = await _get_context()
    url = doc["url"]
    try:
        response = await context.request.get(url, timeout=TIMEOUT_NAV)
        if not response.ok:
            return {"bytes": b"", "content_type": "", "erro": f"HTTP {response.status}"}
        content_type = response.headers.get("content-type", "").lower()
        body = await response.body()
        return {"bytes": body, "content_type": content_type, "erro": None}
    except Exception as e:
        return {"bytes": b"", "content_type": "", "erro": str(e)[:200]}


def _encoding_quebrado(texto: str, threshold: float = 0.04) -> bool:
    """True se >4% dos caracteres alfanuméricos são '?' — sinal de CMap corrompido."""
    if not texto:
        return False
    alfa = sum(1 for c in texto if c.isalpha())
    return alfa > 0 and (texto.count("?") / alfa) > threshold


def extrair_texto_pdf(pdf_bytes: bytes) -> dict:
    """Fase B (local, sem sessão): extrai texto do PDF.

    Tenta PyMuPDF primeiro (~0.1s). Se vazio (PDF scan/imagem) OU se o texto
    tiver encoding corrompido (muitos '?' — CMap inválido), roda Tesseract OCR
    em português. Retorna {conteudo: str, ocr_usado: bool, erro: str|None}.
    """
    try:
        import fitz
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        paginas = []
        for p in pdf_doc:
            t = p.get_text()
            if t.strip():
                paginas.append(t)
        texto = "\n\n".join(paginas)

        if not texto.strip() or _encoding_quebrado(texto):
            motivo = "pdf sem texto extraivel" if not texto.strip() else "encoding corrompido (CMap invalido)"
            _log(f"OCR_ACIONADO {motivo}")
            texto_ocr = _ocr_pdf_fitz(pdf_doc)
            pdf_doc.close()
            if texto_ocr.strip():
                return {"conteudo": texto_ocr, "ocr_usado": True, "erro": None}
            # OCR também falhou — devolve o texto original mesmo que corrompido
            return {"conteudo": texto, "ocr_usado": True, "erro": f"OCR sem resultado ({motivo})"}

        pdf_doc.close()
        return {"conteudo": texto, "ocr_usado": False, "erro": None}
    except Exception as e:
        return {"conteudo": "", "ocr_usado": False, "erro": f"pdf_parse: {e}"}


def extrair_texto_html(html_bytes: bytes) -> dict:
    """Fase B alternativa: extrai texto de HTML (resposta e-Proc não-PDF)."""
    import re as _re
    html = html_bytes.decode("utf-8", errors="replace")
    texto = _re.sub(r'<style[^>]*>.*?</style>', '', html, flags=_re.DOTALL | _re.IGNORECASE)
    texto = _re.sub(r'<script[^>]*>.*?</script>', '', texto, flags=_re.DOTALL | _re.IGNORECASE)
    texto = _re.sub(r'<[^>]+>', ' ', texto)
    texto = _re.sub(r'&nbsp;', ' ', texto)
    texto = _re.sub(r'[ \t]+', ' ', texto)
    texto = _re.sub(r'\n{3,}', '\n\n', texto).strip()
    return {"conteudo": texto, "ocr_usado": False, "erro": None}


async def baixar_documento(doc: dict) -> dict:
    """Compatibilidade: baixa + extrai numa chamada.

    Retorna {conteudo: str, pdf_bytes: bytes | None, erro: str | None}.
    Prefira usar baixar_pdf_bytes + extrair_texto_pdf em 2 fases pra
    liberar sessão e-Proc antes de processar.
    """
    context = await _get_context()
    url = doc["url"]
    try:
        response = await context.request.get(url, timeout=TIMEOUT_NAV)
        if not response.ok:
            return {"conteudo": "", "pdf_bytes": None, "erro": f"HTTP {response.status}"}
        content_type = response.headers.get("content-type", "").lower()
        body = await response.body()

        # PDF direto
        if "pdf" in content_type or body[:4] == b"%PDF":
            try:
                import fitz
                pdf_doc = fitz.open(stream=body, filetype="pdf")
                paginas = []
                for p in pdf_doc:
                    t = p.get_text()
                    if t.strip():
                        paginas.append(t)
                texto = "\n\n".join(paginas)

                # Se extração normal falhou (PDF scan/imagem), roda OCR via Tesseract
                if not texto.strip():
                    _log(f"OCR_ACIONADO pdf sem texto — rodando Tesseract pt-BR")
                    texto_ocr = _ocr_pdf_fitz(pdf_doc)
                    pdf_doc.close()
                    if texto_ocr.strip():
                        return {"conteudo": texto_ocr, "pdf_bytes": body, "erro": None}
                    return {"conteudo": "", "pdf_bytes": body, "erro": "PDF scan sem texto OCR"}

                pdf_doc.close()
                return {"conteudo": texto, "pdf_bytes": body, "erro": None}
            except Exception as e:
                return {"conteudo": "", "pdf_bytes": body, "erro": f"pdf_parse: {e}"}

        # HTML (acessar_documento_implementacao retorna HTML com o doc renderizado)
        html = body.decode("utf-8", errors="replace")
        import re
        texto = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'<script[^>]*>.*?</script>', '', texto, flags=re.DOTALL | re.IGNORECASE)
        texto = re.sub(r'<[^>]+>', ' ', texto)
        texto = re.sub(r'&nbsp;', ' ', texto)
        texto = re.sub(r'[ \t]+', ' ', texto)
        texto = re.sub(r'\n{3,}', '\n\n', texto).strip()
        return {"conteudo": texto, "pdf_bytes": None, "erro": None}
    except Exception as e:
        return {"conteudo": "", "pdf_bytes": None, "erro": str(e)[:200]}


async def fechar():
    global _playwright, _context, _page
    if _context:
        try:
            await _context.close()  # persistent_context salva tudo ao fechar
        except Exception:
            pass
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
    _playwright = _context = _page = None


# ----- CLI de teste -----

async def _test():
    """Testa reuso do state — deve entrar sem pedir 2FA (credenciais do .env)."""
    # Carrega .env
    env_file = SCRIPT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
    try:
        page = await garantir_logado()
        print("[OK] login via perfil persistente - SEM 2FA, SEM credenciais interativas")
        print(f"URL atual: {page.url}")
        print(f"Titulo: {await page.title()}")
        body = await page.inner_text("body")
        linha_painel = [l for l in body.split("\n") if "Painel" in l or "Procurador" in l][:3]
        for l in linha_painel:
            print(f"  | {l.strip()}")
    except Exception as e:
        print(f"[FALHA] {e}")
    finally:
        await fechar()


if __name__ == "__main__":
    asyncio.run(_test())
