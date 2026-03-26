# Skill: Triagem Processual

## Objetivo
Analisar os documentos do processo recebido e determinar: (1) tribunal de tramitação, (2) tipo de decisão impugnável, (3) recurso(s) cabível(is), (4) viabilidade recursal, (5) recomendação de atuação.

## Procedimento

### Passo 0 — Verificação de integridade dos TXTs convertidos

**ANTES de analisar qualquer documento**, verifique se os TXTs convertidos de PDF estão íntegros. Sinais de conversão com falha:
- Texto interrompido no meio de uma frase
- Decisão sem dispositivo (sem "ante o exposto", "nego seguimento", etc.)
- Páginas marcadas como "[Pagina de assinatura eletronica omitida]" que podem conter conteúdo substantivo
- Argumentação que não faz sentido lógico ou parece incompleta

**Se detectar qualquer desses sinais:** ler o PDF original diretamente (a ferramenta Read suporta PDFs) e comparar com o TXT. O conversor pode ter classificado incorretamente uma página de conteúdo como página de assinatura. NUNCA construir análise jurídica baseada em texto que parece truncado sem antes verificar o original.

### Passo 1 — Identificação do Tribunal
Leia os documentos e identifique:
- **TNU** — indicadores: "Turma Nacional de Uniformização", "Pedido de Uniformização", "PEDILEF", "Juizados Especiais Federais", menções ao RI-TNU, Resolução 586/2019
- **STJ** — indicadores: "Superior Tribunal de Justiça", "Recurso Especial", "REsp", "AREsp", menções ao RI-STJ

### Passo 2 — Identificação da Decisão
Identifique a última decisão relevante proferida no processo:

**Na TNU, distinguir:**
- Decisão monocrática do **Presidente** da TNU (art. 15 do RI-TNU) — tipicamente: não conhecimento, negativa de seguimento, devolução à origem, inadmissão, suspensão
- Decisão monocrática do **Relator** (art. 8º do RI-TNU) — tipicamente: não conhecimento (art. 14, I), negativa de seguimento (art. 14, III), provimento monocrático (art. 14, IV), inadmissão (art. 14, V)
- **Acórdão** da TNU (decisão colegiada) — julgamento pelo Plenário

**No STJ, distinguir:**
- Decisão monocrática do **Relator** — tipicamente: não conhecimento, negativa de provimento, provimento monocrático do REsp ou AREsp
- Decisão monocrática do **Presidente** do STJ — tipicamente em matéria de repetitivos ou administrativa
- Decisão monocrática em matéria **penal** — sujeita a agravo regimental (art. 258)
- **Acórdão** de Turma — julgamento colegiado do REsp, AREsp ou outros

### Passo 3 — Mapeamento dos Recursos Cabíveis
Com base no tribunal e tipo de decisão, consulte a árvore recursal abaixo e liste todos os recursos cabíveis.

---

## Árvore Recursal

### PROCESSO NA TNU

**Decisão monocrática do PRESIDENTE da TNU (art. 15 do RI-TNU):**
- Irrecorrível (art. 15, §1º) → **ARQUIVAMENTO** (modelo padrão)
- Se houver obscuridade, contradição, omissão ou erro material → **Embargos de Declaração** (art. 30)
  - Skill: `/skills/tnu/embargos-declaracao/SKILL.md`

**Decisão monocrática do RELATOR (art. 8º do RI-TNU):**
- **Agravo Interno** (art. 29) — prazo de 15 dias
  - Skill: `/skills/tnu/agravo-interno/SKILL.md`
- **Embargos de Declaração** (art. 30) — prazo de 5 dias
  - Skill: `/skills/tnu/embargos-declaracao/SKILL.md`

**Acórdão da TNU (decisão colegiada):**
- **Embargos de Declaração** (art. 30) — prazo de 5 dias
  - Skill: `/skills/tnu/embargos-declaracao/SKILL.md`
- **Pedido de Uniformização ao STJ** (art. 31) — prazo de 15 dias, quando o acórdão contrariar súmula ou entendimento dominante do STJ
  - Skill: a ser criada futuramente
- **Recurso Extraordinário ao STF** (art. 32) — prazo de 15 dias
  - Skill: a ser criada futuramente

### PROCESSO NO STJ

