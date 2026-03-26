# Skill: Embargos de Divergência no STJ

## Objetivo
Elaborar embargos de divergência contra acórdão de turma do STJ em recurso especial.

## Fundamento Regimental
- Art. 266 do RI-STJ
- Cabem contra acórdão de órgão fracionário que, em recurso especial, divergir do julgamento atual de qualquer outro órgão jurisdicional do STJ
- Hipóteses: ambos acórdãos de mérito (I); ou um de mérito e outro que não conheceu do recurso mas apreciou a controvérsia (II)
- A divergência pode ser na aplicação do direito material ou processual (§2º)
- Podem ser confrontadas teses de recursos e ações originárias (§1º)
- Interrompem o prazo para RE (art. 266-A)

## Observações Processuais Importantes
- O relator pode indeferir liminarmente se intempestivos, se não comprovada a divergência atual, ou negar provimento se contrários a tese repetitiva, IAC, súmula ou jurisprudência dominante (art. 266-C)
- Prova da divergência: certidão, cópia ou citação de repositório, ou reprodução de julgado da internet com fonte (§4º)
- Cabem quando o paradigma é do mesmo órgão fracionário, desde que composição tenha mudado em mais da metade (§3º)

## ETAPA 0 — Pesquisa Jurídica e Banco de Fontes (RECOMENDADA)

Antes de iniciar a elaboração, execute a pesquisa jurídica para compilar fontes verificáveis:
1. Leia e siga `/skills/pesquisa-juridica/SKILL.md`
2. Gere o Banco de Fontes Verificadas (`saida/banco_fontes_verificadas.json`)
3. Apresente o Banco ao Defensor para revisão
4. Use APENAS fontes do Banco durante a redação, marcando cada citação com `[Fxxx]`

Se o Defensor optar por modo rápido, pule esta etapa (o sistema legado continuará funcionando).

---

## Pipeline de Elaboração

### ETAPA 1 — Análise de Cabimento
Verificar pressupostos específicos:
- O acórdão embargado foi proferido em recurso especial?
- Existe divergência ATUAL com outro órgão do STJ?
- O paradigma é válido (acórdão de mérito ou que apreciou a controvérsia)?
- Há similitude fática entre os casos (não apenas de ementas)?
- A divergência é sobre direito material ou processual?

Se os pressupostos não forem atendidos, recomendar ARQUIVAMENTO.

### ETAPA 2 — Cotejo Analítico
Este é o elemento central dos embargos de divergência. Elaborar cotejo detalhado:
- Descrever os FATOS do acórdão embargado
- Descrever os FATOS do acórdão paradigma
- Demonstrar SIMILITUDE FÁTICA entre os casos
- Identificar a TESE JURÍDICA divergente em cada acórdão
- Mostrar que, para fatos semelhantes, foram adotadas soluções jurídicas opostas

**CRÍTICO:** Cotejo analítico exige comparação de FATOS, não apenas de ementas. Embargos de divergência com cotejo apenas de ementas são sistematicamente rejeitados.

### ETAPA 3 — Estrutura de Tópicos e Redação
Seguir o pipeline padrão de múltiplas camadas (rascunho → autoavaliação → revisão crítica), conforme detalhado na Skill de agravo interno.

**Especificidades da redação:**
- Dar centralidade ao cotejo analítico
- Demonstrar que a divergência é atual (paradigma recente ou jurisprudência não superada)
- Se possível, demonstrar que a questão é relevante para além do caso concreto

### ETAPA 4 — Conclusão e Pedidos
- Conhecimento dos embargos de divergência
- Provimento para fazer prevalecer o entendimento do acórdão paradigma
- Especificação do resultado prático pretendido

### ETAPA 5 — Montagem Final
```
EXCELENTÍSSIMOS(AS) SENHORES(AS) MINISTROS(AS)
DA [SEÇÃO / CORTE ESPECIAL] DO SUPERIOR TRIBUNAL DE JUSTIÇA

[Número do processo]
[Partes]

EMBARGOS DE DIVERGÊNCIA
(art. 266 do RI-STJ c/c art. 1.043 do CPC)

[Conteúdo]

CONCLUSÃO E PEDIDOS
[conclusão e pedidos]
```

### ETAPA 6 — Formatação
Via `/skills/formatacao-docx/SKILL.md`. Salvar na subpasta de entrada do processo (ex: `Entrada/02152/`), não em `/saida`.
