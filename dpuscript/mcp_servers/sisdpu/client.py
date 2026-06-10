"""
Cliente SISDPU via Playwright headless (async).

O SISDPU é um sistema JSF (Java Server Faces) sem API REST.
A interacao é feita via Playwright com Chromium headless,
simulando navegacao e extraindo dados do HTML.
"""

import os
import re
from playwright.async_api import async_playwright, Browser, Page


SISDPU_URL = "https://sisdpu.dpu.def.br/sisdpu"
SISDPU_USER = os.environ.get("SISDPU_USERNAME", "")
SISDPU_PASS = os.environ.get("SISDPU_PASSWORD", "")

_playwright = None
_browser: Browser | None = None
_page: Page | None = None

# JS que espera o PrimeFaces terminar todos os AJAX pendentes.
# Resolve imediatamente se nao houver fila, ou poll a cada 100ms.
_WAIT_PF_AJAX = """
() => new Promise((resolve) => {
    const check = () => {
        if (typeof PrimeFaces === 'undefined'
            || !PrimeFaces.ajax
            || !PrimeFaces.ajax.Queue
            || PrimeFaces.ajax.Queue.isEmpty()) {
            resolve(true);
        } else {
            setTimeout(check, 100);
        }
    };
    check();
})
"""


def _sel(element_id: str) -> str:
    """Gera seletor CSS para IDs JSF (que contem ':')."""
    return f'[id="{element_id}"]'


async def _get_page() -> Page:
    """Retorna a page Playwright, criando browser se necessario."""
    global _playwright, _browser, _page
    if _page is not None:
        try:
            _page.url
            return _page
        except Exception:
            _page = None
            _browser = None

    if _playwright is None:
        _playwright = await async_playwright().start()

    _browser = await _playwright.chromium.launch(headless=True)
    _page = await _browser.new_page(viewport={"width": 1280, "height": 1024})
    return _page


async def _wait_pf_ajax(page: Page, timeout: int = 10000):
    """Espera o PrimeFaces terminar AJAX pendente, com timeout de seguranca."""
    try:
        await page.evaluate(_WAIT_PF_AJAX, timeout=timeout)
    except Exception:
        # Fallback: se PrimeFaces nao estiver disponivel, espera curta
        await page.wait_for_timeout(1000)


async def _login():
    """Faz login no SISDPU."""
    page = await _get_page()
    await page.goto(f"{SISDPU_URL}/login.xhtml", wait_until="domcontentloaded")
    await page.wait_for_selector(_sel("frmLogin:epaj_input_usuario"), timeout=15000)
    await page.fill(_sel("frmLogin:epaj_input_usuario"), SISDPU_USER)
    await page.fill(_sel("frmLogin:epaj_input_senha"), SISDPU_PASS)
    await page.evaluate('PrimeFaces.ab({s:"frmLogin:loginButton",f:"frmLogin"})')
    # Polling robusto — wait_for_url tem comportamento erratico com PrimeFaces
    for _ in range(60):
        await page.wait_for_timeout(1000)
        if 'caixaEntrada' in page.url or 'caixaentrada' in page.url:
            break
    else:
        raise TimeoutError('Login timeout: URL nunca chegou em caixaEntrada apos 60s')


async def _ensure_logged_in():
    """Garante que estamos logados. Refaz login se sessao expirou."""
    global _browser, _page
    page = await _get_page()
    try:
        url = page.url
        if "login" in url or not url.startswith("http"):
            await _login()
            return
        # Testa se a sessao ainda esta viva tentando navegar
        await page.goto(
            f"{SISDPU_URL}/pages/caixaentrada/caixaEntrada.xhtml",
            wait_until="domcontentloaded",
            timeout=10000,
        )
        await page.wait_for_timeout(500)
        current_url = page.url
        if "login" in current_url:
            await _login()
    except Exception:
        # Sessao morta - fecha tudo e recria
        try:
            if _browser:
                await _browser.close()
        except Exception:
            pass
        _browser = None
        _page = None
        await _login()


