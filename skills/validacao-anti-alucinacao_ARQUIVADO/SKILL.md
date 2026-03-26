# SKILL: Validação Anti-Alucinação

## IDENTIDADE

Esta skill é um **checkpoint de controle de qualidade** que atua **OBRIGATORIAMENTE** após a elaboração da peça e **ANTES** da formatação em DOCX/PDF.

Sua função é **combater alucinações**, **verificar citações** e **garantir que toda informação objetiva da peça seja verificável**.

**Versão 3.0:** Suporta o **Banco de Fontes Verificadas** (populado via MCP — BNP + CJF). Quando fornecido via `--banco`, a validação cruza marcadores `[Fxxx]` no texto contra as entradas do Banco, garantindo que TODA citação tenha fonte rastreável.

**Mudança v3.0:** A pesquisa de jurisprudência/precedentes deixou de usar RAG/ChromaDB local e agora é feita via **servidores MCP** (`buscar_precedentes` do BNP e `buscar_jurisprudencia_cjf` do CJF) na etapa de pesquisa jurídica. O Banco de Fontes continua sendo o artefato central — a diferença é como ele é populado.

---

## QUANDO USAR

**SEMPRE** após elaborar qualquer peça jurídica e **ANTES** de chamar `formatar_peca.py`.

Esta skill é **OBRIGATÓRIA** no pipeline de todas as Skills de elaboração de peças (agravo interno, embargos de declaração, memoriais, etc.).

---

## DOIS MODOS DE OPERAÇÃO

### Modo BANCO DE FONTES (recomendado)

Quando o Banco de Fontes Verificadas está disponível (`--banco`):
- Citações com marcador `[Fxxx]` válido no Banco = RISCO ZERO (verificadas)
- Citações sem marcador = RISCO ALTO (removidas)
- Legislação federal conhecida = RISCO ZERO (sem marcador)
- Princípios jurídicos consolidados = RISCO ZERO (sem marcador)
- Gera arquivo `_FONTES.md` com lista de todas as fontes utilizadas e seus métodos de verificação

### Modo LEGADO (sem Banco)

Quando o Banco não está disponível (comportamento original v1.0):
- Verifica citações contra documentos PDF fornecidos
- Classifica risco: ZERO, BAIXO, MÉDIO, ALTO
- Transforma ou remove citações não verificáveis

---

## PIPELINE CORRETO DE ELABORAÇÃO

### Com Banco de Fontes (recomendado)
```
1. Pesquisa Jurídica via MCP (BNP + CJF) → gerar Banco de Fontes Verificadas
2. Elaborar texto da peça com marcadores [Fxxx]
3. CHECKPOINT OBRIGATÓRIO: validacao-anti-alucinacao (com --banco)
4. Formatar peça (formatar_peca.py com --banco)
5. Entregar ao Defensor
```

### Sem Banco (modo legado)
```
1. Elaborar texto da peça (via Skill específica)
2. CHECKPOINT OBRIGATÓRIO: validacao-anti-alucinacao
   (se MCP disponível, usar como verificação auxiliar)
3. Formatar peça (formatar_peca.py)
4. Entregar ao Defensor
```

**JAMAIS pule a etapa de validação!**

---

## O QUE ESTA SKILL FAZ

### 1. **IDENTIFICA CITAÇÕES OBJETIVAS**

Busca no texto da peça:
- Números de processos/julgados (REsp, AgRg, EREsp, PUIL, etc.)
- Nomes de ministros/relatores
- Datas de julgamento/publicação
- Súmulas e teses
- Citações doutrinárias (livros, autores)
- Dados estatísticos
- Normas infralegais (Instruções Normativas, Portarias, etc.)

### 2. **VERIFICA FONTES**

Para cada citação identificada, verifica se há fonte confirmada em:

