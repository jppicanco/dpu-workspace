# Skill: Ensinar o Grok (corrigir erro recorrente da decisão automática)

## Objetivo
Sempre que JP ou o Claude descobrir que o **Grok** (estágio de decisão no M4) errou —
classificação, fundamento, prazo, conduta, formato de despacho — capturar a correção
de forma estruturada para que o Grok **não repita o mesmo erro** nas próximas rodadas.

## Como o Grok aprende (o que ele lê a cada rodada)
O `decidir_grok.py` (M4) carrega no prompt, a cada execução:
- `dpuscript/memory/regras_atuacao.md` — regras aprendidas. **Dinâmico: sem deploy.**
- `dpuscript/memory/modelo_arquivamento.md` — modelo/conteúdo do despacho de arquivamento.
- Regras hardcoded no prompt de `dpuscript-ui/decidir_grok.py` — **estrutural: exige deploy.**

## Onde colocar a correção (decida pelo tipo de erro)
1. **`regras_atuacao.md`** — PADRÃO (≈90% dos casos): erro de classificação (DESPACHO/
   ARQUIVAMENTO/RECURSO), fundamento jurídico, cálculo de prazo, conduta. Dinâmico —
   a próxima rodada do Grok já considera, sem deploy.
2. **`modelo_arquivamento.md`** — se for sobre o conteúdo/estrutura do despacho de
   arquivamento (ex.: parágrafo-padrão, precedente a citar, formatação SISDPU).
3. **Prompt do `decidir_grok.py`** — SÓ se for estrutural (campo novo no schema, regra
   que vale para todo o prompt, formato de saída). Exige deploy + commit + restart.

## Formato da regra (em `regras_atuacao.md`)
Inserir uma seção ANTES de "## Como adicionar nova regra":

```
## <Tema curto e específico>

**ERRO COMUM:** <o que o Grok fez de errado, concreto>

**REALIDADE:** <o que é juridicamente correto, com fundamento>

**REGRA:** <instrução explícita e acionável — como o Grok deve agir>

**Exemplo:** <caso concreto, opcional mas útil>

**Origem:** JP correção em <AAAA-MM-DD>
```

## Passos
1. **Entender** o erro e a correção. Se faltar elemento jurídico, perguntar ao JP —
   NÃO presumir.
2. **Confirmar o fundamento** com pesquisa real (MCP `cjf-jurisprudencia` / `bnp-api`)
   quando for questão jurídica. **NUNCA inventar** citação, súmula, tema ou número.
3. **Escrever a regra** no formato acima, no arquivo certo (ver "Onde colocar").
4. **Sincronizar para o M4** (o Grok roda lá):
   `scp <arquivo> macmini@192.168.0.102:/Users/macmini/dpu-workspace/dpuscript/memory/`
   (ou para `dpuscript-ui/` se mexeu no prompt; aí reiniciar a UI e o cron usa no próximo run).
5. **Registrar no log de aprendizado:** acrescentar uma linha em
   `dpuscript/memory/correcoes_grok.log` — `<AAAA-MM-DD> | <tema> | <resumo 1 linha>`.
6. **Commitar** (`dpu-workspace` e/ou `dpuscript-ui`) e `git push`.
7. **PAJs já afetados:** se o mesmo erro já contaminou PAJs decididos, sugerir ao JP
   regenerar — `decidir_grok.py --prod --force --so-tipos <TIPO>` ou `--only <PAJ>`.
   (Atenção: `--force` pode reclassificar; rever depois.)

## Regras de ouro
- **Uma regra por tema.** Específica, acionável, sem prolixidade.
- **Anti-alucinação:** todo fundamento jurídico deve ser verificado (autos/jurisprudência),
  nunca inventado.
- **Preferir `regras_atuacao.md`** (dinâmico) a mexer no prompt (que exige deploy).
- A regra deve descrever o ERRO a evitar + a CONDUTA correta — não só "está errado".
