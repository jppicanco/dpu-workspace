---
description: Captura uma correção de erro do Grok numa regra estruturada para ele não repetir
---

O Grok (decisão automática no M4) cometeu um erro que descobrimos. Sua tarefa é
**ensiná-lo a não repetir** — siga a skill `skills/ensinar-grok/SKILL.md`.

Erro / correção a registrar: $ARGUMENTS

Passos:
1. Entenda o erro e a correção. Se faltar fundamento jurídico, **pergunte** — não presuma.
2. Confirme o fundamento com pesquisa real (MCP cjf/bnp) se for questão jurídica. Nunca invente.
3. Decida ONDE registrar (regras_atuacao.md (padrão) / modelo_arquivamento.md / prompt do decidir_grok.py).
4. Escreva a regra no formato canônico (ERRO COMUM / REALIDADE / REGRA / Exemplo / Origem: JP correção em <data>).
5. Sincronize pro M4 (`scp` para `/Users/macmini/dpu-workspace/dpuscript/memory/`).
6. Registre no log `dpuscript/memory/correcoes_grok.log`.
7. Commit + push. Se houver PAJs já afetados, ofereça regenerar.
