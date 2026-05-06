# SISDPU — Mapeamento Visual: Fluxo Arquivamento com Vitória

> Fonte: gravação dubble.so + análise visual das screenshots (17/04/2026)
> Referência para implementação Playwright

---

## Visão Geral do Sistema

- **Tecnologia:** Java Server Faces (JSF) + PrimeFaces — AJAX extensivo
- **URL base:** `https://sisdpu.dpu.def.br/sisdpu`
- **Atenção:** Toda navegação gera AJAX. Nunca avançar sem aguardar `networkidle` ou seletor específico.

---

## URLs do Fluxo

| Tela | URL Pattern |
|------|-------------|
| Caixa de Entrada | `/pages/caixaentrada/caixaEntrada.xhtml` |
| PAJ Detalhe | `/pages/atendimento/detalhamentoProcesso.xhtml?idTramite={idTramite}&caixaEntrada=true&id={id}&tp=D` |
| Movimentação | `/pages/movimentacao/movimentaProcesso.xhtml?id={id}&idTramite={idTramite}` |
| Tramitação | `/pages/tramite/tramitaProcesso.xhtml?caixaEntrada=false&idTramite={idTramite}&ids={id}&id={id}` |
| Histórico Trâmite | `/pages/tramite/historicoTramitacao.xhtml?caixaEntrada=false&idTramite={idTramite}&id={id}` |

**Parâmetros:**
- `id` — ID do atendimento/PAJ
- `idTramite` — ID do trâmite corrente

---

## Fluxo Passo a Passo

### PASSO 1 — Caixa de Entrada

**Tela:** `/pages/caixaentrada/caixaEntrada.xhtml`

**Visual:** lista de PAJs com colunas: Processo, Assistido, Data de Envio, Remetente, Prazo, Descrição.

**Ações:**
1. Clicar em "Data de Envio" para ordenar cronologicamente (mais antigos primeiro = prazos mais curtos)
2. Clicar no **número do PAJ** (link na coluna Processo) para abrir

**⚠️ Atenção:** Pode aparecer pop-up de aviso do sistema antes da caixa. Tratar com `dismiss()` ou `accept()` dependendo do conteúdo.

---

### PASSO 2 — Detalhe do PAJ

**Tela:** `/pages/atendimento/detalhamentoProcesso.xhtml`

**Visual:** barra de navegação superior com links:
```
Peticionar | Arquivos | Movimentar | Tramitar | Marcar Audiência | Retorno | Incluir Assistidos | Incluir Representante | ...
```

Abaixo da barra: seção "Notificações Encerradas" + tabela de movimentações com colunas Data/Hora, Movimentação, Fases, Descrição.

**CRÍTICO — Dois "Movimentar" na página:**
- ✅ **CORRETO:** link "Movimentar" na **barra de navegação superior** (fundo acinzentado/escuro)
- ❌ **ERRADO:** botão "Movimentar" em algum ponto abaixo da página (fundo azulado)
- Clicar sempre no da barra de navegação (o primeiro a aparecer no topo)

**Seletor provável:** `a[href*="movimentaProcesso"]` ou link de texto "Movimentar" dentro do nav superior.

---

### PASSO 3 — Página de Movimentação

**Tela:** `/pages/movimentacao/movimentaProcesso.xhtml`

**Visual:**

**Seção "Movimentação"** (topo):
- Dropdown fixo: `MOVIMENTAÇÃO MANUAL` (não precisa alterar)

**Seção "Fases":**
- Label: `Fase: *`
- Dropdown amarelo: `Selecione...` — **clicar aqui**
- Checkbox: `Todas as fases` (não marcar)

**Opções disponíveis no dropdown de Fase** (lista completa visualizada):
| Texto exibido | Uso |
|---|---|
| Aguardando tramitação judicial/Administrativa | — |
| Arquivado. Inviabilidade recursal | Arquivamento Tipo 1/2 |
| Decurso de prazo | — |
| **Arquivado. Com vitória total na via judicial** | ✅ **Arquivamento Tipo 3** |
| Arquivado. Encaminhamento a outro órgão | — |
| Arquivado. Outros. | — |
| Petição. Recurso | Para recursos |
| Arquivado. Encaminhado a outra unidade da dpu | — |
| Sustentação oral | — |

