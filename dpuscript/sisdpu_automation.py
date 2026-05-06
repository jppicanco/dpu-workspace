"""
Automação do SISDPU via Playwright.

REGRA DE SEGURANÇA ABSOLUTA:
- Nunca executar sem confirmação explícita do Defensor
- Sempre exibir preview do que será feito antes de qualquer ação
- Sempre aguardar confirmação (Sim/Não) antes de submeter
- Log de cada passo executado

Fluxo implementado: Arquivamento com Vitória (Tipo 3)
Outros fluxos: a implementar conforme mapeamento.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright, Page, BrowserContext

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "eproc_profile"   # mesmo perfil do e-Proc — Edge persistente
SISDPU_URL = "https://sisdpu.dpu.def.br/sisdpu"

# Nome da instância CKEditor na página de movimentação (confirmado via DevTools)
CKEDITOR_INSTANCE = "formHonorario_editorValue"

# ID da unidade COMUNICAÇÃO no dropdown de tramitação
COMUNICACAO_ID = "190"
COMUNICACAO_LABEL = "01. COMUNICACAO"


# ---------------------------------------------------------------------------
# Utilitários de espera (JSF/PrimeFaces usa AJAX extensivo)
# ---------------------------------------------------------------------------

_WAIT_PF_AJAX = """
() => new Promise((resolve) => {
    const check = () => {
        if (typeof PrimeFaces === 'undefined'
                || !PrimeFaces.ajax
                || !PrimeFaces.ajax.Queue
                || PrimeFaces.ajax.Queue.isEmpty()) {
            resolve();
        } else {
            setTimeout(check, 100);
        }
    };
    check();
})
"""


async def _wait_ajax(page: Page) -> None:
    """Aguarda PrimeFaces terminar todos os requests AJAX pendentes."""
    try:
        await page.evaluate(_WAIT_PF_AJAX)
    except Exception:
        await page.wait_for_timeout(800)


async def _wait_nav(page: Page, timeout: int = 15000) -> None:
    """Aguarda navegação + AJAX."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        await page.wait_for_timeout(1500)
    await _wait_ajax(page)


# ---------------------------------------------------------------------------
# Inserção de texto no CKEditor 4
# ---------------------------------------------------------------------------

async def _inserir_texto_editor(page: Page, texto: str, instancia: str = CKEDITOR_INSTANCE) -> None:
    """
    Insere texto no CKEditor 4 via JavaScript.
    Usa setData() — API oficial do CKEditor 4.
    O texto pode conter HTML básico (<p>, <br>) ou texto simples.
    """
    # Converte quebras de linha em parágrafos HTML se o texto for plain text
    if "<p>" not in texto and "<br" not in texto:
        paragrafos = [f"<p>{linha}</p>" for linha in texto.split("\n") if linha.strip()]
        html = "\n".join(paragrafos)
    else:
        html = texto

    await page.evaluate(
        """([instancia, html]) => {
            if (typeof CKEDITOR === 'undefined') {
                throw new Error('CKEditor não encontrado na página');
            }
            const editor = CKEDITOR.instances[instancia];
            if (!editor) {
                // Tenta pegar qualquer instância disponível
                const keys = Object.keys(CKEDITOR.instances);
                if (keys.length === 0) throw new Error('Nenhuma instância CKEditor encontrada');
                CKEDITOR.instances[keys[0]].setData(html);
            } else {
                editor.setData(html);
            }
        }""",
        [instancia, html],
    )
    await page.wait_for_timeout(300)  # CKEditor pode demorar um tick para processar


async def _verificar_texto_editor(page: Page, instancia: str = CKEDITOR_INSTANCE) -> str:
    """Retorna o conteúdo atual do editor (para verificação)."""
    return await page.evaluate(
        """(instancia) => {
            if (typeof CKEDITOR === 'undefined') return '';
            const keys = Object.keys(CKEDITOR.instances);
            const key = CKEDITOR.instances[instancia] ? instancia : keys[0];
            return key ? CKEDITOR.instances[key].getData() : '';
        }""",
        instancia,
    )


# ---------------------------------------------------------------------------
# Helpers de modal
# ---------------------------------------------------------------------------

async def _clicar_modal_btn(page: Page, texto_botao: str, timeout: int = 5000) -> bool:
    """
    Clica em botão dentro de modal/dialog PrimeFaces.
    Retorna True se encontrou e clicou, False se o modal não apareceu.
    """
    try:
        btn = page.locator(f"div.ui-dialog button:has-text('{texto_botao}')").first
        await btn.wait_for(state="visible", timeout=timeout)
        await btn.click()
        await _wait_ajax(page)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Fluxo principal: Arquivamento com Vitória (Tipo 3)
# ---------------------------------------------------------------------------

