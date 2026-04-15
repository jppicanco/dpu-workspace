---
description: Roda o dpuscript para preparar pastas de todos PAJs novos/movimentados da caixa SISDPU
allowed-tools: Bash(cmd //c *)
---

Execute o script `dpuscript/preparar_pajs.py` para coletar dados de todos os PAJs novos ou movimentados na caixa de entrada do SISDPU, baixar peças TNU e decisões STJ/STF, e montar as pastas em `Entrada/dpuscript/<PAJ>/` prontas para análise.

## Comando

```bash
cmd //c "cd /d E:\DPU\dpu-workspace\dpuscript && .venv\Scripts\python.exe preparar_pajs.py"
```

## Após execução

1. Liste as pastas novas/atualizadas em `Entrada/dpuscript/`
2. Para cada uma, mostre:
   - PAJ, assistido, classificação automática (ARQUIVADO_TRAMITE_INTERNO, DECISAO_MERITO_STJ_PENDENTE, etc.)
   - Quantas peças TNU foram baixadas
   - Quantas decisões de tribunais superiores foram baixadas
3. Pergunte ao João qual PAJ quer analisar primeiro. Ele pode usar `/analisar Entrada/dpuscript/<PAJ>` para iniciar a análise, ou abrir o `PROMPT_MAX.md` da pasta diretamente.

**Observações:**
- O script usa dedup por hash da última movimentação: PAJs inalterados desde a última rodada são pulados (rápido).
- Filtragem anti-lixo preserva sempre as 3 movs mais recentes + tudo dentro de 30 dias antes da data de retorno à caixa.
- PROMPT_MAX.md já incorpora teor completo das decisões STJ/STF baixadas — não é preciso abrir o PDF em separado.
- Se algum PAJ falhar, o script continua os demais e reporta as falhas no final.
