# SKILL: Validacao Anti-Alucinacao (v2 Simplificada)

## Objetivo

Verificar, apos a redacao de qualquer peca juridica, se todas as citacoes diretas possuem origem rastreavel. Citacoes sem origem verificavel sao removidas ou substituidas por argumentacao baseada em principios.

**Principio:** Presuncao de veracidade por origem. O que veio de fonte confiavel na sessao e confiavel. O que nao veio de lugar nenhum e potencial alucinacao.

---

## Quando Usar

**APOS** a redacao de qualquer peca juridica (agravo, embargos, memoriais, etc.) e **ANTES** da formatacao DOCX.

Nao se aplica a arquivamentos (Tipo 1 ou 2), que nao contem citacoes diretas de jurisprudencia.

---

## Fontes Confiaveis (presuncao de veracidade)

Citacoes provenientes destas origens NAO precisam de verificacao adicional:

| Origem | Por que e confiavel | Exemplo |
|--------|---------------------|---------|
| Documentos do processo (PDFs) | Pecas oficiais juntadas aos autos | Decisao, acordao, peticao, laudo |
| MCP BNP (`buscar_precedentes`) | API oficial do CNJ — Banco Nacional de Precedentes | Tema 999/STJ, Sumula Vinculante 37 |
| MCP CJF (`buscar_jurisprudencia_cjf`) | Base unificada oficial do CJF | REsp 1.234.567/SP, ementa completa |
| Banco de Fontes Verificadas (JSON) | Compilado pela skill de pesquisa juridica | Qualquer fonte com ID [Fxxx] |
| Legislacao oficial (Planalto) | Texto legal vigente verificado via web | Art. 201, §1o, CF |

**Se a citacao veio de uma dessas origens durante a sessao atual, e confiavel.**

---

## Fontes Suspeitas (potencial alucinacao)

Citacoes que NAO vieram de nenhuma das origens acima sao suspeitas. Exemplos tipicos:

- Numero de processo inventado (REsp, AgRg, PUIL que nao apareceu em MCP nem nos PDFs)
- Nome de ministro/relator associado a julgado inexistente
- Data de julgamento sem correspondencia nos documentos
- Ementa ou trecho de acordao "citado de memoria"
- Dado estatistico sem fonte (ex: "70% dos segurados...")
- Tese atribuida a tema/sumula que nao foi pesquisado

---

## Procedimento

### ETAPA 1 — Inventario de citacoes

Listar TODAS as citacoes diretas presentes na peca redigida. Citacao direta e qualquer referencia especifica a:

- Numero de processo (REsp, AgRg, PUIL, PEDILEF, ARE, etc.)
- Sumula (numerada)
- Tema de repercussao geral ou repetitivo (numerado)
- Nome de ministro/relator vinculado a julgado
- Data de julgamento especifica
- Trecho literal de ementa ou acordao
- Dado estatistico ou numerico com pretensao de precisao
- Doutrina com autor e obra

### ETAPA 2 — Classificacao por origem

Para CADA citacao inventariada, verificar se ela veio de uma fonte confiavel:

```
PARA CADA citacao:
  1. Aparece nos documentos do processo (PDFs lidos nesta sessao)?
     → SIM: VERIFICADA (documento)
  2. Aparece nos resultados de chamada MCP BNP feita nesta sessao?
     → SIM: VERIFICADA (BNP)
  3. Aparece nos resultados de chamada MCP CJF feita nesta sessao?
     → SIM: VERIFICADA (CJF)
  4. Aparece no Banco de Fontes Verificadas (JSON com [Fxxx])?
     → SIM: VERIFICADA (Banco)
  5. E legislacao verificada via Planalto?
     → SIM: VERIFICADA (legislacao)
  6. Nao veio de nenhuma dessas origens?
     → SUSPEITA
```

### ETAPA 3 — Tratamento das citacoes suspeitas

Para cada citacao classificada como SUSPEITA, aplicar UMA das acoes:

| Acao | Quando usar | Exemplo |
|------|-------------|---------|
| **REMOVER** | Citacao especifica (numero, data, relator) sem fonte | "REsp 1.999.999/SP" inventado → deletar |
| **GENERALIZAR** | A tese e valida mas a referencia e duvidosa | "conforme jurisprudencia consolidada do STJ" (sem numero) |
| **PESQUISAR** | A citacao parece real e vale confirmar | Fazer chamada MCP para verificar antes de manter |
| **SUBSTITUIR** | Existe fonte verificada equivalente | Trocar por precedente encontrado via MCP |

**Regra:** Na duvida entre manter e remover, REMOVER. Uma peca sem citacao e melhor que uma peca com citacao falsa.

### ETAPA 4 — Relatorio ao Defensor

Apresentar resultado sucinto:

```
VALIDACAO ANTI-ALUCINACAO

Citacoes verificadas: X
  - [lista com origem de cada uma]

Citacoes suspeitas tratadas: Y
  - [citacao] → [acao tomada: REMOVIDA / GENERALIZADA / PESQUISADA / SUBSTITUIDA]

Citacoes suspeitas mantidas: Z (se houver, com justificativa)
```

Aguardar confirmacao do Defensor antes de prosseguir para formatacao DOCX.

---

## Regras Criticas

### REGRA 1: Presuncao de veracidade por origem
Citacao que veio de MCP ou documento do processo e confiavel — nao re-verificar. Isso economiza tokens e evita falsos positivos.

### REGRA 2: Sem origem = suspeita
Se voce nao consegue apontar DE ONDE veio a citacao (qual PDF, qual chamada MCP, qual entrada do Banco), ela e suspeita. O onus e do sistema provar a origem, nao do Defensor.

### REGRA 3: Legislacao consolidada e segura
Artigos de leis federais amplamente conhecidas (CF, CPC, Lei 8.213/91, etc.) NAO precisam de verificacao MCP — sao conhecimento juridico consolidado. Apenas verificar se o dispositivo citado existe e esta vigente.

### REGRA 4: Principios nao precisam de fonte
Argumentacao por principios juridicos consolidados (contraditorio, ampla defesa, dignidade da pessoa humana, etc.) NAO e citacao direta e NAO precisa de fonte. So precisa de fonte a citacao ESPECIFICA (numero, data, nome, trecho).

### REGRA 5: Transparencia
O Defensor deve saber exatamente o que foi verificado, o que foi removido e por que. Sem decisoes silenciosas.

---

## Integracao no Pipeline

```
Redacao da peca
  ↓
VALIDACAO (esta skill)
  ↓
Formatacao DOCX (formatar_peca.py)
  ↓
Copia para Entrada/XXXXX/
```

A validacao ocorre NO TEXTO MARKDOWN, antes da conversao para DOCX. Alteracoes feitas aqui sao refletidas no documento final.

---

## Output

Esta skill gera:
1. **Peca corrigida** — texto com citacoes suspeitas tratadas
2. **Relatorio de validacao** — apresentado na conversa para revisao do Defensor

---

**Versao:** 2.0
**Data:** 2026-03-09
