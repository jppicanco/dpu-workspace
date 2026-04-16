# Guia: Como consultar processos e documentos da TNU via WebFetch

Este documento explica como acessar processos judiciais e o conteúdo de decisões/despachos
da Turma Nacional de Uniformização (TNU) usando WebFetch, sem necessidade de browser
ou autenticação.

---

## Contexto e motivação

A TNU (Turma Nacional de Uniformização dos Juizados Especiais Federais) usa o sistema
**e-Proc** hospedado no CJF. O sistema tem uma **consulta pública** que não exige login.

### Por que NÃO usar browser (Playwright, Selenium, Chrome MCP)?
- Extremamente lento (cada interação leva segundos)
- Páginas frequentemente dão timeout ou erro de conexão
- Formulários JSF/PrimeFaces são frágeis para automação
- A consulta pública da TNU funciona perfeitamente via HTTP GET direto

### Por que NÃO usar o DataJud?
- O DataJud (API do CNJ) costuma estar **meses desatualizado** para a TNU
- Não traz o conteúdo das decisões, apenas metadados das movimentações
- Útil como fallback para dados básicos, mas não para informação recente

---

## Arquitetura da consulta (3 etapas)

```
┌──────────────────────────────────────────────────────────┐
│ ETAPA 1: Consulta pública do processo                    │
│ URL: processo_seleciona_publica                          │
│ Retorna: dados do processo + lista de eventos            │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ ETAPA 2: Extrair link do documento desejado              │
│ Mesma URL, prompt diferente                              │
│ Retorna: link com doc, evento, key, hash                 │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ ETAPA 3: Acessar conteúdo real do documento              │
│ URL: acessar_documento_implementacao (NÃO _publico!)     │
│ Retorna: texto completo do despacho/decisão/sentença     │
└──────────────────────────────────────────────────────────┘
```

---

## Etapa 1 — Consultar dados do processo

### URL
```
https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo={NUMERO_SEM_PONTUACAO}&acao_origem=processo_consulta_publica&acao_retorno=processo_consulta_publica
```

### Preparação do número
Remover TODA a pontuação do número CNJ:
- `5034182-15.2024.4.02.5101` → `50341821520244025101`

### Prompt sugerido para o WebFetch
```
Extract ALL information about this judicial process: events, movements, decisions,
intimations, parties, class, subject, rapporteur, value. For each event, include
date, description, and any linked document names. Give me everything available.
```

### O que você obtém
- Classe processual (ex: Pedido de Uniformização de Interpretação de Lei)
- Relator (ex: Ministro Reynaldo Soares da Fonseca)
- Partes (requerente, requerido, representantes)
- Assunto (ex: Auxílio-Doença Previdenciário)
- Valor da causa
- Status
- Lista de TODOS os eventos/movimentações com:
  - Número do evento
  - Data/hora
  - Descrição
  - Documentos vinculados (DESPADEC1, ATOORD1, SENT1, etc.)

---

## Etapa 2 — Obter links dos documentos

### URL
Mesma da Etapa 1.

### Prompt sugerido
```
I need to find the URL or link to the document called {NOME_DO_DOCUMENTO} from event {NUMERO}.
Look for any hyperlinks or document viewer links with controlador.php. Search the
entire HTML for links containing "acessar_documento". Give me the complete URL with
all parameters (doc, evento, key, hash).
```

### O que você obtém
Um link relativo no formato:
```
controlador.php?acao=acessar_documento_publico&doc={DOC_ID}&evento={EVENTO_ID}&key={KEY}&hash={HASH}
```

Monte a URL completa:
```
https://eproctnu.cjf.jus.br/eproc/controlador.php?acao=acessar_documento_publico&doc={DOC_ID}&evento={EVENTO_ID}&key={KEY}&hash={HASH}
```

---

## Etapa 3 — Acessar o conteúdo real do documento

### ATENÇÃO: Armadilha importante!

Se você fizer WebFetch direto na URL `acessar_documento_publico`, vai receber
apenas o **template da página** (CSS + JavaScript), NÃO o conteúdo do documento.

O conteúdo real é carregado via **AJAX** pelo JavaScript da página.

### Solução em 2 sub-passos

#### Sub-passo 3a: Descobrir a URL AJAX
Faça WebFetch na URL do documento (`acessar_documento_publico`) com este prompt:

```
Look at the JavaScript code. Find the AJAX call URL that loads the document content
into #divdochtml. What is the full URL pattern with all parameters?
```

Isso vai revelar que a URL AJAX usa `acao=acessar_documento_implementacao` em vez de
`acessar_documento_publico`.

