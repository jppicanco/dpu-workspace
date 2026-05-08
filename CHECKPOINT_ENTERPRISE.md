# Checkpoint Completo — Migração para Claude Enterprise (2026-05-08)

> Arquivo criado para preservar estado total do projeto antes de JP trocar
> conta Claude Code (de MAX para Enterprise). Nova sessão deve ler ESTE
> arquivo PRIMEIRO para retomar exatamente de onde parou.

---

## 1. Identificação do Projeto

| Item | Valor |
|------|-------|
| **Pasta local** | `E:\DPU\dpu-workspace\` |
| **GitHub** | `https://github.com/jppicanco/dpu-workspace` |
| **Branch ativa** | `main` (commits mais recentes) |
| **Branch legado** | `v2-dpuscript` (primeiros commits do dpuscript, antes de merge pra main) |
| **Último commit** | `03dd26d` — feat(dpuscript): automação SISDPU + fluxo arquivamento |
| **Sync GitHub** | ✅ Tudo pushado. Nenhum commit local pendente. |

---

## 2. O que é este projeto

Sistema de assistência jurídica para Defensoria Pública da União (DPU).
Defensor **João Paulo Picanço** atua em TNU (Turma Nacional de Uniformização)
e STJ (Superior Tribunal de Justiça).

**Dois subsistemas:**

### A) Claude MAX workspace (skills jurídicas)
- Skills de triagem, arquivamento (Tipo 1/2/3), agravo, embargos, pesquisa jurídica
- MCPs: BNP (precedentes vinculantes) + CJF (jurisprudência)
- Formatação DOCX institucional DPU
- Anti-alucinação, regra de ouro "sem fonte verificável não cite"
- Slash commands: `/analisar`, `/arquivar`, `/juris`, `/preparar-pajs`, `/preparar`

### B) dpuscript (pipeline automático de coleta)
- Entra no SISDPU via Playwright, baixa caixa de entrada, extrai movimentações
- Entra no e-Proc TNU **autenticado** (perfil ASSISTENTE PROCURADOR), lista e baixa TODAS as peças
- Baixa decisões STJ e STF
- OCR condicional via Tesseract (só PDFs scan/imagem)
- Download em 2 fases (sessão e-Proc curta + processamento local)
- Gera `PROMPT_MAX.md` por PAJ com teor embutido
- Automação de movimentação no SISDPU (`sisdpu_automation.py`)

---

## 3. Arquivos-chave

### Pipeline dpuscript (`dpuscript/`)
| Arquivo | Função |
|---------|--------|
| `preparar_pajs.py` | Pipeline principal — coleta SISDPU + TNU + STJ + STF + gera PROMPT_MAX |
| `eproc_auth_client.py` | Autenticação e-Proc TNU (perfil persistente + 2FA interativo fallback) |
| `setup_eproc.py` | Setup 1x do perfil autenticado (abre Edge visível, JP faz 2FA) |
| `sisdpu_automation.py` | Automação de movimentação no SISDPU |
| `monitor_transito.py` | Monitor de trânsito em julgado |
| `notificar_telegram.py` | Notificação via Bot Telegram Jarbas DPU |
| `_reset_estado.py` | Helper: remove PAJ do estado pra forçar reprocessamento |
| `requirements.txt` | Dependências Python |
| `.env` (gitignored) | Credenciais: SISDPU_USERNAME, SISDPU_PASSWORD, EPROC_USUARIO, EPROC_SENHA, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| `eproc_profile/` (gitignored) | Perfil persistente Edge com cookies e-Proc TNU |
| `sisdpu_profile/` (gitignored) | Perfil persistente Edge com cookies SISDPU |

### MCPs (`dpuscript/mcp_servers/`)
| MCP | Função |
|-----|--------|
| `sisdpu/client.py` | Scraping SISDPU (Playwright, login+caixa+PAJs+detalhes) |
| `datajud/client.py` | API pública DataJud/CNJ |
| `tnu/client.py` | Consulta pública e-Proc TNU (eventos, docs públicos) |
| `stj/client.py` | Extrator PDF decisões STJ (PyMuPDF) |

### Skills jurídicas (raiz do workspace)
| Pasta | Função |
|-------|--------|
| `skills/triagem/` | Classificação tribunal+decisão+recurso cabível |
| `skills/arquivamento/` | Despachos de arquivamento (Tipo 1/2/3) |
| `skills/tnu/agravo-interno/` | Agravo interno TNU |
| `skills/tnu/embargos-declaracao/` | ED TNU |
| `skills/stj/agravo-interno/` | Agravo interno STJ |
| `skills/stj/embargos-declaracao/` | ED STJ |
| `skills/stj/agravo-resp/` | AREsp STJ |
| `skills/stj/embargos-divergencia/` | EDiv STJ |
| `skills/pesquisa-juridica/` | Pesquisa BNP+CJF+legislação |
| `skills/formatacao-docx/` | Formatação institucional DPU (DOCX+PDF) |

