---
description: Força reprocessamento de 1 PAJ específico (mesmo que já tenha sido preparado hoje)
argument-hint: <PAJ no formato AAAA/UNI-NUM, ex: 2021/039-18791>
allowed-tools: Bash(cmd //c *)
---

Reprocessa um PAJ específico mesmo se ele já estiver registrado no estado. Use quando quiser forçar nova coleta (ex: sabe que houve mov nova e o estado ainda não atualizou).

## Validação

Se $ARGUMENTS estiver vazio, pergunte ao João qual PAJ processar. O formato é `AAAA/UNI-NUM`, por exemplo `2021/039-18791`.

## Comando

```bash
cmd //c "cd /d E:\DPU\dpu-workspace\dpuscript && .venv\Scripts\python.exe _reset_estado.py $ARGUMENTS && .venv\Scripts\python.exe preparar_pajs.py --only $ARGUMENTS"
```

## Após execução

1. Mostre ao João a classificação automática e quantas peças/decisões foram baixadas
2. Ofereça abrir a pasta `Entrada/dpuscript/<PAJ_NORMALIZADO>/` para iniciar análise (`/analisar Entrada/dpuscript/<PAJ_NORMALIZADO>`)
3. Se o script falhar, mostre o erro do stderr para diagnóstico

**Observação:** o `_reset_estado.py` remove só esse PAJ do estado (não zera os outros), então PAJs já preparados hoje permanecem registrados.
