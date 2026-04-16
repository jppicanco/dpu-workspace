# Prompt pra próxima sessão — retomada do dpuscript

Copie o bloco abaixo em um chat NOVO do Claude Code, já aberto em `E:\DPU\dpu-workspace\`.

---

```
Projeto dpu-workspace — continuação da sessão de 15-abr-2026 tarde sobre o pipeline dpuscript (e-Proc TNU autenticado + OCR).

**ANTES DE QUALQUER AÇÃO**, leia na ordem:

1. `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\MEMORY.md` (índice)
2. `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\checkpoint_2026-04-15_eproc_autenticado.md` (estado final DETALHADO da última sessão)
3. `C:\Users\JP\.claude\projects\E--JARBAS-DPU\memory\licoes_aprendidas_anti_padroes.md` (lições 1-14 — NÃO repita erros)
4. `E:\DPU\dpu-workspace\dpuscript\FUTURO.md` (plano de front-end separado, só pra contexto)

**Estado atual do sistema (15-abr-2026 19:00):**

- Projeto DPU migrado de `D:\DPU\` → `E:\DPU\` (completo)
- Pipeline dpuscript em `E:\DPU\dpu-workspace\dpuscript\` com venv, MCPs, Playwright, Tesseract
- Autenticação e-Proc TNU funcionando (perfil persistente + 2FA interativo fallback)
- Download em 2 fases (sessão e-Proc curta + processamento local)
- OCR condicional via Tesseract PT (só em PDFs scan, PDFs modernos passam direto)
- Branch git `v2-dpuscript` com 8 commits no GitHub — `main` intocada

**Testes validados**:
- 2018/039-17434 (Rita, TNU antigo com scans): 41 docs autenticados, 30 baixados, 30 com texto (OCR)
- 2026/039-00177 (Luciano, TNU moderno): 2 docs, sem OCR, 25s
- 2025/039-06569 (Therezinha, STJ): decisão monocrática STJ embutida

**Pendências ao retomar** (de menor a maior):

1. **Classificação do Luciano**: virou `DECISAO_MERITO_TNU_PENDENTE` quando devia ser `VISTA_MP`. Não é crítico mas vale investigar se for rápido. O teor do PDF embutido no PROMPT_MAX está correto ("Abra-se vista ao MPF").

2. **Rodar full (31 PAJs)** — ainda não foi feito. Vai demorar 20-40min por causa dos OCRs. Pode fazer via `.venv\Scripts\python.exe preparar_pajs.py` (sem --only).

3. **Decidir sobre agendamento automático**: Task Scheduler no Windows pra rodar de manhã, ou continuar manual via `/preparar-pajs` no MAX.

4. **Sessão e-Proc expira entre execuções** — quando expirar, script abre Edge visível pedindo 2FA (1x por run). Comportamento esperado.

## REGRAS IMUTÁVEIS (da sessão anterior)

1. NÃO pedir credenciais do JP no chat — ele coloca direto no `.env`
2. NÃO commitar `.env`, `eproc_profile/`, `Entrada/`, `logs/`, `estado/` (já no `.gitignore`)
3. SEMPRE perfil ASSISTENTE PROCURADOR no e-Proc (`ASP83999639334`), NUNCA P39334/PROCURADOR
4. Descobertas: STF não libera peças sem login; TNU sim (via ASSISTENTE); STJ é via URL na descrição da caixa SISDPU
5. Se migrar/portar algo, ANTES olhar se já existe em `E:\ASSISTENTE-JUDICIAL\` (read-only)

## Tarefa inicial

Confirme que leu os 4 arquivos de memória. Resuma em 3 linhas o estado atual. Pergunte ao Joao o que ele quer fazer:
- Ajustar classificação Luciano?
- Rodar full 31 PAJs?
- Agendar automação?
- Outro refinamento específico?

## Chat / tom

PT-BR, direto, chama Joao de "Joao". Nada de emoji/acentuação em prints (Windows cp1252 não suporta).
```

---

## Comandos úteis pra ter à mão

```powershell
cd E:\DPU\dpu-workspace\dpuscript

# Resetar estado de 1 PAJ pra reprocessar
.venv\Scripts\python.exe _reset_estado.py 2018/039-17434

# Rodar 1 PAJ
.venv\Scripts\python.exe preparar_pajs.py --only 2018/039-17434

# Rodar tudo (caixa inteira)
.venv\Scripts\python.exe preparar_pajs.py

# Rerodar setup autenticação e-Proc (só se expirou)
.venv\Scripts\python.exe setup_eproc.py

# Git: ver qual branch
git branch
git log --oneline -5
```

## Paths importantes

- Pipeline: `E:\DPU\dpu-workspace\dpuscript\preparar_pajs.py`
- Auth e-Proc: `E:\DPU\dpu-workspace\dpuscript\eproc_auth_client.py`
- Setup auth: `E:\DPU\dpu-workspace\dpuscript\setup_eproc.py`
- Output por PAJ: `E:\DPU\dpu-workspace\Entrada\dpuscript\<PAJ>\`
- Credenciais: `E:\DPU\dpu-workspace\dpuscript\.env`
- Perfil e-Proc: `E:\DPU\dpu-workspace\dpuscript\eproc_profile\`