### Slash commands (`.claude/commands/`)
| Comando | Função |
|---------|--------|
| `/analisar` | Triagem completa de processo |
| `/arquivar` | Despacho de arquivamento direto |
| `/juris` | Pesquisa jurisprudencial |
| `/preparar-pajs` | Roda dpuscript em todos PAJs novos/movimentados |
| `/preparar <PAJ>` | Força reprocessar 1 PAJ específico |

---

## 4. Estado do ambiente local

### Python
- Versão: 3.13.5 (sistema)
- Venv: `dpuscript/.venv/` (Playwright, httpx, pymupdf, pytesseract, Pillow)
- Tesseract-OCR: 5.5 em `C:\Program Files\Tesseract-OCR\` (com `por.traineddata`)

### Perfis autenticados (NÃO versionados — gitignored)
- `dpuscript/eproc_profile/` (711 arquivos) — sessão e-Proc TNU
- `dpuscript/sisdpu_profile/` (368 arquivos) — sessão SISDPU

**Se os perfis expirarem:** rodar `setup_eproc.py` (Edge visível, JP faz 2FA 1x).
Se `sisdpu_automation.py` pedir login: `.env` tem as credenciais.

### Credenciais (`.env`, NÃO versionado)
```
SISDPU_USERNAME=...
SISDPU_PASSWORD=...
EPROC_USUARIO=...
EPROC_SENHA=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

### PAJs já preparados em `Entrada/dpuscript/`
40 pastas de PAJ com PROMPT_MAX.md + peças + decisões. Cada pasta contém:
- `PROMPT_MAX.md` — consolidado pronto pro MAX analisar
- `metadata.json` — dados do SISDPU + classificação
- `eventos_tnu.json` — eventos e-Proc (se TNU)
- `datajud.json` — dados DataJud (se não-TNU)
- `peças/` — PDFs + .txt das peças TNU baixadas (com OCR quando scan)
- `decisoes_superiores/` — decisões STJ/STF baixadas (PDF + texto)

---

## 5. MCPs do workspace (`.mcp.json`)
- **bnp-api** — precedentes vinculantes (STF/STJ/TST)
  - Server: `E:\DPU\lista-trf\mcp\bnp-api\server.py`
- **cjf-jurisprudencia** — jurisprudência unificada CJF
  - Server: `E:\DPU\lista-trf\mcp\cjf-jurisprudencia\server.py`

---

## 6. Lições aprendidas (referência)

Arquivo detalhado em `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\licoes_aprendidas_anti_padroes.md`

Principais:
1. NÃO duplicar no PROMPT_MAX o que o MAX já sabe (formatação, triagem, etc)
2. SEMPRE consultar ASSISTENTE-JUDICIAL antes de reinventar solução
3. Status PAJ + últimas movimentações são o que importa — não metadados
4. URLs de decisão vêm de qualquer tribunal (STF, STJ, TNU) — regex amplo
5. Filtro anti-lixo preserva últimas 3 movs + 30 dias antes da data de retorno
6. OCR condicional: só quando PyMuPDF retorna vazio (PDFs scan)
7. Download em 2 fases: sessão e-Proc curta + processamento local
8. Seleção de perfil ASSISTENTE via JS `acaoLogar(hash)` — NUNCA PROCURADOR

---

## 7. Mac Mini M4 (Jarbas — separado)

Projeto Jarbas roda no M4 via Hermes Agent. **Separado do dpu-workspace.**
- SSH: `macmini@192.168.0.102`
- Único serviço DPU ativo: `ai.jarbas.verificar-pajs` (cron 8h → Telegram lista PAJs)
- Cron `preparar-pajs` desabilitado no M4 (agora roda no PC via dpuscript)
- Modelo LLM: Hermes + minimax/minimax-m2.7 via Nous Portal
- Decisão arquitetural: preparação pesada roda no PC (MAX/Enterprise), M4 só notificação leve

---

## 8. Como retomar na sessão Enterprise

1. Abrir Claude Code Enterprise em `E:\DPU\dpu-workspace\`
2. Claude vai ler `CLAUDE.md` automaticamente (instruções do projeto)
3. Pra contexto adicional, pedir pra ler este `CHECKPOINT_ENTERPRISE.md`
4. Pra memórias de sessões passadas: `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\`
5. Comandos úteis:
   ```powershell
   cd E:\DPU\dpu-workspace\dpuscript
   .venv\Scripts\python.exe preparar_pajs.py --only 2018/039-17434  # 1 PAJ
   .venv\Scripts\python.exe preparar_pajs.py                        # todos
   .venv\Scripts\python.exe _reset_estado.py 2018/039-17434         # força reprocessar
   .venv\Scripts\python.exe setup_eproc.py                          # setup auth e-Proc
   ```

---

## 9. Mudanças não commitadas (status atual)

- `CHECKPOINT_2026-05-08.md` — untracked (anterior a este)
- `.claude/worktrees/` — temp Claude Code, ignorar
- **Nada pendente de commit relevante. GitHub está em dia.**
