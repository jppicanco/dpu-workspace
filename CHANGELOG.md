# CHANGELOG — DPU Workspace

Log de alterações do projeto. Cada entrada registra O QUE mudou, ONDE mudou e COMO reverter.

**Backup pré-v2.0:** `D:\DPU\dpu-workspace-BACKUP-2026-02-15`

---

## [v6.4] — 2026-04-30

### Politica de Custo x Beneficio (MAX) consolidada no CLAUDE.md

**Motivacao:** Joao reportou estouro recorrente de quota no plano MAX. A regra de roteamento existente no CLAUDE.md era curta demais e nao orientava qual modelo usar como sessao principal nem em que momento subir para Opus. Sem default explicito, o assistente tendia a manter Opus o tempo todo, queimando cota em tarefas mecanicas.

**Arquivos modificados:**
- `CLAUDE.md` — substituida a linha unica "Roteamento de modelos" por secao completa "Politica de Custo x Beneficio (MAX)" cobrindo: (1) modelo default da sessao = Sonnet 4.6; (2) lista explicita de quando subir para Opus 4.7 e quando ficar em Sonnet; (3) roteamento via subagentes com mapeamento opus/sonnet/haiku; (4) disciplina de contexto (uma sessao por processo, apontar arquivos especificos, pre-converter PDFs avulsos, nao reler PDF se TXT existe).

**Rollback:** `git revert HEAD` — alteracao aditiva e cirurgica, nao remove regras anteriores.

---

## [v6.3] — 2026-04-16

### Arquivamento Tipo 3 — por Vitória

**Motivação:** Nos testes do front-end dpuscript-ui (E:\DPU\dpuscript-ui), o Claude classificou erradamente um caso de acordo homologado e cumprido (PAJ Rita, 2018/039-17434) como "despacho de mero expediente" em vez de "arquivamento por vitória". A skill de arquivamento só previa Tipo 1 (irrecorribilidade) e Tipo 2 (inviabilidade de mérito) — faltava o Tipo 3, muito comum na prática.

**Arquivos modificados:**
- `skills/arquivamento/SKILL.md` — adicionada seção "Tipo 3 — Arquivamento por Vitória" com estrutura, tom, distinção vs Tipos 1/2 e menção opcional a watchlist de trânsito
- `CLAUDE.md` — contexto operacional atualizado para mencionar 3 tipos de arquivamento

**Rollback:** `git revert HEAD` (duas edições cirúrgicas, aditivas, não removem nada).

---

## [v6.2] — 2026-03-13

### Conversor PDF para TXT com OCR seletivo

**Motivacao:** O projeto tinha 3 gargalos na leitura de PDFs: limite de 20 paginas do Read tool, limite de 30 paginas do pesquisar.py, e nenhuma capacidade de OCR para PDFs escaneados. Adaptado a partir de esquema compartilhado por colega Defensor (originalmente voltado para PJe), ajustado para EPROC/STJ.

**Arquivos criados:**

| Arquivo | Descricao |
|---------|-----------|
| `skills/extracao-pdf/converter.py` | Conversor PDF→TXT com OCR seletivo (PyMuPDF + Tesseract) |
| `skills/extracao-pdf/SKILL.md` | Documentacao da skill |

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `skills/pesquisa-juridica/pesquisar.py` | Auto-deteccao de TXT pre-convertido (novo metodo `extrair_texto_txt`, remove limite de 30 paginas quando TXT existe) |
| `CLAUDE.md` | Adicionada regra de conversao para PDFs grandes (>500KB) na etapa de Leitura |

**Dependencias instaladas:**
- `pytesseract` (pip) — wrapper Python para Tesseract
- Tesseract OCR — instalador baixado em `%TEMP%\tesseract-installer.exe` (requer instalacao manual com idioma `por`)

**Rollback:** Remover `skills/extracao-pdf/`, reverter `pesquisar.py` (remover metodo `extrair_texto_txt` e check de `.txt`), reverter linha adicionada no `CLAUDE.md`.

---

## [v6.1] — 2026-03-09

### Nova skill de validacao anti-alucinacao simplificada

**Motivacao:** O validador antigo (extinto na v6.0) era baseado em scripts e regex — complexo e contraproducente com MCPs. A nova versao e um procedimento de checklist sem scripts: apos redigir a peca, o sistema inventaria todas as citacoes diretas, classifica cada uma por origem (documento do processo, MCP BNP, MCP CJF, Banco de Fontes, legislacao) e trata as que nao vieram de nenhuma fonte confiavel (remover, generalizar, pesquisar ou substituir). Presuncao de veracidade por origem: o que veio de MCP ou PDF e confiavel; o que nao veio de lugar nenhum e potencial alucinacao.

**Arquivos criados:**

| Arquivo | Descricao |
|---------|-----------|
| `skills/validacao/SKILL.md` | Skill de validacao anti-alucinacao v2.0 (simplificada, sem scripts) |

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `CLAUDE.md` | Pipeline obrigatorio: adicionada validacao (`/skills/validacao/SKILL.md`) antes da formatacao DOCX |