> O valor interno é `br.gov.dpu.sisdpu.dto.FaseDTO@8b - Id: 4` para vitória total.
> Selecionar por **texto visível**, não pelo value interno.

**Seção "Descrição da Movimentação" (editor de texto):**
- Editor WYSIWYG (CKEditor ou similar) com toolbar completa
- Toolbar: Estilo | Formatado | Fonte | Tamanho | B I U S x₂ x² Ix | links | alinhamento...
- **Colar o despacho aqui** — ver seção "Inserção no Editor" abaixo

**Seção "Defensor":**
- Label: `Indique o Defensor Responsável:`
- Dropdown já pré-selecionado com `DR. JOÃO PAULO GONDIM PICANÇO`
- Não alterar

**Botões no final da página:**
- `Movimentar` (botão azul escuro/navy) ← clicar
- `Voltar`

---

### PASSO 4 — Modal: Honorários

**Tipo:** Modal/Dialog JSF — bloqueia interação

**Visual:**
```
┌─────────────────────────────┐
│  Cadastrar Honorário         │
├─────────────────────────────┤
│ ⚠ Deseja cadastrar honorário?│
│                             │
│   [  Sim  ]   [  Não  ]     │
└─────────────────────────────┘
```

**Ação:** Clicar **Não** — SEMPRE, sem exceção.

---

### PASSO 5 — Modal: Tramitar processo

**Tipo:** Modal/Dialog JSF

**Visual:**
```
┌─────────────────────────────────┐
│  Tramitar processo(s)            │
├─────────────────────────────────┤
│ ⚠ Deseja tramitar este(s)        │
│   processo(s) ?                  │
│                                 │
│   [  Sim  ]   [  Não  ]         │
└─────────────────────────────────┘
```

**Ação para arquivamento com vitória:** Clicar **Sim**
> (Para outros tipos de arquivamento onde não se tramita, pode ser Não — a confirmar nos próximos guias)

---

### PASSO 6 — Página de Tramitação

**Tela:** `/pages/tramite/tramitaProcesso.xhtml`

**Visual:** dropdown de destino com lista de unidades/ofícios da DPU.

**Lista de destinos (parcial visualizada):**
- 01° OFÍCIO SUPERIOR CRIMINAL
- 03° OFÍCIO SUPERIOR CRIMINAL MILITAR
- 05° OFÍCIO SUPERIOR PREVIDENCIÁRIO
- 09° OFÍCIO SUPERIOR CÍVEL
- 10°, 11°, 12°, 13°, 14°, 15° OFÍCIO SUPERIOR CRIMINAL...
- **01. COMUNICACAO** ← destino correto para arquivamento

> Para encontrar "COMUNICACAO": pode ser necessário rolar a lista ou usar o campo de filtro "SELECIONE..." no rodapé do dropdown.

**Seção "Descrição do Trâmite":**
- Editor de texto (menor que o da movimentação)
- Escrever resumo breve da tramitação

**Botão:** `Tramitar`

---

### PASSO 7 — Modal: Movimentar novamente?

**Tipo:** Modal/Dialog JSF (aparece após clicar Tramitar)

**Ação:** Clicar **Não**
> A movimentação já foi feita no início. Não é necessário movimentar de novo.

---

### PASSO 8 — Histórico de Tramitação

**Tela:** `/pages/tramite/historicoTramitacao.xhtml`

**Ação:**
1. Verificar que o popup "Processo(s) Tramitado(s) com sucesso" apareceu
2. Conferir o destino da tramitação na tabela
3. Clicar em **Voltar** (link ou botão na página)

---

### PASSO 9 — Conferência no Detalhe do PAJ

**Tela:** `/pages/atendimento/detalhamentoProcesso.xhtml`

**Ação:**
1. Rolar a página até a seção de movimentações
2. Verificar que a última (ou penúltima) movimentação registrada é a que acabou de ser feita

---

### PASSO 10 — Concluir PAJ