async def caixa_de_entrada() -> dict:
    """Navega para a caixa de entrada e extrai todos os itens.

    SISDPU pode paginar (rows-per-page default 50). Pega todos via:
    1. Extrai rows visiveis na primeira pagina
    2. Clica next-page enquanto houver e acumula dedup
    """
    await _ensure_logged_in()
    page = await _get_page()
    await page.goto(
        f"{SISDPU_URL}/pages/caixaentrada/caixaEntrada.xhtml",
        wait_until="domcontentloaded",
    )
    await page.wait_for_timeout(2000)
    await _wait_pf_ajax(page, timeout=10000)

    body = await page.inner_text("body")

    JS_EXTRACT_ROWS = """
        () => {
            const tables = document.querySelectorAll('.ui-datatable-data tr, .ui-datalist-content .ui-datalist-item');
            if (tables.length > 0) {
                return Array.from(tables).map(tr => tr.innerText.trim()).filter(t => t.length > 0);
            }
            const allTr = document.querySelectorAll('table tbody tr');
            return Array.from(allTr).map(tr => tr.innerText.trim()).filter(t => t.length > 0);
        }
    """
    JS_EXTRACT_LINKS = """
        () => {
            const anchors = document.querySelectorAll('a[href*="movimenta"], a[href*="processo"], a[onclick*="movimenta"]');
            return Array.from(anchors).map(a => ({
                texto: a.innerText.trim(),
                href: a.getAttribute('href') || '',
                onclick: a.getAttribute('onclick') || ''
            })).filter(l => l.texto.length > 0);
        }
    """

    all_rows: list[str] = []
    all_links: list = []
    seen: set = set()

    rows = await page.evaluate(JS_EXTRACT_ROWS)
    links = await page.evaluate(JS_EXTRACT_LINKS)
    for r in rows:
        if r not in seen:
            seen.add(r)
            all_rows.append(r)
    all_links.extend(links)

    for _ in range(20):  # safeguard 20 paginas
        next_btn = await page.query_selector(".ui-paginator-next:not(.ui-state-disabled)")
        if not next_btn:
            break
        try:
            await next_btn.click()
        except Exception:
            break
        await page.wait_for_timeout(800)
        await _wait_pf_ajax(page, timeout=10000)
        rows = await page.evaluate(JS_EXTRACT_ROWS)
        links = await page.evaluate(JS_EXTRACT_LINKS)
        novos = 0
        for r in rows:
            if r not in seen:
                seen.add(r)
                all_rows.append(r)
                novos += 1
        all_links.extend(links)
        if novos == 0:
            break

    return {
        "url": page.url,
        "itens_tabela": all_rows,
        "links": all_links,
        "texto_pagina": body[:5000],
    }



async def _go_to_search():
    """Navega para a pagina de busca."""
    page = await _get_page()
    await page.goto(
        f"{SISDPU_URL}/pages/atendimento/consultaProcessoSimplificado.xhtml?novaPesquisa=true",
        wait_until="domcontentloaded",
    )
    await page.wait_for_selector(_sel("formulario:numProcesso"), timeout=15000)


async def _submit_and_extract(page: Page, max_paginas: int = 0) -> list[dict]:
    """Clica filtrar, trata marcadores e extrai resultados com paginacao.

    Args:
        page: Pagina Playwright.
        max_paginas: Maximo de paginas a percorrer (0 = todas).
    """
    await page.evaluate('PrimeFaces.ab({s:"formulario:filtrar",f:"formulario",u:"@all"})')
    await _wait_pf_ajax(page, timeout=15000)

    try:
        await page.evaluate('PrimeFaces.ab({s:"formulario:selecionarMarcadores",f:"formulario",u:"@all"})')
        await _wait_pf_ajax(page, timeout=10000)
    except Exception:
        pass

    all_results = await _extract_results(page)

    body = await page.inner_text("body")
    _, total = _parse_pagination(body)
    paginas_total = (total + 9) // 10 if total > 0 else 1
    limite = max_paginas if max_paginas > 0 else paginas_total
    pagina = 1

    while pagina < limite:
        if not await _click_next_page(page):
            break
        pagina += 1
        page_results = await _extract_results(page)
        if not page_results:
            break
        all_results.extend(page_results)

    return all_results


def _parse_pagination(body: str) -> tuple[int, int]:
    """Extrai info de paginacao do texto. Retorna (pagina_atual, total_registros)."""
    m = re.search(r'Página\s*(\d+)\s*-\s*De\s*\d+\s*a\s*\d+\s*\(de\s*(\d+)\)', body)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1, 0


async def _click_next_page(page: Page) -> bool:
    """Clica no botao 'proxima pagina' do paginador PrimeFaces. Retorna False se nao ha mais paginas."""
    try:
        next_btn = page.locator('.ui-paginator-next:not(.ui-state-disabled)').first
        if await next_btn.is_visible(timeout=2000):
            await next_btn.click()
            await _wait_pf_ajax(page, timeout=15000)
            return True
    except Exception:
        pass
    return False