**Diferenca em relacao ao validador antigo (ARQUIVADO):**
- Sem scripts Python (`validar_peca.py` permanece arquivado)
- Sem regex para extrair citacoes — o proprio Claude inventaria
- Sem classificacao de risco (ZERO/BAIXO/MEDIO/ALTO) — binario: VERIFICADA ou SUSPEITA
- Presuncao de veracidade por origem (MCPs e PDFs sao confiaveis por definicao)
- Relatorio simplificado ao Defensor antes da formatacao

**Rollback:**
1. Deletar `skills/validacao/` (pasta inteira)
2. Em `CLAUDE.md`: remover "validacao anti-alucinacao (`/skills/validacao/SKILL.md`) e depois" do pipeline obrigatorio

---

## [v6.0] — 2026-03-09

### Extincao do validador anti-alucinacao + copia obrigatoria de DOCX/PDF para Entrada

**Motivacao:** O validador anti-alucinacao (`validar_peca.py`) tornou-se contraproducente apos a implementacao dos MCPs (BNP + CJF) na v4.0. O padrao recorrente era: (1) peca cita jurisprudencia verificada via MCP, (2) validador so conhece PDFs do processo como fonte, (3) resultado: remove ou genericiza citacoes corretas, (4) gasto de tokens para rodar, analisar, decidir ignorar, usar original. Com os MCPs do BNP e CJF, as citacoes vem direto das bases oficiais — verificaveis por definicao. O risco residual (modelo inventar citacao sem MCP) e controlado pela regra de ouro do CLAUDE.md.

Adicionalmente, DOCX e PDF agora sao copiados automaticamente para a pasta de entrada do processo (alem de serem salvos em `/saida`), para facilitar o acesso pelo Defensor.

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `CLAUDE.md` | Pipeline: removida validacao obrigatoria; adicionada copia DOCX/PDF para Entrada; secao Fontes Verificaveis reescrita com origens confiaveis (PDFs, BNP, CJF, Planalto) |
| `skills/stj/agravo-interno/SKILL.md` | Removida ETAPA 11 inteira (validacao); etapas renumeradas; adicionado passo de copia para Entrada |
| `skills/memoriais/SKILL.md` | Removida ETAPA 9 (validacao); etapas renumeradas; pipeline simplificado; copia para Entrada |
| `skills/arquivamento/SKILL.md` | Pipeline simplificado (removidos CHECKPOINTs de validacao) |
| `skills/pesquisa-juridica/SKILL.md` | Removida secao "Integracao com Validacao Anti-Alucinacao"; pipeline atualizado (copia para Entrada); referencia ao modo legado atualizada |
| `CHECKLIST_FORMATACAO.md` | Removido CHECKPOINT 1 (validacao); CHECKPOINT 2 renumerado; adicionada verificacao de copia para Entrada; removida referencia a arquivo VALIDADO |
| `.claude/commands/arquivar.md` | Removida etapa de validacao; entrega simplificada em .html |
| `MEMORY.md` | Adicionadas notas sobre extincao do validador e copia obrigatoria |

**Arquivos arquivados (renomeados, NAO deletados):**

| Arquivo | Acao |
|---------|------|
| `skills/validacao-anti-alucinacao/` | Renomeado para `skills/validacao-anti-alucinacao_ARQUIVADO/` |

Conteudo da pasta arquivada: `SKILL.md`, `validar_peca.py`, `README.md`, `APRESENTACAO.md`, `INTEGRACAO_COMPLETA.md`, `EXEMPLO_USO.md`

**Rollback:**
1. Renomear `skills/validacao-anti-alucinacao_ARQUIVADO/` de volta para `skills/validacao-anti-alucinacao/`
2. Em `CLAUDE.md`: restaurar "Pipeline obrigatorio: TODA peca deve passar por validacao anti-alucinacao (`validar_peca.py`) e depois formatacao DOCX"
3. Em `skills/stj/agravo-interno/SKILL.md`: restaurar ETAPA 11 completa (validacao) da versao v5.x
4. Em `skills/memoriais/SKILL.md`: restaurar ETAPA 9 (validacao) da versao v5.x
5. Em `skills/arquivamento/SKILL.md`: restaurar pipeline com CHECKPOINTs da versao v5.x
6. Em `skills/pesquisa-juridica/SKILL.md`: restaurar secao "Integracao com Validacao Anti-Alucinacao" e referencia ao modo legado
7. Em `CHECKLIST_FORMATACAO.md`: restaurar CHECKPOINT 1 (validacao)
8. Em `.claude/commands/arquivar.md`: restaurar etapa 3 (validacao) e etapa 4 (entrega com .txt)
9. Em `MEMORY.md`: remover linhas sobre extincao do validador e copia obrigatoria

---

## [v5.3] — 2026-03-09

### Arquivamentos em HTML (substituindo TXT com markdown)

