Pesquise jurisprudencia e precedentes vinculantes nas bases do BNP e CJF via MCP.

## Argumento recebido: $ARGUMENTS

---

## Logica de interpretacao

Identifique o modo de operacao pelo $ARGUMENTS:

### MODO 1 — Busca no BNP (quando $ARGUMENTS NAO contem "cjf" e NAO contem "ambos"/"todos")

Use a ferramenta MCP `buscar_precedentes` com:
- `busca`: os termos fornecidos em $ARGUMENTS (remover "bnp" se presente)
- `orgaos`: "STF,STJ" (padrao)
- `tipos`: "RG,RR,SV,SUM" (padrao)
- `max_resultados`: 10

Sintaxe de busca: `+termo` (obrigatorio), `-termo` (excluir), `"frase exata"`.

Apresente os resultados formatados:
- Numero/codigo do precedente
- Tribunal e tipo (RG, RR, SV, SUM)
- Tese fixada ou ementa
- Status (vigente/superado)

Se nenhum resultado relevante, sugira termos alternativos.

---

### MODO 2 — Busca no CJF (quando $ARGUMENTS contem "cjf")

Use a ferramenta MCP `buscar_jurisprudencia_cjf` com os termos fornecidos (remover "cjf" do query).

Apresente os resultados formatados:
- Numero do processo
- Orgao julgador e relator
- Data do julgamento
- Ementa ou trecho relevante

---

### MODO 3 — Busca combinada (quando $ARGUMENTS contem "ambos" ou "todos")

Execute MODO 1 e MODO 2 em sequencia. Apresente os resultados agrupados:

1. **PRECEDENTES VINCULANTES (BNP):** [resultados do BNP]
2. **JURISPRUDENCIA (CJF):** [resultados do CJF]

---

### Apos apresentar resultados

Pergunte ao Joao:
> "Quer que eu adicione algum desses resultados ao Banco de Fontes Verificadas do processo atual?"

Se Joao confirmar, adicione os itens selecionados ao `banco_fontes_verificadas.json` do processo atual (se existir) com marcador `[Fxxx]` sequencial.

---

## Tom e estilo

- Direto, sem formalidades
- Chamar o usuario de "Joao"
- Nunca mostrar dados brutos do XML/JSON — interpretar e formatar
- Se a busca nao retornar resultados, sugerir termos alternativos

## Exemplos de uso

- `/juris +aposentadoria +especial +EPI` → busca BNP
- `/juris cjf pensao por morte` → busca CJF
- `/juris ambos +aposentadoria +especial` → busca BNP + CJF
- `/juris "tema 1066"` → busca BNP por tema especifico