async def arquivar_vitoria(
    page: Page,
    paj_id: str,
    id_tramite: str,
    texto_despacho: str,
    resumo_tramitacao: str = "Tramitado ao setor de Comunicação para as providências cabíveis.",
    dry_run: bool = True,
) -> dict:
    """
    Executa o fluxo de arquivamento com vitória total na via judicial.

    Args:
        page: Playwright page já autenticada no SISDPU
        paj_id: ID interno do PAJ/atendimento (parâmetro 'id' na URL)
        id_tramite: ID do trâmite corrente (parâmetro 'idTramite' na URL)
        texto_despacho: Texto do despacho (plain text ou HTML)
        resumo_tramitacao: Texto do resumo para a tramitação ao setor Comunicação
        dry_run: Se True, apenas simula (não submete nada). SEMPRE começar com True.

    Returns:
        dict com 'sucesso', 'passos_executados', 'erro' (se houver)
    """
    log: list[str] = []
    url_movimentacao = (
        f"{SISDPU_URL}/pages/movimentacao/movimentaProcesso.xhtml"
        f"?id={paj_id}&idTramite={id_tramite}"
    )

    def _log(msg: str) -> None:
        print(f"  [SISDPU] {msg}")
        log.append(msg)

    try:
        # ------------------------------------------------------------------
        # PASSO 1 — Navegar para a página de movimentação
        # ------------------------------------------------------------------
        _log(f"Navegando para movimentação: PAJ id={paj_id}, tramite={id_tramite}")
        if not dry_run:
            await page.goto(url_movimentacao)
            await _wait_nav(page)
        _log("✓ Página de movimentação carregada")

        # ------------------------------------------------------------------
        # PASSO 2 — Selecionar Fase: "Arquivado. Com vitória total na via judicial"
        # ------------------------------------------------------------------
        _log("Selecionando Fase: 'Arquivado. Com vitória total na via judicial'")
        if not dry_run:
            fase_dropdown = page.locator("select[id*='fase'], .ui-selectonemenu").first
            await fase_dropdown.wait_for(state="visible", timeout=10000)
            # Tenta via select nativo primeiro
            try:
                await fase_dropdown.select_option(label="Arquivado. Com vitória total na via judicial")
            except Exception:
                # PrimeFaces SelectOneMenu — clicar para abrir e depois selecionar item
                await fase_dropdown.click()
                await _wait_ajax(page)
                item = page.locator(
                    "li.ui-selectonemenu-item:has-text('Com vitória total na via judicial')"
                ).first
                await item.click()
            await _wait_ajax(page)
        _log("✓ Fase selecionada")

        # ------------------------------------------------------------------
        # PASSO 3 — Inserir despacho no editor CKEditor
        # ------------------------------------------------------------------
        _log(f"Inserindo despacho no editor (CKEditor, instância: {CKEDITOR_INSTANCE})")
        _log(f"  Prévia do texto ({len(texto_despacho)} chars): {texto_despacho[:80]}...")
        if not dry_run:
            await _inserir_texto_editor(page, texto_despacho)
            conteudo_verificado = await _verificar_texto_editor(page)
            if not conteudo_verificado.strip():
                raise RuntimeError("Editor CKEditor aparenta estar vazio após inserção")
        _log("✓ Despacho inserido no editor")

        # ------------------------------------------------------------------
        # PASSO 4 — Clicar em Movimentar (botão no final da página)
        # ------------------------------------------------------------------
        _log("Clicando em 'Movimentar' (botão de submissão)")
        if not dry_run:
            # O botão correto fica no final da página, dentro do formulário
            btn_movimentar = page.locator(
                "input[value='Movimentar'], button:has-text('Movimentar')"
            ).last  # .last para pegar o de fundo acinzentado (não o do nav superior)
            await btn_movimentar.click()
            await _wait_ajax(page)
        _log("✓ Movimentar clicado")

        # ------------------------------------------------------------------
        # PASSO 5 — Modal Honorários → Não
        # ------------------------------------------------------------------
        _log("Modal 'Cadastrar Honorário?' → clicando Não")
        if not dry_run:
            clicou = await _clicar_modal_btn(page, "Não")
            if not clicou:
                _log("  (modal de honorários não apareceu — pode ser normal)")
            await _wait_ajax(page)
        _log("✓ Honorários: Não")

        # ------------------------------------------------------------------
        # PASSO 6 — Modal Tramitar processo? → Sim
        # ------------------------------------------------------------------
        _log("Modal 'Tramitar processo(s)?' → clicando Sim")
        if not dry_run:
            clicou = await _clicar_modal_btn(page, "Sim")
            if not clicou:
                raise RuntimeError("Modal 'Tramitar processo(s)' não apareceu")
            await _wait_nav(page)
        _log("✓ Tramitar: Sim — indo para página de tramitação")

        # ------------------------------------------------------------------
        # PASSO 7 — Página de Tramitação: selecionar COMUNICAÇÃO
        # ------------------------------------------------------------------
        _log(f"Selecionando destino: '{COMUNICACAO_LABEL}' (Id: {COMUNICACAO_ID})")
        if not dry_run:
            destino_dropdown = page.locator(
                "select[id*='destino'], select[id*='tramite'], .ui-selectonemenu"
            ).first
            await destino_dropdown.wait_for(state="visible", timeout=10000)
            try:
                await destino_dropdown.select_option(value=COMUNICACAO_ID)
            except Exception:
                await destino_dropdown.select_option(label=COMUNICACAO_LABEL)
            await _wait_ajax(page)
        _log(f"✓ Destino selecionado: {COMUNICACAO_LABEL}")

        # ------------------------------------------------------------------
        # PASSO 8 — Inserir resumo na Descrição do Trâmite
        # ------------------------------------------------------------------
        _log(f"Inserindo resumo da tramitação: '{resumo_tramitacao}'")
        if not dry_run:
            # Editor da tramitação — pode ser outro CKEditor ou textarea simples
            try:
                await _inserir_texto_editor(page, resumo_tramitacao)
            except Exception:
                # Fallback: textarea simples
                textarea = page.locator("textarea[id*='descricao'], textarea[id*='resumo']").first
                await textarea.fill(resumo_tramitacao)
            await _wait_ajax(page)
        _log("✓ Resumo da tramitação inserido")

        # ------------------------------------------------------------------
        # PASSO 9 — Clicar Tramitar
        # ------------------------------------------------------------------
        _log("Clicando em 'Tramitar'")
        if not dry_run:
            btn_tramitar = page.locator("input[value='Tramitar'], button:has-text('Tramitar')").first
            await btn_tramitar.click()
            await _wait_ajax(page)
        _log("✓ Tramitar clicado")

        # ------------------------------------------------------------------
        # PASSO 10 — Modal "Movimentar novamente?" → Não
        # ------------------------------------------------------------------
        _log("Modal 'Movimentar novamente?' → clicando Não")
        if not dry_run:
            clicou = await _clicar_modal_btn(page, "Não")
            if not clicou:
                _log("  (modal não apareceu — continuando)")
            await _wait_nav(page)
        _log("✓ Movimentar novamente: Não")

        # ------------------------------------------------------------------
        # PASSO 11 — Voltar ao detalhe do PAJ
        # ------------------------------------------------------------------
        _log("Voltando para o detalhe do PAJ")
        if not dry_run:
            btn_voltar = page.locator("a:has-text('Voltar'), input[value='Voltar']").first
            try:
                await btn_voltar.click()
                await _wait_nav(page)
            except Exception:
                await page.go_back()
                await _wait_nav(page)
        _log("✓ De volta ao detalhe do PAJ")

        # ------------------------------------------------------------------
        # PASSO 12 — Concluir PAJ
        # ------------------------------------------------------------------
        _log("Clicando em 'Concluir PAJ da minha caixa de entrada'")
        if not dry_run:
            btn_concluir = page.locator(
                "input[value*='Concluir PAJ'], button:has-text('Concluir PAJ')"
            ).first
            await btn_concluir.wait_for(state="visible", timeout=10000)
            await btn_concluir.click()
            await _wait_ajax(page)
            await _wait_nav(page)
        _log("✓ PAJ concluído")

        _log("=" * 50)
        _log("FLUXO CONCLUÍDO COM SUCESSO" if not dry_run else "DRY-RUN concluído (nada foi submetido)")

        return {"sucesso": True, "passos_executados": log, "erro": None}

    except Exception as exc:
        _log(f"❌ ERRO: {exc}")
        return {"sucesso": False, "passos_executados": log, "erro": str(exc)}