**a) Banco de Fontes Verificadas (modo preferencial):**
- Marcadores `[Fxxx]` cruzados contra o JSON do Banco
- Fontes do Banco podem ter sido populadas via MCP (campo `origem_mcp`) ou via documentos
- Fontes com `origem_mcp: "bnp-api"` = precedentes vinculantes do BNP/CNJ
- Fontes com `origem_mcp: "cjf-jurisprudencia"` = jurisprudência unificada do CJF

**b) Documentos carregados pelo Defensor:**
- PDFs na pasta `/entrada`
- PDFs anexados na conversa
- Arquivos marcados como "PARADIGMA"

**c) Legislação federal de acesso público:**
- Constituição Federal
- Leis federais (8.212/91, 8.213/91, etc.)
- Decretos regulamentares
- Resoluções do CNJ/CSJT

**d) Verificação auxiliar via MCP (ÚLTIMO RECURSO — economia de tokens):**
- Usar APENAS para citações de origem desconhecida (possíveis alucinações do modelo)
- NUNCA re-consultar MCP para citações que já passaram pelo MCP na pesquisa jurídica ou redação da mesma conversa
- Citações oriundas do Banco (que foi populado via MCP) já têm presunção de veracidade
- Citações que o Claude buscou via MCP durante a redação já têm presunção de veracidade
- Ferramentas: `buscar_precedentes` (BNP) e `buscar_jurisprudencia_cjf` (CJF)
- Se MCP confirma a citação, classificar como RISCO ZERO

**e) Bases públicas verificáveis:**
- Site oficial do STJ/STF/TNU
- Diário Oficial da União
- Planalto (legislação)

### 3. **CLASSIFICA O RISCO**

Para cada citação, atribui um nível de risco:

| Nível | Descrição | Ação |
|-------|-----------|------|
| ✅ **ZERO** | Confirmada nos documentos ou legislação | Manter |
| ⚠️ **BAIXO** | Princípio geral do direito, doutrina consolidada | Converter em argumentação genérica |
| 🔴 **MÉDIO** | Julgado não confirmado, mas plausível | Converter em "entendimento jurisprudencial" sem citação específica |
| 🚨 **ALTO** | Dado específico não verificável | **REMOVER IMEDIATAMENTE** |

### 4. **TRANSFORMA OU REMOVE**

**Estratégias de transformação:**

#### ✅ **Risco ZERO → Manter como está**

```
ORIGINAL:
"Conforme art. 21, §3º, da Lei 8.212/91..."

AÇÃO: Nenhuma (verificável na legislação)
```

#### ⚠️ **Risco BAIXO → Converter em princípio**

```
ORIGINAL:
"Como leciona Anderson Schreiber (2005, p. 50), a vedação ao comportamento contraditório..."

TRANSFORMADO:
"A vedação ao comportamento contraditório (venire contra factum proprium), princípio derivado da boa-fé objetiva, impõe..."
```

#### 🔴 **Risco MÉDIO → Generalizar**

```
ORIGINAL:
"No REsp 1.490.523/SP, o STJ reconheceu que a complementação não gera extemporaneidade..."

TRANSFORMADO:
"A jurisprudência do Superior Tribunal de Justiça tem reconhecido que a complementação de contribuições não configura extemporaneidade, pois o segurado já havia cumprido sua obrigação contributiva..."
```

#### 🚨 **Risco ALTO → Remover**

```
ORIGINAL:
"Segundo pesquisa do IPEA de 2023, 87% dos MEIs..."

AÇÃO: Remover completamente (dado estatístico não verificável)
```

---

## COMO USAR

### Entrada
A skill recebe:
1. **Caminho do arquivo .txt** com o texto da peça elaborada
2. **Lista de documentos fonte** (PDFs carregados pelo Defensor)
3. **Nível de rigor** (padrão: ALTO)

### Processo
1. Lê o arquivo da peça
2. Extrai todas as citações objetivas (regex + NLP)
3. Para cada citação:
   - Busca nos documentos fonte
   - Busca na legislação conhecida
   - Classifica o risco
   - Aplica estratégia de transformação