**Decisão monocrática do RELATOR:**
- **Agravo Interno** (art. 259 do RI-STJ) — prazo de 15 dias
  - Skill: `/skills/stj/agravo-interno/SKILL.md`
- **Embargos de Declaração** (art. 263 do RI-STJ) — prazo de 5 dias
  - Skill: `/skills/stj/embargos-declaracao/SKILL.md`

**Decisão monocrática em matéria PENAL:**
- **Agravo Regimental** (art. 258 do RI-STJ) — prazo de 5 dias
  - Skill: a ser criada futuramente
- **Embargos de Declaração** (art. 263 do RI-STJ)
  - Skill: `/skills/stj/embargos-declaracao/SKILL.md`

**Acórdão de TURMA (em REsp):**
- **Embargos de Declaração** (art. 263 do RI-STJ) — prazo de 5 dias
  - Skill: `/skills/stj/embargos-declaracao/SKILL.md`
- **Embargos de Divergência** (art. 266 do RI-STJ) — quando acórdão de turma em REsp divergir de outro órgão do STJ
  - Skill: `/skills/stj/embargos-divergencia/SKILL.md`
- **Recurso Extraordinário ao STF**
  - Skill: a ser criada futuramente

**Decisão do PRESIDENTE do STJ:**
- **Agravo Interno** (art. 259 do RI-STJ), quando cabível
  - Skill: `/skills/stj/agravo-interno/SKILL.md`
- **Embargos de Declaração** (art. 263 do RI-STJ)
  - Skill: `/skills/stj/embargos-declaracao/SKILL.md`

**Inadmissão do REsp na origem:**
- **Agravo em Recurso Especial — AREsp** (art. 253 do RI-STJ)
  - Skill: `/skills/stj/agravo-resp/SKILL.md`

---

### Passo 4 — Análise de Viabilidade
Para cada recurso cabível, avalie:

**Critérios favoráveis à interposição:**
- Argumento central do recurso anterior não enfrentado pela decisão
- Precedente favorável ignorado (da TNU, do STJ, do STF)
- Súmula ou tese repetitiva aplicada sem considerar elementos distintivos do caso
- Legislação protetiva desconsiderada ou aplicada restritivamente
- Omissão, contradição ou obscuridade na decisão (para embargos de declaração)
- Divergência jurisprudencial atual demonstrável (para embargos de divergência)

**Critérios desfavoráveis:**
- Todos os argumentos adequadamente enfrentados
- Jurisprudência consolidada contra a pretensão sem fato distintivo
- Pretensão que demandaria reexame fático (Súmula 42/TNU, Súmula 7/STJ)
- Falta de prequestionamento (Súmula 211/STJ) sem embargos declaratórios prévios
- Ausência de paradigma válido para cotejo analítico

**Armadilhas processuais a verificar:**
- Súmula 42/TNU ou Súmula 7/STJ: a questão é reexame de provas ou revaloração jurídica?
- Súmula 211/STJ: prequestionamento assegurado? Prequestionamento ficto (art. 1.025 CPC)?
- Teses repetitivas: há espaço para distinguishing?
- Divergência: há paradigma com similitude fática (não apenas de ementas)?
- Intempestividade: verificar prazos

### Passo 5 — Recomendação
Apresente a recomendação em formato estruturado:

```
TRIBUNAL: [TNU / STJ]
DECISÃO: [tipo e autoridade prolatura]
RECURSO(S) CABÍVEL(IS): [lista]
RECOMENDAÇÃO: [ARQUIVAMENTO / RECURSO / VIABILIDADE DUVIDOSA]
RECURSO RECOMENDADO: [qual, se for o caso]
JUSTIFICATIVA: [fundamentação]
RISCOS: [riscos identificados]
```

### Passo 6 — Encadeamento
- Se ARQUIVAMENTO → informe que está prosseguindo para a Skill de arquivamento
- Se RECURSO → informe qual Skill será executada e prossiga
- Se VIABILIDADE DUVIDOSA → apresente a análise e aguarde decisão do Defensor

## Observações
- A triagem deve ser conservadora: na dúvida entre arquivamento e recurso, classificar como "viabilidade duvidosa" e deixar a decisão com o Defensor
- Nunca recomendar recurso manifestamente inadmissível ou protelatório
- Considerar sempre o impacto concreto da decisão sobre o assistido