# ---------------------------------------------------------------------------
# Ponto de entrada para teste manual
# ---------------------------------------------------------------------------

async def _testar_dry_run():
    """Executa um dry-run completo para verificar o fluxo sem submeter nada."""
    print("\n" + "=" * 60)
    print("SISDPU Automation — DRY RUN (nenhuma ação será submetida)")
    print("=" * 60)

    despacho_exemplo = """DESPACHO DE ARQUIVAMENTO POR VITÓRIA

Tomo ciência do acórdão favorável ao assistido. A DPU obteve resultado
favorável no presente incidente. Não há providência jurídica pendente
nesta instância.

Comunique-se o assistido do resultado favorável.

Arquive-se com vitória. Encaminhe-se ao setor de COMUNICAÇÃO."""

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                channel="msedge",
            )
        except Exception as e:
            print(f"ERRO: não conseguiu abrir Edge: {e}")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        resultado = await arquivar_vitoria(
            page=page,
            paj_id="4126422",        # PAJ de exemplo (Therezinha)
            id_tramite="61291193",
            texto_despacho=despacho_exemplo,
            dry_run=True,             # ← NUNCA mudar para False sem revisão humana
        )

        print("\nResultado:", "✓ OK" if resultado["sucesso"] else "❌ ERRO")
        if resultado["erro"]:
            print("Erro:", resultado["erro"])

        await context.close()


if __name__ == "__main__":
    asyncio.run(_testar_dry_run())