4. Gera relatório de validação
5. Salva versão limpa da peça

### Saída
1. **Arquivo validado**: `{nome_peca}_VALIDADO.txt`
2. **Relatório de validação**: `{nome_peca}_RELATORIO_VALIDACAO.md`
3. **Status**: APROVADO / APROVADO COM RESSALVAS / REPROVADO

---

## EXEMPLO DE RELATÓRIO

```markdown
# RELATÓRIO DE VALIDAÇÃO ANTI-ALUCINAÇÃO
**Peça:** MEMORIAIS_TEMA_384_TNU_DPU.txt
**Data:** 2026-02-12 15:30
**Status:** ✅ APROVADO COM RESSALVAS

## CITAÇÕES VERIFICADAS (12)
✅ Art. 21, §3º, Lei 8.212/91 → Fonte: Legislação federal
✅ PUIL 5007913-47.2020.4.04.7000 → Fonte: Documento 55_PET1.pdf
✅ Tema 359 da TNU → Fonte: Documento 54_PET1.pdf
...

## CITAÇÕES TRANSFORMADAS (5)
⚠️ Anderson Schreiber (2005) → Convertido em princípio geral da boa-fé
⚠️ "O STJ tem entendido..." → Mantido genérico sem número de processo
...

## CITAÇÕES REMOVIDAS (3)
🚨 REsp 1.490.523/SP → Não confirmado (REMOVIDO)
🚨 AgRg REsp 1.326.913/MG → Não confirmado (REMOVIDO)
🚨 "Segundo o IBGE..." → Dado estatístico não verificável (REMOVIDO)

## RECOMENDAÇÕES
- A peça foi aprovada após remoção de 3 citações não verificáveis
- 5 citações foram convertidas em argumentação genérica
- Nenhum argumento central foi comprometido
- ✅ SEGURO PARA FORMATAÇÃO
```

---

## REGRAS CRÍTICAS

### 🔴 **REGRA 1: PRESUNÇÃO DE ALUCINAÇÃO**
**Toda citação específica é presumida FALSA até prova em contrário.**

- Não confie na existência de julgados apenas pelo número
- Não confie em datas, ministros ou ementas sem confirmação
- Não confie em citações doutrinárias sem o livro em mãos

### 🔴 **REGRA 2: PRESUNÇÃO DE VERACIDADE POR ORIGEM**

Citações têm presunção de veracidade conforme sua origem — NÃO re-verificar via MCP:

| Origem | Presunção | Ação na validação |
|--------|-----------|-------------------|
| Banco de Fontes (marcador [Fxxx] válido) | Verificada | RISCO ZERO — já passou pelo MCP na pesquisa |
| PDFs do Defensor (confirmada no documento) | Verificada | RISCO ZERO — fonte primária |
| MCP na mesma conversa (Claude buscou e usou) | Verificada | RISCO ZERO — não re-consultar MCP |
| Legislação federal conhecida | Verificável | RISCO ZERO — dispensa fonte |
| Princípio jurídico consolidado | Verificável | RISCO ZERO — dispensa fonte |
| Origem desconhecida (possível alucinação) | Suspeita | Verificar via MCP como ÚLTIMO RECURSO |

**Regra de economia:** MCP na validação é acionado APENAS para citações sem origem rastreável. Nunca para re-confirmar o que já foi buscado via MCP na pesquisa ou redação.

### 🔴 **REGRA 3: HIERARQUIA DE FONTES**

1. **Banco de Fontes Verificadas** (máxima confiança — fontes já verificadas na pesquisa jurídica)
2. **Documentos carregados pelo Defensor** (alta confiança)
3. **Precedentes vinculantes via MCP/BNP** (alta confiança — API oficial do CNJ)
4. **Jurisprudência via MCP/CJF** (alta confiança — base unificada oficial)
5. **Legislação federal** (Planalto, DOU)
6. **Sites oficiais** (STJ, STF, TNU — apenas se acessível)
7. **Argumentação genérica** (sem fonte específica)