**Visual:** botão proeminente no canto direito da página:
```
[ Concluir PAJ da minha caixa de entrada ]
```
Barra de navegação acima: `... | Gerar Formulário/Arquivos Padrões | Notificar ao Assistido`

**Ação:** Clicar no botão "Concluir PAJ da minha caixa de entrada"

---

### PASSO 11 — Confirmação Final

**Visual:** Popup/mensagem: `Processo(s) concluído(s) com sucesso.`

**Resultado:** Sistema retorna automaticamente para a **Caixa de Entrada**.

> **Nota:** Para arquivamento, o sistema NÃO pergunta sobre "retorno automático" — encerra direto.

---

## Inserção de Texto no Editor WYSIWYG

O editor é um CKEditor incorporado via PrimeFaces. Não aceita `fill()` direto do Playwright.

**Estratégia recomendada:**
```python
# Opção A — via iframe (se o editor estiver em iframe)
frame = page.frame_locator("iframe.cke_wysiwyg_frame")
await frame.locator("body").click()
await page.keyboard.press("Control+a")
await page.keyboard.type(texto_despacho)

# Opção B — via JavaScript (mais robusto para CKEditor)
await page.evaluate("""
    (texto) => {
        // CKEditor 4
        const editorId = Object.keys(CKEDITOR.instances)[0];
        CKEDITOR.instances[editorId].setData(texto);
    }
""", texto_despacho)

# Opção C — via PrimeFaces p:editor (Quill ou similar)
await page.evaluate("""
    (texto) => {
        // Tentar quill
        const editor = document.querySelector('.ql-editor');
        if (editor) { editor.innerHTML = texto; return; }
        // Tentar CKEditor
        if (typeof CKEDITOR !== 'undefined') {
            const id = Object.keys(CKEDITOR.instances)[0];
            CKEDITOR.instances[id].setData(texto);
        }
    }
""", texto_despacho)
```

> **A identificar na próxima sessão de mapeamento:** inspecionar o DOM do editor para confirmar qual biblioteca está sendo usada (CKEditor 4? Quill? TinyMCE?).

---

## Tratamento de AJAX (PrimeFaces)

Após cada ação, aguardar o AJAX completar:

```python
# Helper — aguardar PrimeFaces AJAX
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

async def wait_ajax(page):
    await page.evaluate(_WAIT_PF_AJAX)
```

---

## Fluxo por Tipo de Arquivamento

| Tipo | Fase a Selecionar | Tramitar? | Destino |
|------|-------------------|-----------|---------|
| **Tipo 3 — Vitória** | Arquivado. Com vitória total na via judicial | **Sim** | 01. COMUNICACAO |
| **Tipo 1 — Irrecorrível** | Arquivado. Inviabilidade recursal | A confirmar | A confirmar |
| **Tipo 2 — Inviabilidade** | Arquivado. Inviabilidade recursal | A confirmar | A confirmar |

> Registros dos outros tipos serão adicionados conforme novos guias do dubble.so.

---

## Sequência de Modais (Arquivamento Tipo 3)

```
[Clicar Movimentar]
    ↓
Modal: "Cadastrar Honorário?" → [Não]
    ↓
Modal: "Tramitar processo(s)?" → [Sim]
    ↓
[Página Tramitação — selecionar COMUNICACAO — escrever resumo — Tramitar]
    ↓
Modal: "Deseja movimentar novamente?" → [Não]
    ↓
[Histórico — conferir — Voltar]
    ↓
[PAJ Detalhe — conferir movimentação]
    ↓
[Concluir PAJ da minha caixa de entrada]
    ↓
Popup: "Processo(s) concluído(s) com sucesso."
    ↓
[Caixa de Entrada]
```

---

## Pendências para Próximos Guias

- [ ] Inspeção do DOM do editor (confirmar CKEditor vs outro)
- [ ] Fluxo Arquivamento Tipo 1/2 (inviabilidade recursal) — tramitar ou não?
- [ ] Fluxo quando há prazo (retorno automático)
- [ ] Como o SISDPU trata recursos (Petição. Recurso)
- [ ] ID exato do dropdown "COMUNICACAO" no DOM

---

*Documento gerado em 17/04/2026 com base em gravação dubble.so + análise visual multimodal.*
