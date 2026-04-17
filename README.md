# dpu-workspace

Workspace do Claude Code para Defensores Públicos Federais atuantes na **TNU** (Turma Nacional de Uniformização) e no **STJ** — elaboração de peças jurídicas assistida por IA.

> Desenvolvido para uso interno na DPU. Projeto pessoal, sem vínculo institucional oficial.

---

## O que é

Um workspace completo para o Claude Code que inclui:

- **CLAUDE.md** — instruções do sistema: fluxo de trabalho, regras de formatação, estilo jurídico, gestão de fontes verificáveis, alertas de contexto
- **Skills** — receitas detalhadas para cada tipo de peça (triagem, arquivamento, embargos, agravo interno, memoriais, formatação DOCX)
- **Pipeline dpuscript** — scripts Python que baixam automaticamente os processos do e-Proc TNU, extraem texto (com OCR), classificam as decisões e geram prompts otimizados para o Claude
- **Regimentos internos** — TNU e STJ em texto, para consulta rápida pelo Claude sem precisar de PDF

### Peças suportadas

| Tribunal | Peça |
|----------|------|
| TNU | Embargos de declaração |
| TNU | Agravo interno |
| TNU | Arquivamento (3 tipos) |
| TNU | Memoriais |
| STJ | Agravo interno |
| STJ | Embargos de declaração |
| STJ | Embargos de divergência |
| STJ | Agravo em REsp |

---

## Pré-requisitos

- **Claude Code** com modelo Max (claude-opus ou claude-sonnet) — a elaboração das peças é feita via CLI, não por API paga
- **Python 3.11+** (para o pipeline dpuscript)
- **Playwright** — `pip install playwright && playwright install msedge`
- **Tesseract OCR** — para PDFs escaneados (opcional, mas recomendado)
- Acesso ao e-Proc TNU com 2FA (para o pipeline automatizado)

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/jppicanco/dpu-workspace.git
cd dpu-workspace

# 2. Instale as dependências do pipeline
cd dpuscript
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install msedge

# 3. Configure as credenciais
copy .env.example .env
# Edite .env com suas credenciais do e-Proc e SISDPU

# 4. Faça o setup inicial do e-Proc (só uma vez)
.venv\Scripts\python.exe setup_eproc.py
```

---

## Estrutura

```
dpu-workspace/
├── CLAUDE.md                  # Instruções do sistema para o Claude Code
├── CHANGELOG.md
├── .mcp.json.example          # Template de configuração de MCPs
├── dpuscript/                 # Pipeline de automação
│   ├── .env.example           # Template de credenciais
│   ├── preparar_pajs.py       # Script principal do pipeline
│   ├── eproc_auth_client.py   # Autenticação e-Proc TNU via Playwright
│   ├── setup_eproc.py         # Setup único da sessão autenticada
│   ├── notificar_telegram.py  # Notificações via Telegram (opcional)
│   ├── monitor_transito.py    # Monitoramento de trânsito em julgado
│   └── mcp_servers/           # MCPs locais (SISDPU, datajud, TNU, STJ)
├── skills/                    # Skills do Claude para cada tipo de peça
│   ├── triagem/SKILL.md
│   ├── arquivamento/SKILL.md
│   ├── tnu/
│   │   ├── embargos-declaracao/SKILL.md
│   │   └── agravo-interno/SKILL.md
│   ├── stj/
│   │   ├── embargos-declaracao/SKILL.md
│   │   ├── embargos-divergencia/SKILL.md
│   │   ├── agravo-interno/SKILL.md
│   │   └── agravo-resp/SKILL.md
│   ├── memoriais/SKILL.md
│   ├── pesquisa-juridica/SKILL.md
│   └── formatacao-docx/       # Geração de DOCX+PDF via python-docx
├── regimentos/                # Regimentos TNU e STJ em texto
│   ├── REGIMENTO_INTERNO_TNU.txt
│   └── REGIMENTO_INTERNO_STJ_RECURSOS.txt
├── .claude/commands/          # Slash commands (/analisar, /arquivar, /preparar-pajs)
└── Entrada/                   # IGNORADO pelo git — seus processos ficam aqui
```

---

## Uso básico (sem pipeline)

Abra o Claude Code na pasta `dpu-workspace` e descreva o que precisa:

```
Analise o processo na pasta Entrada e elabore a peça cabível
```

O Claude vai: ler os PDFs → fazer triagem → identificar o recurso cabível → elaborar a peça → formatar em DOCX.

## Uso com pipeline (automação completa)

```bash
# Baixar todos os processos novos do e-Proc TNU
cd dpuscript
.venv\Scripts\python.exe preparar_pajs.py

# Ou via slash command no Claude Code:
/preparar-pajs
```

O pipeline baixa as peças, extrai texto, classifica as decisões e prepara `PROMPT_MAX.md` para cada PAJ — pronto para o Claude elaborar as peças.

Para o painel web com todos os PAJs, use o [dpuscript-ui](https://github.com/jppicanco/dpuscript-ui).

---

## Dados e privacidade

Os arquivos de processos (PDFs, TXTs, metadados de assistidos) ficam **exclusivamente na máquina local** do Defensor. O `.gitignore` exclui as pastas `Entrada/`, `saida/`, `Juris/`, logs e credenciais. Nenhum dado de assistido é versionado ou enviado para qualquer servidor externo.

---

## Contribuições

Pull requests são bem-vindos — especialmente novas skills, melhorias no pipeline e correções nos regimentos.

Se você é Defensor Público Federal e quer usar este sistema, o setup mínimo é:
1. Clone o repo
2. Adapte o `CLAUDE.md` para o seu contexto (tribunal, instância, nome)
3. Abra o Claude Code Max aqui e comece
