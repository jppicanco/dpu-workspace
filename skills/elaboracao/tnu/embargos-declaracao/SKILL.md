# Skill: Embargos de Declaração na TNU

> **OBRIGATORIO CLAUDE OPUS.** Esta skill produz peca judicial intelectual. Teste comparativo 2026-05-21 reprovou Grok (4.3 fast e 4.20-reasoning) para elaboracao deste tipo de peca. Nunca delegar ao Grok no M4. Validacao anti-alucinacao tambem OBRIGATORIA antes de entregar.


## Objetivo
Elaborar embargos de declaração contra decisão proferida no âmbito da Turma Nacional de Uniformização, com pipeline completo de múltiplas camadas de revisão.

## Fundamento Regimental
- Art. 30 do RI-TNU (Res. 586/2019)
- Cabem contra QUALQUER decisão (monocrática do presidente, monocrática do relator, ou acórdão)
- Prazo: 5 dias a contar da intimação
- Hipóteses: omissão, contradição, obscuridade ou erro material
- Interrompem o prazo para interposição de outros recursos (art. 30, §6º)

## Observações Processuais Importantes
- ED contra decisão monocrática: o relator (ou presidente) decide monocraticamente (art. 30, §3º: "se manifestamente incabíveis, o relator os rejeitará de plano")
- ED contra acórdão: serão apresentados em mesa na primeira sessão subsequente (art. 30, §4º)
- Se houver possibilidade de efeitos modificativos sobre súmula ou representativo de controvérsia: inclusão em pauta (art. 30, §5º)

## ETAPA 0 — Pesquisa Jurídica e Banco de Fontes (RECOMENDADA)

Antes de iniciar a elaboração, execute a pesquisa jurídica para compilar fontes verificáveis:
1. Leia e siga `/skills/pesquisa/pesquisa-juridica/SKILL.md`
2. Gere o Banco de Fontes Verificadas (`saida/banco_fontes_verificadas.json`)
3. Apresente o Banco ao Defensor para revisão
4. Use APENAS fontes do Banco durante a redação, marcando cada citação com `[Fxxx]`

Se o Defensor optar por modo rápido, pule esta etapa (o sistema legado continuará funcionando).

---

## Pipeline de Elaboração

### ETAPA 1 — Análise de Cabimento

#### 1.1 — Critério de análise conforme a autoridade prolautora

**Decisão monocrática do PRESIDENTE da TNU (art. 15 do RI-TNU):**

Os embargos de declaração são o ÚNICO recurso cabível contra a decisão monocrática do Presidente da TNU (art. 15, §1º — irrecorribilidade). Por isso, a análise de cabimento deve ser mais cuidadosa e menos rígida com os requisitos formais dos ED.

Nesse caso, adote o seguinte critério:
- Leia o Pedido de Uniformização original e compare com a fundamentação da decisão presidencial
- Pergunte: a decisão enfrentou adequadamente os argumentos centrais do Pedilef? Há ponto relevante que ficou sem resposta?
- Pergunte: a decisão aplicou súmula, tese ou questão de ordem de forma mecânica, sem considerar especificidades do caso concreto?
- Pergunte: a decisão é injusta — ou seja, levaria a um resultado materialmente errado — mesmo que formalmente justificada?
- Se a resposta a qualquer dessas perguntas for "sim", há matéria para embargos, mesmo que o encaixe nos requisitos formais (omissão, contradição, obscuridade) seja por via oblíqua

A estratégia é: se a decisão foi materialmente injusta ou ignorou argumento relevante, encontre o vício formal que acomoda essa crítica — especialmente omissão (argumento não enfrentado) ou obscuridade (fundamento genérico que não esclarece por que o caso concreto se enquadra na jurisprudência citada). Não é necessário que o vício seja gritante; basta que seja sustentável.

**Decisão monocrática do RELATOR ou Acórdão:**

Aplica-se o critério padrão abaixo. Como há outros recursos disponíveis (agravo interno contra o relator; RE ou pedido de uniformização ao STJ contra acórdão), a análise pode ser mais conservadora — interponha ED apenas se o vício for claro e relevante.

---

#### 1.2 — Identificação dos vícios

Analise a decisão embargada e identifique especificamente:

**Omissão (art. 30, caput):**
- Ponto ou questão sobre a qual o julgador deveria ter se pronunciado, de ofício ou a requerimento, e não o fez
- Argumentos do recurso/petição que não foram enfrentados
- Matérias de ordem pública não apreciadas
- Pedidos não analisados

**Contradição (art. 30, caput):**
- Incompatibilidade entre fundamentos da decisão
- Incompatibilidade entre fundamentação e dispositivo
- Afirmações conflitantes dentro da mesma decisão

**Obscuridade (art. 30, caput):**
- Trecho de difícil compreensão ou ambíguo
- Fundamentação que não permite identificar o real fundamento da decisão
- Dispositivo vago ou impreciso

