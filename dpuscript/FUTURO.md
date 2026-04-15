# Plano futuro — projeto front-end separado para o dpuscript

Registrado em 2026-04-15 pelo João Paulo Picanço (Defensor TNU+STJ).

## Objetivo

Depois que o `dpuscript` (backend Python) estiver estável e refinado em vários casos reais, criar um **projeto separado** (não dentro do dpu-workspace) que forneça uma interface gráfica amigável para:

1. **Listagem da caixa** — ver todos os PAJs atuais organizadamente, com resumo (classificação Jarbas, assistido, última movimentação, prazos detectados)
2. **Ações por PAJ**:
   - Baixar tudo (metadata + movimentações + decisões) — chama `preparar_pajs.py --only <PAJ>` sob o capô
   - Visualizar decisão/peça baixada (.pdf ou .txt) inline
   - Ver movimentações SISDPU em timeline
   - Gerar/atualizar PROMPT_MAX.md
   - Abrir MAX com o contexto pronto (botão "Elaborar peça" → dispara análise e minuta)
   - Ver a peça final (DOCX/PDF)
3. **Priorização** — ordenar por data de envio, por classificação (urgência), por foro etc.

## Arquitetura provável

- **Backend**: reutiliza `dpuscript` (Python puro + clients MCP) atual
- **Frontend**: provavelmente web local (FastAPI + React/HTMX) ou desktop (Electron/Tauri)
- **Deploy**: próprio PC do JP (Windows)
- **Integração MAX**: via CLI (chama `claude` do Claude Code) ou API Anthropic direta

## Por que projeto SEPARADO e não dentro do dpu-workspace

- dpu-workspace é o projeto de trabalho jurídico — fica limpo pra minutas/peças
- dpuscript é o pipeline de coleta — backend
- Frontend seria a "casca" visual — merece projeto próprio com roadmap independente

## Quando começar

Só depois de:
- `dpuscript` estar refinado e validado em dezenas de PAJs reais
- Fluxo manual (abrir workspace → `/preparar-pajs` → `/analisar <PAJ>`) estar confortável
- JP decidir que a fricção atual vale um frontend

**Não começar antes disso — evita construir UI sobre API imatura.**

## Referência cruzada

- Backend atual: `E:\DPU\dpu-workspace\dpuscript\preparar_pajs.py`
- Slash commands MAX: `E:\DPU\dpu-workspace\.claude\commands\preparar-pajs.md` e `preparar.md`
- Memórias do projeto: `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\` (convém criar memória separada do projeto dpu-workspace quando criar o front end)