**Motivacao:** Despachos de arquivamento salvos como .txt com marcadores markdown (##, **) nao renderizam formatacao ao colar no sistema web da DPU. HTML basico resolve: renderiza direto no navegador, peso similar ao TXT.

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `.claude/commands/arquivar.md` | Entrega em .html (mantendo .txt para validacao) |
| `.claude/commands/arquivamento.md` | Entrega em .html |

**Formato:** `<h2>`, `<h3>`, `<p>`, `<b>`, `<i>` — sem CSS, sem `<html>`/`<body>`, apenas fragmento HTML colavel.

**Rollback:** Trocar .html por .txt nos dois commands acima.

---

## [v5.2] — 2026-03-09

### Correcao de leitura de arquivos e caminho do pesquisar.py

**Motivacao:** Dois bugs recorrentes: (1) sistema lia TODOS os arquivos da pasta mesmo quando apontado arquivo especifico, consumindo tokens desnecessariamente; (2) caminho do `pesquisar.py` era adivinhado incorretamente como `skills/extracao-pdf/pesquisar.py` (inexistente).

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `CLAUDE.md` | Leitura condicional (arquivo vs pasta) + caminho completo do pesquisar.py |
| `.claude/commands/arquivar.md` | Leitura condicional |
| `.claude/commands/analisar.md` | Leitura condicional |
| `.claude/commands/arquivamento.md` | Leitura condicional |

**Regra:** Se o Defensor aponta arquivo(s) especifico(s), ler SOMENTE esses. Se aponta pasta, ler todos. Caminho correto: `skills/pesquisa-juridica/pesquisar.py`.

**Rollback:** Restaurar "Ler TODOS os arquivos da pasta" nos 4 arquivos acima.

---

## [v5.1] — 2026-03-06

### Alinhamento da skill anti-alucinacao com sistema MCP

**Motivacao:** Apos migração de ChromaDB/RAG para MCP (BNP + CJF) na v4.0, a SKILL.md da validacao anti-alucinacao permanecia na v2.0 sem referencias ao novo sistema.

**Arquivos alterados:**

| Arquivo | Alteracao |
|---------|-----------|
| `skills/validacao-anti-alucinacao/SKILL.md` | Atualizado de v2.0 para v3.0 |

**O que mudou:**
1. Cabecalho: adicionada nota sobre MCP e remocao do RAG/ChromaDB
2. Secao "Verifica fontes": adicionado Banco de Fontes (item a) e verificacao auxiliar via MCP (item d) com regra de ULTIMO RECURSO
3. Nova REGRA 2 (Presuncao de veracidade por origem): tabela definindo que citacoes vindas do Banco, PDFs ou MCP na mesma conversa NAO devem ser re-verificadas via MCP (economia de tokens)
4. Hierarquia de fontes: adicionados niveis 1 (Banco), 3 (BNP/MCP), 4 (CJF/MCP)
5. Pipeline: ambos os modos (Banco e legado) referenciam MCP
6. Processo manual: passo 5 usa MCP APENAS para citacoes de origem desconhecida (possiveis alucinacoes)
7. Casos especiais: precedentes vinculantes referenciam MCP como fallback
8. Regras renumeradas (1-5). Versao atualizada de 2.0 para 3.0

**Rollback:** Restaurar `SKILL.md` do backup ou reverter para texto anterior (versao 2.0).

---

## [v5.0] — 2026-03-06

### Otimizacao de consumo de tokens — reestruturacao do contexto automatico

**Motivacao:** Estouro recorrente de cota de tokens. Inspirado em tecnica de reducao de contexto (ref: tabnews.com.br/andersonlimadev). Objetivo: reduzir o que carrega automaticamente em cada sessao.

**Resultado:** Reducao de ~570 para ~165 linhas de contexto automatico (~70%).

**Arquivos alterados:**

| Arquivo | De | Para | Economia |
|---------|-----|------|----------|
| `CLAUDE.md` | 418 linhas | ~65 linhas | ~85% |
| `MEMORY.md` | 43 linhas | ~18 linhas | ~58% |
| `settings.json` (global) | 4 plugins | 1 plugin | ~75% |
| `settings.local.json` | 107 linhas | ~25 linhas | ~77% |
| `skills/triagem/SKILL.md` | 77 linhas | ~130 linhas | +53 (recebeu arvore recursal) |

**O que mudou em cada arquivo:**

1. **`CLAUDE.md`** — Removidos: arvore recursal completa (migrada para triagem), detalhes de ETAPAs 1/1.5/1.7 (ja existiam em pesquisa-juridica SKILL.md), pipeline com comandos bash completos (ja existiam nas skills de validacao e formatacao), detalhes de fontes verificaveis (ja existiam em pesquisa-juridica), regras de formatacao detalhadas (ja existiam em formatacao-docx), exemplo de estrutura de marcadores. Mantidos: identidade, contexto, regra de ouro de fontes, fluxo resumido em 3 etapas, regras inviolaveis essenciais.

2. **`skills/triagem/SKILL.md`** — Recebeu a arvore recursal completa (TNU + STJ) que antes estava no CLAUDE.md. Referencia interna atualizada de "consulte a arvore recursal do CLAUDE.md" para "consulte a arvore recursal abaixo".

3. **`MEMORY.md`** — Removidas duplicacoes com CLAUDE.md: "Chamar o Defensor de Joao", "Sistema de Fontes Verificaveis", "Encoding UTF-8", "Skills em /skills/", "Arquivamentos salvar apenas .txt". Mantidos apenas dados unicos: licoes operacionais, identificacao de autoridade na TNU, padroes tecnicos.

4. **`settings.json`** (global) — Desabilitados plugins nao essenciais: `code-simplifier` (para programacao), `claude-code-setup` (raramente usado), `claude-md-management` (raramente usado). Mantido: `skill-creator`.

5. **`settings.local.json`** — Substituidos ~90 comandos one-time especificos por ~15 wildcards genericos (ex: `Bash(cmd //c:*)` substitui dezenas de comandos cmd especificos). Removidos WebFetch de dominios raramente usados.

6. **Smart Dispatch Skill** (NOVO) — Skill global em `~/.claude/skills/smart-dispatch/SKILL.md` para roteamento de modelos: opus para raciocinio juridico (triagem, redacao), sonnet para tarefas padrao (scripts, pesquisa MCP, arquivamento Tipo 1), haiku para operacoes mecanicas (listar/mover arquivos). Referencia breve adicionada ao CLAUDE.md.

**Nao afetados:**
- Nenhum script .py foi modificado
- Nenhuma skill de recurso foi modificada (exceto triagem, que recebeu conteudo)
- Pipeline de validacao + formatacao permanece identico
- Comportamento funcional do sistema e 100% preservado

**Rollback:**
1. Restaurar `CLAUDE.md` da versao v4.0 (copiar do CHANGELOG ou do historico)
2. Em `skills/triagem/SKILL.md`: remover a secao "Arvore Recursal" inteira (do `---` apos Passo 3 ate o `---` antes de Passo 4), restaurar referencia original "consulte a arvore recursal do CLAUDE.md"
3. Restaurar `MEMORY.md` da versao anterior (historico de conversas)
4. Restaurar `settings.json`: adicionar plugins `claude-md-management`, `claude-code-setup`, `code-simplifier`
5. Restaurar `settings.local.json` da versao anterior
6. Deletar `C:\Users\JP\.claude\skills\smart-dispatch\` (pasta inteira)
7. Em `CLAUDE.md`: remover linha "Roteamento de modelos..."

---

## [v4.0] — 2026-03-06

### Substituicao do sistema RAG/ChromaDB por MCP (BNP + CJF)

**Mudanca arquitetural:** O sistema de busca de jurisprudencia baseado em ChromaDB/RAG (embeddings locais + busca vetorial) foi substituido por servidores MCP que acessam diretamente as bases oficiais do Banco Nacional de Precedentes (BNP/CNJ) e da Jurisprudencia Unificada do CJF. Elimina dependencia de ChromaDB, sentence-transformers e torch; nao requer alimentacao manual.

**Arquivos removidos:**
- `skills/jurisprudencia/` (diretorio inteiro) — base RAG local com ChromaDB, scripts de ingestao/busca/update, parsers, config, templates, dados vetoriais
- `.claude/commands/juris.md` (versao RAG) — comando de gerenciamento da base RAG

**Arquivos criados:**
- `.claude/commands/juris.md` (versao MCP) — novo comando /juris para busca no BNP e CJF via MCP (3 modos: BNP, CJF, combinado)

**Arquivos alterados:**
- `CLAUDE.md` — Removidas ETAPA 1.2 (auto-indexacao RAG) e ETAPA 1.5 (busca RAG); adicionada nova ETAPA 1.5 (Pesquisa de Precedentes via MCP com BNP + CJF); pipeline atualizado para substituir "Busca RAG" por "Pesquisa MCP de Precedentes"
- `skills/pesquisa-juridica/SKILL.md` — v1.0 para v2.0: Fases 2 e 3 reescritas para usar ferramentas MCP (BNP `buscar_precedentes` e CJF `buscar_jurisprudencia_cjf`) em vez de pesquisa web manual; adicionado tipo de fonte `precedente_vinculante`; pipeline atualizado para 5 fases
- `skills/validacao-anti-alucinacao/validar_peca.py` — v2.1 para v3.0: removidos parametro --rag, metodos carregar_rag() e verificar_em_rag(), status RAG_VERIFICAR, e secao de verificacao RAG no relatorio

**Servidores MCP instalados (escopo D:/DPU):**
- `bnp-api` (via uvx): buscar_precedentes, gerar_relatorio_precedentes, listar_tipos_precedentes
- `cjf-jurisprudencia` (via uv run): buscar_jurisprudencia_cjf

**Repositorio clonado:**
- `D:/DPU/lista-trf` (GitHub: georgemarmelstein/lista-trf) — servidor CJF em mcp/cjf-jurisprudencia/

**Nao afetados:**
- `skills/pesquisa-juridica/pesquisar.py` — mantido intacto
- `skills/formatacao-docx/formatar_peca.py` — nao afetado
- Banco de Fontes Verificadas (JSON com marcadores [Fxxx]) — mantido como backbone anti-alucinacao

**Rollback:**
1. Restaurar `skills/jurisprudencia/` do backup `D:\DPU\dpu-workspace-BACKUP-2026-02-15` (ou v2.9 do CHANGELOG)
2. Restaurar `.claude/commands/juris.md` (versao RAG) do backup
3. Em `CLAUDE.md`: restaurar ETAPA 1.2 e ETAPA 1.5 (versao RAG); restaurar pipeline
4. Em `validar_peca.py`: restaurar v2.1 (com --rag)
5. Em `skills/pesquisa-juridica/SKILL.md`: restaurar v1.0
6. Remover servidores MCP: editar `C:\Users\JP\.claude.json`, remover entradas `bnp-api` e `cjf-jurisprudencia` do projeto `D:/DPU`
7. Deletar `D:/DPU/lista-trf`

---

## [v3.0] — 2026-02-25

### Comando /juris e auto-indexação de decisões dos processos

**Arquivos criados:**
- `.claude/commands/juris.md` — Comando `/juris` para gerenciar a base RAG (update, add, stats, search, limpar)
- `skills/jurisprudencia/scripts/auto_ingest.py` — Script para indexar automaticamente uma decisão específica; detecta tribunal/tipo automaticamente, copia para a pasta correta e executa ingest

**Arquivos alterados:**
- `CLAUDE.md` — Adicionada ETAPA 1.2: paradigmas indexados automaticamente na base RAG; acórdãos relevantes sugeridos ao Defensor

**Mudança:**
- `/juris` aceita: sem argumento (update geral), arquivo específico (add com auto-detecção), "stats", "buscar [query]", "limpar" (com confirmação)
- `auto_ingest.py` detecta tribunal e tipo pelo nome e conteúdo; cópia sem afetar original em `Entrada/`
- Paradigmas (PARADIGMA no nome) indexados automaticamente ao analisar processo; outros acórdãos relevantes sugeridos ao Defensor

**Rollback:**
- Deletar `.claude/commands/juris.md`
- Deletar `skills/jurisprudencia/scripts/auto_ingest.py`
- Em `CLAUDE.md`: remover ETAPA 1.2 inteira (do título até "### ETAPA 1.5")

---

## [v2.9] — 2026-02-25

### Skill de Jurisprudência RAG — Base vetorial local com busca semântica

**Arquivos criados:**
- `skills/jurisprudencia/SKILL.md` — Documentação e protocolo de uso
- `skills/jurisprudencia/config/config.yaml` — Configurações (modelo embedding, ChromaDB, chunking)
- `skills/jurisprudencia/templates/categorias.json` — Mapeamento de áreas temáticas
- `skills/jurisprudencia/scripts/ingest.py` — Ingestão e indexação de documentos
- `skills/jurisprudencia/scripts/search.py` — Busca semântica CLI
- `skills/jurisprudencia/scripts/update.py` — Atualização incremental
- `skills/jurisprudencia/scripts/parsers/__init__.py` — Factory de parsers
- `skills/jurisprudencia/scripts/parsers/pdf_parser.py` — Parser PDF
- `skills/jurisprudencia/scripts/parsers/html_parser.py` — Parser HTML
- `skills/jurisprudencia/scripts/parsers/txt_parser.py` — Parser TXT
- `skills/jurisprudencia/scripts/parsers/json_parser.py` — Parser JSON
- `skills/jurisprudencia/requirements.txt` — Dependências Python

**Arquivos alterados:**
- `CLAUDE.md` — Adicionada ETAPA 1.5 (busca RAG) no fluxo principal; pipeline atualizado para incluir RAG como etapa 0
- `skills/validacao-anti-alucinacao/validar_peca.py` — v2.1: adicionados parâmetro `--rag`, método `carregar_rag()`, método `verificar_em_rag()`, status `RAG_VERIFICAR` e seção correspondente no relatório

**Mudança:** Implementação completa de RAG local usando ChromaDB + sentence-transformers. Modelo primário: `stjiris/bert-large-portuguese-cased-legal-tsdae-gpl-nli-sts-v0` (BERT legal português). Pasta de fontes: `skills/jurisprudencia/data/sources/` com subpastas por tribunal/tipo. O validador agora aceita `--rag rag_results.json` e sinaliza citações encontradas na base RAG para revisão humana em vez de removê-las automaticamente.

**Dependências instaladas:** chromadb, sentence-transformers, torch, pypdf, beautifulsoup4, lxml, pyyaml

**Rollback:**
- Deletar pasta `skills/jurisprudencia/` inteira
- Em `CLAUDE.md`: remover ETAPA 1.5 (busca RAG) e reverter ETAPA 1.6 para ETAPA 1.5 (pesquisa jurídica); reverter pipeline para versão v2.8
- Em `validar_peca.py`: reverter para v2.0 (remover parâmetro `--rag`, métodos `carregar_rag()` e `verificar_em_rag()`, status `RAG_VERIFICAR` e seção do relatório)

---

## [v2.8] — 2026-02-20

### Suporte a negrito inline (`**texto**`) nas peças jurídicas

**Arquivos alterados:**
- `skills/formatacao-docx/formatar_peca.py`
- `CLAUDE.md`

**Mudança:** Adicionada função `_adicionar_runs_com_negrito()` no formatador. Nos tipos de parágrafo `normal` e `citacao_longa`, o texto é agora parseado para segmentos `**...**`, que recebem `run.bold = True`. Segmentos fora de `**` mantêm o estilo padrão. O CLAUDE.md foi atualizado para autorizar o uso criterioso do marcador `**texto**` (máximo 2–3 destaques por tópico) e remover a proibição anterior.

**Rollback:**
- Em `formatar_peca.py`: remover a função `_adicionar_runs_com_negrito()` e substituir as duas chamadas nos blocos `citacao_longa` e `else: # normal` pelo `add_run(texto)` original (sem parsing de `**`)
- Em `CLAUDE.md`: substituir o item 1 da lista de marcadores pela versão anterior (sem `**texto**`) e o item 2 (negrito inline) pelo antigo item 3 com a proibição de Markdown

---

## [v2.7] — 2026-02-20

### Correção de dois bugs na pipeline de validação

**Bug 1 — `pesquisar.py`: diretório passado em `--fontes` causava `Permission denied`**

Arquivo: `skills/pesquisa-juridica/pesquisar.py`, método `processar_documentos()`.

O loop de expansão de argumentos `--fontes` não tratava o caso em que o argumento era um diretório — passava o path do diretório direto para `extrair_texto_pdf()`, que falhava com `Permission denied`. Corrigido adicionando `p.is_dir()` antes de verificar wildcard: se for diretório, expande todos os `*.pdf`/`*.PDF` dentro dele.

Rollback: remover o bloco `if p.is_dir():` e seu conteúdo (3 linhas), mantendo apenas `if '*' in pattern:`.

---

**Bug 2 — `validar_peca.py`: "Tema 27/STF" e "Tema 122/TNU" transformados indevidamente**

Arquivo: `skills/validacao-anti-alucinacao/validar_peca.py`, método `verificar_em_fontes()`.

A busca por números usava `r'\d{5,}'` (5+ dígitos), excluindo números curtos como "27" e "122" usados em Temas e Súmulas. A busca literal também falhava porque o PDF continha quebras de linha que impediam o match. Corrigido: adicionada busca específica para padrões `Tema` e `Súmula` usando regex `r'(?:Tema|Súmula)\s+<numero>'` no conteúdo dos documentos.

Rollback: substituir o método `verificar_em_fontes()` pela versão anterior (apenas `numeros_citacao = re.findall(r'\d{5,}', citacao)`, sem o bloco de busca específica para Temas/Súmulas).

---

## [v2.6] — 2026-02-20

### Critério ampliado para ED contra decisão do Presidente da TNU

**Arquivo:** `skills/tnu/embargos-declaracao/SKILL.md`

**Mudança:** ETAPA 1 foi reestruturada em dois subitens (1.1 e 1.2). O subitem 1.1 introduz critério diferenciado para análise de cabimento conforme a autoridade prolautora. Para decisões do Presidente da TNU (irrecorríveis), a análise é mais maleável: compara o PU com a decisão, verifica se argumentos centrais foram ignorados ou se a jurisprudência foi aplicada mecanicamente, e orienta a buscar o vício formal (omissão/obscuridade) que acomoda a injustiça material. Para decisões do Relator e acórdãos, mantém-se o critério conservador original.

**Rollback:** Substituir a ETAPA 1 pelo texto original (único bloco sem subdivisão em 1.1 e 1.2), que começava diretamente em "Analise a decisão embargada e identifique especificamente".

---

## [v2.5] — 2026-02-20

### Migração PyPDF2 → pypdf

**Contexto:** PyPDF2 foi descontinuado pelos autores em favor do `pypdf` (sucessor oficial).

**A — `pesquisar.py`** (`skills/pesquisa-juridica/pesquisar.py`)
- `import PyPDF2` → `import pypdf`
- `PyPDF2.PdfReader` → `pypdf.PdfReader`
- Mensagem de ImportError atualizada

**B — `validar_peca.py`** (`skills/validacao-anti-alucinacao/validar_peca.py`)
- `import PyPDF2` → `import pypdf`
- `PyPDF2.PdfReader` → `pypdf.PdfReader`
- Mensagem de ImportError atualizada

### Arquivos modificados
| Arquivo | Alteração |
|---------|-----------|
| `skills/pesquisa-juridica/pesquisar.py` | PyPDF2 → pypdf |
| `skills/validacao-anti-alucinacao/validar_peca.py` | PyPDF2 → pypdf |

### Como reverter
- Substituir `import pypdf` por `import PyPDF2` e `pypdf.PdfReader` por `PyPDF2.PdfReader` nos dois arquivos
- `PyPDF2 3.0.1` ainda está instalado no ambiente

---

## [v2.4] — 2026-02-20

### Melhorias de performance e robustez

**A — LEGISLACAO_CONHECIDA expandida** (`validar_peca.py`)
- Adicionadas 18 leis previdenciárias, processuais e de direitos fundamentais de uso frequente
- Leis adicionadas: 9.784/99, 10.259/01, 9.099/95, 13.105/15, 8.742/93, 8.036/90, 1.060/50, 8.078/90, 8.080/90, 20.910/32, 9.469/97, 6.015/73, 10.666/03, 10.741/03, LC 142/2013

**B — `--fontes` aceita diretório** (`validar_peca.py` + `CLAUDE.md`)
- Passar a pasta do processo como `--fontes` carrega todos os PDFs automaticamente
- Resolve definitivamente o problema com nomes de arquivo com espaços
- CLAUDE.md atualizado: padrão agora é `--fontes "Entrada/XXXXX"` (sem listar arquivos individuais)

**C — Eliminar subagente para leitura de PDFs** (`CLAUDE.md`)
- ETAPA 1 agora instrui usar `pesquisar.py` diretamente para extrair texto dos PDFs
- Mais rápido, extrai com número de página, já prepara base para o Banco

### Arquivos modificados
| Arquivo | Alteração |
|---------|-----------|
| `skills/validacao-anti-alucinacao/validar_peca.py` | LEGISLACAO_CONHECIDA expandida; `--fontes` aceita diretório |
| `CLAUDE.md` | ETAPA 1 e CHECKPOINT 1 atualizados |

### Como reverter
- `validar_peca.py`: restaurar `LEGISLACAO_CONHECIDA` original (5 entradas) e `ler_documentos_fonte()` original (sem tratamento de diretório)
- `CLAUDE.md`: restaurar texto original das seções ETAPA 1 e CHECKPOINT 1

---

## [v2.3] — 2026-02-20

### Corrigido
- **Barra lateral com texto do modelo (hanseníase)** — `formatar_peca.py` agora atualiza a barra lateral SEMPRE, independente de `--texto-pedido` ser passado. Antes, quando omitido, o texto do template permanecia intacto.
- **Extração automática do pedido** — nova função `_extrair_texto_pedido()` extrai o resumo do pedido diretamente do conteúdo da peça (SÍNTESE ARGUMENTATIVA → CONCLUSÃO → primeiro parágrafo), eliminando a necessidade de passar `--texto-pedido` manualmente.

### Arquivos modificados
| Arquivo | Alteração |
|---------|-----------|
| `skills/formatacao-docx/formatar_peca.py` | Barra lateral sempre atualizada; função `_extrair_texto_pedido()` adicionada |

### Como reverter
- Em `criar_documento`, restaurar: `if texto_pedido and itens_sumario: atualizar_barra_lateral(...)`
- Remover a função `_extrair_texto_pedido()`

---

## [v2.2] — 2026-02-20

### Corrigido
- **Encoding UTF-8 no terminal Windows** — todos os scripts agora forçam `sys.stdout`/`sys.stderr` para UTF-8, eliminando os `?` e `\ufffd` no output do terminal
- **Instrução Normativa removida indevidamente** — `validar_peca.py` agora trata `instrucao_normativa` e `portaria` como risco ZERO (normas verificáveis), não mais as remove
- **Endereçamento removido indevidamente** — `validar_peca.py` agora ignora ocorrências do tipo `ministro` no cabeçalho da petição (antes do primeiro `##`), preservando o destinatário

### Arquivos modificados
| Arquivo | Alteração |
|---------|-----------|
| `skills/validacao-anti-alucinacao/validar_peca.py` | UTF-8 stdout; IN/Portaria como risco ZERO; exclusão de ministro no cabeçalho |
| `skills/formatacao-docx/formatar_peca.py` | UTF-8 stdout |
| `skills/pesquisa-juridica/pesquisar.py` | UTF-8 stdout |

### Como reverter
- Remover o bloco `if sys.stdout.encoding != 'utf-8':` dos três scripts
- Em `validar_peca.py`, remover o bloco `if tipo in ['instrucao_normativa', 'portaria', 'sumula']:` e a lógica de exclusão de cabeçalho em `extrair_citacoes`

---

## [v2.1] — 2026-02-19

### Adicionado
- **CHANGELOG.md** (este arquivo) — log de versões para rastreabilidade e rollback
- Referência ao CHANGELOG adicionada no CLAUDE.md

### Arquivos criados
| Arquivo | Descrição |
|---------|-----------|
| `CHANGELOG.md` | Log de alterações do projeto |

### Como reverter
- Deletar `CHANGELOG.md`
- Remover referência ao CHANGELOG do `CLAUDE.md`

---

## [v2.0] — 2026-02-15

### Resumo
Introdução do **Sistema de Fontes Verificáveis** — mudança arquitetural significativa. Adicionou o Banco de Fontes Verificadas como fonte de verdade para citações, marcadores `[Fxxx]` convertidos em notas de rodapé, e modo duplo de operação (Banco vs. Legado).

### Adicionado
| Arquivo | Descrição |
|---------|-----------|
| `skills/pesquisa-juridica/SKILL.md` | Nova skill de pesquisa jurídica |
| `skills/pesquisa-juridica/pesquisar.py` (v1.0) | Script de extração de citações de PDFs → JSON |

### Modificado
| Arquivo | O que mudou | Versão anterior |
|---------|-------------|-----------------|
| `CLAUDE.md` | Adicionada Etapa 1.5 (Pesquisa Jurídica), seção "Sistema de Fontes Verificáveis", pipeline com `--banco`, marcadores `[Fxxx]` | v1.x (sem sistema de fontes) |
| `skills/validacao-anti-alucinacao/validar_peca.py` | v1.0 → v2.0: suporte a `--banco` para validação cruzada com Banco de Fontes | v1.0 (modo legado apenas) |
| `skills/formatacao-docx/formatar_peca.py` | v1.x → v2.0: suporte a `--banco` para gerar notas de rodapé a partir do Banco | v1.x (sem notas de rodapé do Banco) |
| `skills/validacao-anti-alucinacao/SKILL.md` | Referência ao modo Banco de Fontes | Sem menção ao Banco |
| `skills/memoriais/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/tnu/agravo-interno/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/tnu/embargos-declaracao/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/stj/agravo-interno/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/stj/embargos-declaracao/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/stj/embargos-divergencia/SKILL.md` | Pesquisa Jurídica marcada como RECOMENDADA | Sem referência |
| `skills/arquivamento/SKILL.md` | Pesquisa Jurídica marcada como OPCIONAL | Sem referência |

### Como reverter
- Restaurar backup completo de `D:\DPU\dpu-workspace-BACKUP-2026-02-15`
- OU reverter manualmente:
  1. Deletar `skills/pesquisa-juridica/` (pasta inteira)
  2. Restaurar `validar_peca.py` v1.0 do backup
  3. Restaurar `formatar_peca.py` v1.x do backup
  4. Restaurar `CLAUDE.md` do backup (remover Etapa 1.5 e seção de Fontes Verificáveis)
  5. Restaurar cada SKILL.md do backup (remover referências ao Banco)

---

## [v1.2] — 2026-02-12 (estimado)

### Adicionado
| Arquivo | Descrição |
|---------|-----------|
| `CHECKLIST_FORMATACAO.md` | Checklist de qualidade para formatação de peças |

### Como reverter
- Deletar `CHECKLIST_FORMATACAO.md`

---

## [v1.1] — 2026-02 (estimado)

### Resumo
Adição das skills de recurso para TNU e STJ, e da skill de memoriais.

### Adicionado
| Arquivo | Descrição |
|---------|-----------|
| `skills/tnu/agravo-interno/SKILL.md` | Skill de agravo interno na TNU |
| `skills/tnu/embargos-declaracao/SKILL.md` | Skill de embargos de declaração na TNU |
| `skills/stj/agravo-interno/SKILL.md` | Skill de agravo interno no STJ |
| `skills/stj/embargos-declaracao/SKILL.md` | Skill de embargos de declaração no STJ |
| `skills/stj/embargos-divergencia/SKILL.md` | Skill de embargos de divergência no STJ |
| `skills/stj/agravo-resp/SKILL.md` | Skill de AREsp (placeholder — a ser detalhada) |
| `skills/memoriais/SKILL.md` | Skill de memoriais/manifestação |

### Como reverter
- Deletar as pastas/arquivos adicionados acima

---

## [v1.0] — 2026-02 (estimado)

### Resumo
Versão inicial do sistema. Estrutura base com orquestração via CLAUDE.md, triagem, arquivamento, validação anti-alucinação e formatação DOCX.

### Arquivos criados
| Arquivo | Descrição |
|---------|-----------|
| `CLAUDE.md` | Orquestração principal do sistema |
| `README.md` | Guia de uso |
| `skills/triagem/SKILL.md` | Skill de triagem processual |
| `skills/arquivamento/SKILL.md` | Skill de despacho de arquivamento |
| `skills/validacao-anti-alucinacao/SKILL.md` | Skill de validação anti-alucinação |
| `skills/validacao-anti-alucinacao/validar_peca.py` (v1.0) | Script de validação |
| `skills/validacao-anti-alucinacao/README.md` | Documentação da validação |
| `skills/validacao-anti-alucinacao/APRESENTACAO.md` | Apresentação do sistema |
| `skills/validacao-anti-alucinacao/INTEGRACAO_COMPLETA.md` | Guia de integração |
| `skills/validacao-anti-alucinacao/EXEMPLO_USO.md` | Exemplos de uso |
| `skills/formatacao-docx/SKILL.md` | Skill de formatação DOCX/PDF |
| `skills/formatacao-docx/formatar_peca.py` (v1.x) | Script de formatação |
| `skills/formatacao-docx/EXEMPLO_USO.md` | Exemplos de uso |
| `skills/formatacao-docx/assets/` | Fontes e imagens do template |
| `regimentos/REGIMENTO_INTERNO_TNU.txt` | RI-TNU extraído |
| `regimentos/REGIMENTO_INTERNO_STJ_RECURSOS.txt` | RI-STJ (Recursos) extraído |
| `regimentos/*.pdf` | PDFs originais dos regimentos |
| `.claude/commands/analisar.md` | Comando Claude: analisar processo |
| `.claude/commands/arquivar.md` | Comando Claude: arquivar PAJ |

### Como reverter
- N/A (versão inicial)

---

## Convenções deste Log

- **Versões:** `[vX.Y]` — X = mudança arquitetural, Y = adições/correções
- **Datas:** formato AAAA-MM-DD. Datas marcadas "estimado" foram inferidas
- **Cada entrada contém:**
  - O que foi adicionado/modificado/removido
  - Tabela de arquivos afetados
  - Instruções de rollback ("Como reverter")
- **Ao modificar o projeto:** adicionar nova entrada NO TOPO deste arquivo (mais recente primeiro)

---

## Instruções para o Claude

**Ao fazer qualquer alteração no projeto (criar, modificar ou deletar arquivos de configuração, skills ou scripts), o Claude DEVE:**

1. Adicionar uma nova entrada neste CHANGELOG.md com:
   - Número de versão incrementado
   - Data (AAAA-MM-DD)
   - Lista de arquivos criados/modificados/removidos
   - Descrição concisa do que mudou em cada arquivo
   - Instruções de rollback ("Como reverter")
2. Se a alteração for significativa, sugerir ao Defensor criar backup antes de aplicar

**O Claude NÃO deve atualizar o CHANGELOG para:**
- Arquivos gerados na pasta `/saida` (são output de trabalho, não alterações do sistema)
- Arquivos na pasta `/entrada` (são input do Defensor)