**Erro material:**
- Erro de cálculo, de digitação, de nome, de número de processo
- Equívoco na transcrição de ementa ou dispositivo legal

Para cada vício identificado, registre:
- O trecho exato da decisão onde ocorre
- A natureza do vício (omissão, contradição, obscuridade, erro material)
- O impacto no julgamento

Se nenhum vício for identificado, recomende ARQUIVAMENTO e interrompa o pipeline.

### ETAPA 2 — Estrutura de Tópicos
Elabore a estrutura dos embargos:
- Um tópico por vício identificado (sem sobreposições)
- Cada tópico deve ser autônomo
- Títulos com numeração romana (I, II, III...)
- Títulos nunca começam com "de"

### ETAPA 3 — Redação (para cada tópico)

**3A — Rascunho:**
Redija o tópico observando:
- Partir do trecho específico da decisão onde está o vício
- Demonstrar objetivamente a existência do vício
- Para omissões: indicar exatamente o que deveria ter sido apreciado, citando o dispositivo legal, argumento ou pedido preterido
- Para contradições: colocar lado a lado os trechos contraditórios
- Para obscuridades: demonstrar a ambiguidade e o que precisa ser esclarecido
- Para erros materiais: indicar o erro e a correção necessária
- Quando cabíveis efeitos infringentes (modificativos), fundamentar por que o saneamento do vício conduz à alteração do resultado
- Prosa contínua, sem listas no corpo do texto
- Tom respeitoso e propositivo — nunca atribuir erro ao julgador

**Formulações adequadas para ED:**
- "A decisão foi omissa quanto a..."
- "Há aparente contradição entre o fundamento X e o fundamento Y..."
- "O trecho '...' comporta interpretações distintas, sendo necessário esclarecimento..."
- "Verifica-se erro material na indicação de..."
- "O saneamento da omissão/contradição conduz necessariamente à modificação do resultado, pois..."

**Formulações a evitar:**
- "A decisão errou ao..." / "O julgador incorreu em equívoco..."
- "Não é X, mas sim Y"
- Qualquer formulação que atribua erro diretamente ao julgador

**3B — Autoavaliação:**
Revise o texto verificando:
- Trechos formulaicos ou típicos de produção automatizada
- Citações de precedentes que não constam dos documentos carregados (remover)
- Inferências sem respaldo nos documentos
- Tom inadequado (atribuição de erro ao julgador)
- Conformidade com regras de caixa (minúsculas para cargos, recursos, princípios)

**3C — Revisão Crítica e Reescrita:**
Analise criticamente avaliando:
- Estrutura argumentativa: encadeamento lógico
- Fundamentação: pertinência dos dispositivos e precedentes invocados
- Técnica recursal: os embargos efetivamente apontam vício no art. 30 ou tentam rediscutir o mérito?
- Vulnerabilidades: fragilidades exploráveis em impugnação
- Naturalidade do texto

Produza versão reescrita incorporando melhorias.

### ETAPA 4 — Conclusão e Pedidos
Elabore em dois parágrafos:

**Primeiro parágrafo:** Amarração final — retomar os vícios identificados, conectar à necessidade de saneamento para garantia dos direitos do assistido.

**Segundo parágrafo:** Pedido formal:
- Conhecimento e provimento dos embargos de declaração
- Saneamento dos vícios apontados (especificar cada um)
- Se cabíveis efeitos infringentes: pedido expresso de modificação do resultado
- Se cabível efeito interruptivo: mencionar a interrupção do prazo para outros recursos (art. 30, §6º)

### ETAPA 5 — Síntese Argumentativa
Elabore síntese em 3 a 5 parágrafos de aproximadamente 80 palavras cada, para inserção no início da petição. Deve ser autossuficiente — sua leitura isolada precisa conduzir ao provimento.

### ETAPA 6 — Revisão da Síntese
Analise criticamente a síntese: cobertura argumentativa, autossuficiência, clareza, tom. Produza versão revisada.

### ETAPA 7 — Montagem Final
Monte a peça completa na seguinte estrutura:

```
ENDEREÇAMENTO (adequar conforme a decisão embargada):
- Se contra decisão do Presidente: ao Presidente da TNU
- Se contra decisão do Relator: ao Relator
- Se contra acórdão: à TNU

[Número do processo]
[Partes]

EMBARGOS DE DECLARAÇÃO
(art. 30 do Regimento Interno da TNU — Resolução CJF 586/2019)

SÍNTESE ARGUMENTATIVA
[síntese revisada]

I — [Título do primeiro tópico]
[texto revisado]

II — [Título do segundo tópico]
[texto revisado]

[demais tópicos]

CONCLUSÃO E PEDIDOS
[conclusão e pedidos]
```

### ETAPA 8 — Formatação
Leia e siga `/skills/_shared/formatacao-docx/SKILL.md` para gerar o .docx final. Salve na subpasta de entrada do processo (ex: `Entrada/02152/`), não em `/saida`.