async def _extract_results(page: Page) -> list[dict]:
    """Extrai resultados da tabela de busca do SISDPU (pagina atual)."""
    body = await page.inner_text("body")

    results = []
    blocks = re.split(r'(?=Assistido:\s*CPF/CNPJ:)', body)

    for block in blocks[1:]:
        # Remove texto do paginador que pode vazar nos campos
        block = re.sub(r'Página\s*\d+\s*-\s*De\s*\d+\s*a\s*\d+\s*\(de\s*\d+\)', '', block)

        entry = {}

        m = re.search(r'Assistido:\s*CPF/CNPJ:\s*RG:\s*\n\s*(.+)', block)
        if m:
            name_line = m.group(1).strip()
            entry["assistido"] = name_line.split("\n")[0].strip()

        m = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', block)
        if m:
            entry["cpf"] = m.group(1)

        m = re.search(r'PAJ:\s*(\S+)', block)
        if m:
            entry["paj"] = m.group(1)

        m = re.search(r'Unidade:\s*(.+?)(?:\s*Processo Judicial:|\n)', block)
        if m:
            entry["unidade"] = m.group(1).strip()

        m = re.search(r'Processo Judicial:\s*\n?\s*(\S+)', block)
        if m:
            val = m.group(1).strip()
            if val and val != "Ofício:":
                entry["processo_judicial"] = val

        m = re.search(r'Ofício:\s*(.+?)(?:\n|Reto)', block)
        if m:
            entry["oficio"] = m.group(1).strip()

        m = re.search(r'Pretensão:\s*(.+?)(?:\n|Parte)', block)
        if m:
            entry["pretensao"] = m.group(1).strip()

        partes = re.findall(r'Parte Contrária:\s*(.+)', block)
        if partes:
            entry["parte_contraria"] = "; ".join(p.strip() for p in partes if p.strip())

        if entry.get("assistido") or entry.get("paj"):
            results.append(entry)

    return results


async def buscar_por_nome(nome: str, tipo_busca: str = "CONTEM", max_paginas: int = 0) -> list[dict]:
    """Busca PAJs por nome do assistido."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    tipo_select = page.locator("select:has(option[value='CONTEM'])").first
    await tipo_select.select_option(tipo_busca)
    await page.fill(_sel("formulario:nome"), nome)

    return await _submit_and_extract(page, max_paginas)


async def buscar_por_paj(numero: str, ano: str = "2024", unidade: str = "39") -> list[dict]:
    """Busca PAJ por numero."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    await page.select_option(_sel("formulario:anoProcesso"), ano)
    await page.select_option(_sel("formulario:codigoUnidade"), unidade)
    await _wait_pf_ajax(page, timeout=5000)
    await page.fill(_sel("formulario:numProcesso"), numero)

    return await _submit_and_extract(page)


async def buscar_por_processo_judicial(numero: str) -> list[dict]:
    """Busca PAJ por numero de processo judicial."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    await page.fill(_sel("formulario:numeroProcJudicial"), numero)

    return await _submit_and_extract(page)


async def buscar_por_cpf(cpf: str, max_paginas: int = 0) -> list[dict]:
    """Busca PAJ por CPF do assistido."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    cpf_clean = cpf.replace(".", "").replace("-", "")
    await page.fill(_sel("formulario:cpfCnpjInvalidos"), cpf_clean)

    return await _submit_and_extract(page, max_paginas)