**JAMAIS aceite:**
- Citações "de segunda mão" (via doutrina)
- Julgados sem inteiro teor acessível e não confirmados via MCP
- Dados estatísticos sem fonte oficial

### 🔴 **REGRA 4: PRESERVAÇÃO DO ARGUMENTO**

Ao transformar/remover citação, **preserve o argumento jurídico**:

**❌ ERRADO:**
```
ORIGINAL: "Como decidiu o STJ no REsp X, a complementação retroage à DER."
TRANSFORMADO: [removido]
```

**✅ CORRETO:**
```
ORIGINAL: "Como decidiu o STJ no REsp X, a complementação retroage à DER."
TRANSFORMADO: "A complementação de contribuições, por sua natureza declaratória, deve produzir efeitos desde a DER, preservando os efeitos da contribuição originária já vertida tempestivamente pelo segurado."
```

### 🔴 **REGRA 5: TRANSPARÊNCIA TOTAL**

O relatório de validação deve ser **TRANSPARENTE**:
- Informar exatamente o que foi removido
- Justificar cada transformação
- Permitir que o Defensor revise as alterações
- Destacar se algum argumento central foi afetado

---

## NÍVEIS DE RIGOR

### **ALTO** (padrão)
- Remove qualquer citação não confirmada
- Converte doutrina em princípios gerais
- Exige fonte explícita para todos os dados

### **MÉDIO**
- Permite jurisprudência consolidada sem citação específica
- Aceita princípios gerais conhecidos
- Exige fonte apenas para dados estatísticos

### **BAIXO** (use apenas se Defensor autorizar)
- Permite citações plausíveis
- Aceita doutrina conhecida
- Remove apenas dados claramente falsos

**SEMPRE use ALTO, salvo instrução expressa do Defensor.**

---

## EXECUÇÃO

### Com Banco de Fontes (recomendado)
```bash
python skills/validacao-anti-alucinacao/validar_peca.py \
  --entrada "saida/minha_peca.txt" \
  --fontes "entrada/*.pdf" \
  --banco "saida/banco_fontes_verificadas.json" \
  --rigor ALTO
```

### Sem Banco (modo legado)
```bash
python skills/validacao-anti-alucinacao/validar_peca.py \
  --entrada "saida/minha_peca.txt" \
  --fontes "entrada/*.pdf" \
  --rigor ALTO
```

### Manual (via Claude)
1. Ler o arquivo da peça
2. Identificar citações objetivas
3. Verificar marcadores [Fxxx] contra o Banco (se disponível)
4. Buscar cada citação nos documentos carregados
5. **Verificação MCP (ÚLTIMO RECURSO):** usar MCP APENAS para citações que NÃO vieram do Banco, NÃO vieram dos PDFs e NÃO foram buscadas via MCP na mesma conversa (possíveis alucinações). Citações já verificadas via MCP na pesquisa/redação NÃO devem ser re-consultadas (economia de tokens).
6. Classificar risco (citações confirmadas via MCP = RISCO ZERO)
7. Aplicar transformações
8. Gerar relatório (+ relatório de fontes no modo Banco)
9. Salvar versão validada

---

## INTEGRAÇÃO COM OUTRAS SKILLS

Todas as Skills de elaboração de peças devem incluir este passo:

**Exemplo: `/skills/stj/agravo-interno/SKILL.md`**

```markdown
## ETAPA 5 — VALIDAÇÃO ANTI-ALUCINAÇÃO (OBRIGATÓRIA)

Após elaborar o texto completo do agravo interno:

1. Salvar em arquivo .txt temporário
2. **EXECUTAR: `/skills/validacao-anti-alucinacao/validar_peca.py`**
3. Revisar o relatório de validação
4. Usar a versão VALIDADA para formatação
5. Seguir para formatação DOCX/PDF

**NÃO pule esta etapa!** A validação garante que nenhuma citação não verificável chegue ao Defensor.
```

---