#### Sub-passo 3b: Acessar o conteúdo real
Monte a URL trocando a ação e adicionando parâmetros extras:

```
https://eproctnu.cjf.jus.br/eproc/controlador.php?acao=acessar_documento_implementacao&acao_origem=acessar_documento_publico&doc={DOC_ID}&evento={EVENTO_ID}&key={KEY}&hash={HASH}&nome_documento={NUM_EVENTO}_{TIPO_DOC}&termosPesquisados=
```

**Parâmetros extras em relação à URL original:**
- `acao` muda de `acessar_documento_publico` para `acessar_documento_implementacao`
- Adicionar `acao_origem=acessar_documento_publico`
- Adicionar `nome_documento={NUM_EVENTO}_{TIPO_DOC}` (ex: `4_DESPADEC1`)
- Adicionar `termosPesquisados=` (vazio)

#### Prompt sugerido para extrair o texto
```
Extract the COMPLETE text content of this legal document. Give me every word,
every paragraph, including signatory, date, and verification codes.
```

### O que você obtém
O texto integral do documento judicial (despacho, decisão, sentença, etc.).

---

## Exemplo completo testado

### Processo: 5034182-15.2024.4.02.5101

**Etapa 1** — WebFetch na URL pública:
```
https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50341821520244025101&acao_origem=processo_consulta_publica&acao_retorno=processo_consulta_publica
```
Resultado: Processo é um PUIL, relator Min. Reynaldo Soares da Fonseca, Luciano da Cunha Valle vs INSS, auxílio-doença previdenciário. Evento 4 de 28/03/2026 = DESPADEC1 (vista ao MP).

**Etapa 2** — Segundo WebFetch na mesma URL pedindo o link do DESPADEC1:
```
Link encontrado:
doc=771774698940643659550703996613
evento=771774698940643659550704006579
key=b8172c28536aa534278d5d548d14f367aef3f528d3ee1b2a487f639d3ec6a4ab
hash=035bd29f92cc7aa14fea5913c5a4082b
```

**Etapa 3** — WebFetch na URL AJAX:
```
https://eproctnu.cjf.jus.br/eproc/controlador.php?acao=acessar_documento_implementacao&acao_origem=acessar_documento_publico&doc=771774698940643659550703996613&evento=771774698940643659550704006579&key=b8172c28536aa534278d5d548d14f367aef3f528d3ee1b2a487f639d3ec6a4ab&hash=035bd29f92cc7aa14fea5913c5a4082b&nome_documento=4_DESPADEC1&termosPesquisados=
```
Resultado: Texto completo do despacho — abertura de vista ao MPF nos termos da QO 34/TNU.

---

## Dificuldades encontradas e como foram resolvidas

| Dificuldade | Solução |
|---|---|
| e-Proc TNU via browser dava timeout/erro | Usar WebFetch direto na URL de consulta pública |
| Número do processo não encontrado no TRF2 | O processo na TNU tem jurisdição própria; consultar no e-Proc da TNU, não do TRF |
| DataJud desatualizado (última atualização out/2025 para processo de mar/2026) | Consultar diretamente o e-Proc da TNU via WebFetch |
| URL do documento retorna só CSS/JS, não o conteúdo | Conteúdo é carregado via AJAX; usar `acessar_documento_implementacao` em vez de `acessar_documento_publico` |
| DPU-Digital tem o processo mas documentos são stubs da migração | Ir direto na fonte (e-Proc TNU) |

---

## Tipos de documentos comuns no e-Proc

| Código | Significado |
|---|---|
| DESPADEC | Despacho/Decisão |
| ATOORD | Ato Ordinário |
| SENT | Sentença |
| ACORD | Acórdão |
| PET | Petição |
| CONTRAZ | Contrarrazões |
| PARECER | Parecer (geralmente do MPF) |

---

## Notas para implementação em outro projeto

1. **São necessários no mínimo 2 WebFetch** para consultar o processo (etapas 1+2 podem
   ser combinadas em 1 se o prompt for bom o suficiente). Para acessar o documento,
   são necessários mais 1-2 WebFetch.

2. **Os parâmetros key e hash mudam** a cada consulta. Não é possível cachear os links
   dos documentos — é preciso extraí-los a cada vez.

3. **Não precisa de autenticação**. A consulta pública do e-Proc não exige login.

4. **Funciona para qualquer processo público da TNU**. Processos sigilosos não serão
   acessíveis.

5. **O mesmo padrão provavelmente funciona para outros e-Proc** (TRF1-5), bastando
   trocar o domínio base. Não foi testado ainda.