async def detalhes_paj(numero: str, ano: str, unidade: str = "39") -> dict:
    """Busca um PAJ e abre sua pagina de detalhes, extraindo todas as informacoes."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    await page.select_option(_sel("formulario:anoProcesso"), ano)
    await page.select_option(_sel("formulario:codigoUnidade"), unidade)
    await _wait_pf_ajax(page, timeout=5000)
    await page.fill(_sel("formulario:numProcesso"), numero)

    await page.evaluate('PrimeFaces.ab({s:"formulario:filtrar",f:"formulario",u:"@all"})')
    await _wait_pf_ajax(page, timeout=15000)

    try:
        await page.evaluate('PrimeFaces.ab({s:"formulario:selecionarMarcadores",f:"formulario",u:"@all"})')
        await _wait_pf_ajax(page, timeout=10000)
    except Exception:
        pass

    # Clica no primeiro link de resultado (nome do assistido ou link de detalhe)
    link = page.locator('a[href*="movimentaProcesso"], a[href*="detalhe"], a[onclick*="movimenta"]').first
    try:
        await link.click(timeout=5000)
    except Exception:
        # Tenta clicar no primeiro link dentro dos resultados
        first_link = page.locator('.ui-datalist-content a, .ui-datatable-data a').first
        try:
            await first_link.click(timeout=5000)
        except Exception:
            return {"erro": "Nao foi possivel abrir detalhes do PAJ"}

    await _wait_pf_ajax(page, timeout=15000)
    await page.wait_for_timeout(2000)

    # Extrai todo o conteudo de texto da pagina de detalhes
    body = await page.inner_text("body")
    url = page.url

    details: dict = {"url": url}

    # Extrai campos comuns de detalhes do PAJ
    patterns = {
        "assistido": r'(?:Assistido|Nome)[:\s]*([^\n]+)',
        "cpf": r'CPF[:\s]*(\d{3}\.\d{3}\.\d{3}-\d{2})',
        "rg": r'RG[:\s]*([^\n]+)',
        "paj": r'PAJ[:\s]*(\S+)',
        "unidade": r'Unidade[:\s]*([^\n]+)',
        "oficio": r'Ofício[:\s]*([^\n]+)',
        "pretensao": r'Pretensão[:\s]*([^\n]+)',
        "processo_judicial": r'(?:Processo Judicial|Nº Processo)[:\s]*([^\n]+)',
        "parte_contraria": r'Parte Contrária[:\s]*([^\n]+)',
        "situacao": r'Situação[:\s]*([^\n]+)',
        "data_abertura": r'(?:Data de Abertura|Dt\. Abertura)[:\s]*([^\n]+)',
        "data_encerramento": r'(?:Data de Encerramento|Dt\. Encerramento)[:\s]*([^\n]+)',
        "responsavel": r'(?:Responsável|Defensor)[:\s]*([^\n]+)',
        "area": r'Área[:\s]*([^\n]+)',
        "subarea": r'(?:Sub-?[Áá]rea|Subárea)[:\s]*([^\n]+)',
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, body, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val:
                details[key] = val

    # Se nao extraiu quase nada, retorna o texto bruto (truncado)
    if len(details) <= 2:
        details["texto_pagina"] = body[:3000]

    return details


async def listar_oficios() -> list[dict]:
    """Retorna as opcoes disponiveis no dropdown de oficios."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    options = await page.evaluate("""
        () => {
            const sel = document.querySelector('[id="formulario:listaOficios"]');
            if (!sel) return [];
            return Array.from(sel.options).map(o => ({value: o.value, label: o.textContent.trim()}));
        }
    """)
    return [o for o in options if o.get("value")]


async def buscar_por_oficio(oficio_value: str, max_paginas: int = 0) -> list[dict]:
    """Busca PAJs por oficio selecionado."""
    await _ensure_logged_in()
    await _go_to_search()
    page = await _get_page()

    await page.select_option(_sel("formulario:listaOficios"), oficio_value)
    await _wait_pf_ajax(page, timeout=5000)

    return await _submit_and_extract(page, max_paginas)


async def movimentacoes_paj(numero: str, ano: str, unidade: str = "39") -> dict:
    """Retorna dados completos do PAJ incluindo TABELA DE MOVIMENTACOES com URLs.

    Portado do sisdpu_sync.py do projeto ASSISTENTE-JUDICIAL.
    Fluxo: Caixa de Entrada -> clica no TEXTO DO PAJ -> Detalhamento do Processo.
    E' a tela que expoe URL STJ como texto copiavel em cada movimentacao.
    """
    await _ensure_logged_in()
    page = await _get_page()

    await page.goto(
        f"{SISDPU_URL}/pages/caixaentrada/caixaEntrada.xhtml",
        wait_until="domcontentloaded",
    )
    await page.wait_for_timeout(2000)
    await _wait_pf_ajax(page, timeout=10000)

    # Texto do PAJ (formato: ANO/UNIDADE-NUMERO, ex: 2025/039-06569)
    paj_texto = f"{ano}/{unidade.zfill(3)}-{numero}"

    # Clica no link com esse texto na tabela
    clicked = await page.evaluate("""
        (pajTexto) => {
            const links = document.querySelectorAll('a');
            for (const a of links) {
                if (a.textContent.includes(pajTexto)) {
                    a.click();
                    return true;
                }
            }
            return false;
        }
    """, paj_texto)

    if not clicked:
        # Fallback: buscar pelo numero sozinho
        clicked = await page.evaluate("""
            (numero) => {
                const links = document.querySelectorAll('a');
                for (const a of links) {
                    if (a.textContent.includes(numero)) {
                        a.click();
                        return true;
                    }
                }
                return false;
            }
        """, numero)

    if not clicked:
        return {"erro": f"PAJ {paj_texto} nao encontrado na caixa de entrada"}

    await _wait_pf_ajax(page, timeout=15000)
    await page.wait_for_timeout(3000)

    dados = await page.evaluate("""
        () => {
            const r = {};
            const body = document.body.innerText;

            const assistidoMatch = body.match(/Assistido\\(s\\)[\\t\\s]+([A-ZAEIOUCAEIOUAEIOUAOCcAEIOU][A-ZAEIOUCAEIOUAEIOUAOCcAEIOU ]+)/);
            if (assistidoMatch) r.assistido = assistidoMatch[1].trim();

            const pajMatch = body.match(/(\\d{4}\\/\\d{3}-\\d+)\\s*-\\s*PAJ\\s+([^\\n]+)/);
            if (pajMatch) {
                r.paj = pajMatch[1];
                r.status_paj = pajMatch[2].trim();
            }

            const oficioMatch = body.match(/Oficio[\\t\\s]+([^\\n]+)/) ||
                                body.match(/Ofício[\\t\\s]+([^\\n]+)/);
            if (oficioMatch) r.oficio = oficioMatch[1].trim();

            const procMatch = body.match(/(\\d{7}-\\d{2}\\.\\d{4}\\.\\d\\.\\d{2}\\.\\d{4})/);
            if (procMatch) r.processo_judicial = procMatch[1];

            const juizoMatch = body.match(/Juízo\\/Orgão Julgador\\s*\\n\\s*([^\\n]+)/) ||
                               body.match(/Juizo\\/Orgao Julgador\\s*\\n\\s*([^\\n]+)/);
            if (juizoMatch) r.juizo = juizoMatch[1].trim();

            // Tabela de movimentacoes — filtro rigoroso:
            // seq de 1 a 4 digitos (seqs reais vao de 1 a milhares);
            // descarta linhas sem descricao E sem movimentacao (sao de outras tabelas).
            const movs = [];
            const movRows = document.querySelectorAll('table tbody tr');
            for (const tr of movRows) {
                const cells = tr.querySelectorAll('td');
                if (cells.length >= 5) {
                    const seq = (cells[0]?.textContent || '').trim();
                    const dataHora = (cells[2]?.textContent || '').trim();
                    const movimentacao = (cells[3]?.textContent || '').trim();
                    const fases = (cells[4]?.textContent || '').trim();
                    const textoCompleto = cells[5]?.textContent || '';
                    const usuario = (cells[6]?.textContent || '').trim();

                    if (seq && /^\\d{1,4}$/.test(seq) && (textoCompleto.trim() || movimentacao)) {
                        const urls = textoCompleto.match(/https?:\\/\\/[^\\s]+/g) || [];
                        const links_decisao = urls.filter(u =>
                            u.includes('stj.jus.br') ||
                            u.includes('stf.jus.br') ||
                            u.includes('portal.stf') ||
                            u.includes('processo.stj') ||
                            u.includes('eproc') ||
                            u.includes('downloadPeca') ||
                            u.includes('decisao') ||
                            u.includes('documento') ||
                            u.endsWith('.pdf')
                        );
                        movs.push({
                            seq: seq,
                            data: dataHora,
                            movimentacao: movimentacao,
                            fases: fases,
                            descricao: textoCompleto.substring(0, 3000),
                            links_decisao: links_decisao,
                            usuario: usuario
                        });
                    }
                }
            }
            if (movs.length > 0) r.movimentacoes = movs.slice(0, 30);

            return r;
        }
    """)

    if not dados:
        dados = {}
    dados["paj_numero"] = numero
    dados["paj_ano"] = ano
    dados["paj_unidade"] = unidade
    dados["url"] = page.url

    # Consolidar URLs de decisao de todas as movimentacoes (STJ + STF + outros)
    todas_urls = []
    for m in dados.get("movimentacoes", []) or []:
        for u in m.get("links_decisao", []) or []:
            if u not in todas_urls:
                todas_urls.append(u)
    if todas_urls:
        dados["urls_decisoes"] = todas_urls
        # Mantem urls_stj pra compat com codigo antigo
        dados["urls_stj"] = [u for u in todas_urls if "stj.jus.br" in u]

    return dados


async def fechar():
    """Fecha o navegador headless."""
    global _playwright, _browser, _page
    if _browser:
        await _browser.close()
        _browser = None
        _page = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