## CASOS ESPECIAIS

### **Citações de precedentes vinculantes**
- Súmulas do STJ/STF → Sempre verificar redação exata (usar MCP/BNP se Banco indisponível)
- Teses repetitivas → Confirmar número e texto (usar `buscar_precedentes` para validar)
- Precedentes qualificados → Exigir fonte (Banco ou confirmação MCP)

### **Citações de normas infralegais**
- IN INSS → Confirmar número, ano e artigo
- Portarias → Verificar vigência
- Resoluções → Confirmar órgão emissor

### **Citações doutrinárias**
- Transformar em princípio, sempre que possível
- Se indispensável: exigir livro completo ou trecho escaneado
- Preferir legislação/jurisprudência à doutrina

---

## OUTPUT FINAL

A skill sempre gera 3 arquivos (+ 1 no modo Banco):

1. **`{nome}_VALIDADO.txt`** → Texto limpo, pronto para formatação
2. **`{nome}_RELATORIO_VALIDACAO.md`** → Relatório detalhado
3. **`{nome}_BACKUP_ORIGINAL.txt`** → Backup do original (caso Defensor queira revisar)
4. **`{nome}_FONTES.md`** → (apenas modo Banco) Lista de fontes utilizadas com verificação

**SEMPRE use o arquivo `_VALIDADO.txt` para formatar a peça!**

---

## FLUXOGRAMA

```
┌─────────────────────────────┐
│ Peça elaborada (.txt)       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ VALIDAÇÃO ANTI-ALUCINAÇÃO   │
│ (esta skill)                │
└─────────────┬───────────────┘
              │
         ┌────┴────┐
         │ Análise │
         └────┬────┘
              │
    ┌─────────┴─────────┐
    │ Extração citações │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Verificação fonte │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Classificação     │
    │ risco             │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Transformação/    │
    │ Remoção           │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │ Geração relatório │
    └─────────┬─────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3 arquivos gerados:         │
│ - _VALIDADO.txt             │
│ - _RELATORIO_VALIDACAO.md   │
│ - _BACKUP_ORIGINAL.txt      │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ formatar_peca.py            │
│ (usa _VALIDADO.txt)         │
└─────────────────────────────┘
```

---

## RESPONSABILIDADES

### **DO CLAUDE:**
1. Executar a validação SEMPRE antes de formatar
2. Apresentar o relatório ao Defensor
3. Usar APENAS a versão validada para formatação
4. Alertar se algum argumento central foi afetado

### **DO DEFENSOR:**
1. Revisar o relatório de validação
2. Decidir se aceita as transformações
3. Fornecer fontes adicionais, se necessário
4. Autorizar nível de rigor diferente, se aplicável

---

## MENSAGEM PADRÃO AO DEFENSOR

Após executar a validação, SEMPRE apresentar:

```
✅ VALIDAÇÃO ANTI-ALUCINAÇÃO CONCLUÍDA

📋 Relatório completo: saida/{nome}_RELATORIO_VALIDACAO.md

Resumo:
- ✅ {n} citações verificadas (fonte confirmada)
- ⚠️ {n} citações transformadas (convertidas em argumentação genérica)
- 🚨 {n} citações removidas (não verificáveis)

Status: {APROVADO / APROVADO COM RESSALVAS / REPROVADO}

📄 Arquivo validado pronto para formatação:
   saida/{nome}_VALIDADO.txt

Deseja revisar o relatório antes da formatação?
```

---

## MANUTENÇÃO E EVOLUÇÃO

Esta skill deve ser **atualizada periodicamente** com:
- Novos padrões de citação identificados
- Melhorias nos algoritmos de detecção
- Novas fontes verificáveis
- Feedback dos Defensores sobre falsos positivos/negativos

**Versão atual:** 3.0
**Última atualização:** 2026-03-06
**Nota v3.0:** Pesquisa de jurisprudência/precedentes agora via MCP (BNP + CJF). ChromaDB/RAG removidos.
