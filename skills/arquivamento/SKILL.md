# Skill: Arquivamento do PAJ

## Objetivo
Elaborar o despacho administrativo de arquivamento do Processo de Assistência Jurídica (PAJ), justificando a inviabilidade recursal ou outro motivo que impeça a continuidade da atuação.

**IMPORTANTE:** O arquivamento NÃO é uma peça dirigida ao Judiciário. É um despacho administrativo interno da DPU, inserido no sistema da Defensoria.

**ATENÇÃO — comando `/arquivar`:** Quando o Defensor acionar esta skill via `/arquivar`, a decisão pelo arquivamento já foi tomada. NÃO fazer triagem, NÃO avaliar viabilidade recursal, NÃO sugerir interposição de recurso. Ir diretamente para a leitura dos documentos e elaboração do despacho.

## ETAPA 0 — Pesquisa Jurídica e Banco de Fontes (OPCIONAL)

Para arquivamentos, a pesquisa jurídica é opcional, mas pode ser útil em casos complexos (Tipo 2):
1. Leia e siga `/skills/pesquisa-juridica/SKILL.md`
2. Gere o Banco de Fontes Verificadas (`saida/banco_fontes_verificadas.json`)
3. Use fontes do Banco durante a redação, marcando citações com `[Fxxx]`

Para arquivamentos simples (Tipo 1 — irrecorribilidade), esta etapa pode ser pulada.

---

## Tipos de Arquivamento

### Tipo 1 — Modelo Padrão: EXCLUSIVO para Decisão Monocrática do Presidente da TNU

**USO RESTRITO:** Este modelo se aplica ÚNICA E EXCLUSIVAMENTE quando a decisão que motiva o arquivamento é decisão monocrática do Presidente da TNU (art. 15 do RI-TNU), irrecorrível por força do §1º. NÃO utilizar este modelo para nenhuma outra hipótese de arquivamento.

**Estrutura do modelo padrão:**
1. Qualificação do despacho: "Despacho de Arquivamento"
2. Contextualização: identificar a decisão monocrática, número do processo, partes, assistido, origem
3. Histórico processual resumido: o que foi pedido na ação originária, o que foi decidido, qual recurso trouxe o processo à TNU
4. Síntese dos argumentos do recurso (Pedilef)
5. Síntese da decisão monocrática do Presidente
6. Fundamentação da irrecorribilidade:
   - Art. 15, §1º do RI-TNU (decisões do Presidente são irrecorríveis)
   - Jurisprudência do STJ sobre irrecorribilidade
7. Análise sobre cabimento excepcional de embargos de declaração:
   - Verificar se há omissão, contradição, obscuridade ou erro material
   - Se não houver, fundamentar a não oposição
8. Conclusão: esgotamento das vias recursais
9. "Comunique-se o assistido."
10. "Arquive-se."

**Modelo de referência (adaptar ao caso concreto):**

---

Despacho de Arquivamento

Trata-se de Decisão monocrática proferida pelo Ministro Presidente da Turma Nacional de Uniformização nos autos do Pedido de Uniformização de Interpretação de Lei Federal (TURMA) nº [NÚMERO DO PROCESSO], interposto por [NOME DO ASSISTIDO], assistido pela Defensoria Pública da União, em face de [PARTE CONTRÁRIA], com origem no processo nº [NÚMERO ORIGEM].

O Pedido de Uniformização foi apresentado em face de acórdão proferido pela [TURMA RECURSAL DE ORIGEM] que [RESUMO DA DECISÃO RECORRIDA].

O assistido alegou no recurso [SÍNTESE DOS ARGUMENTOS DO PEDILEF].

O Ministro Presidente da TNU [NÃO CONHECEU / NEGOU SEGUIMENTO / INADMITIU] o Pedido de Uniformização, fundamentando que [SÍNTESE DOS FUNDAMENTOS DA DECISÃO].

Diante do [NÃO CONHECIMENTO / NEGATIVA DE SEGUIMENTO / INADMISSÃO] do Pedido de Uniformização pela Presidência da TNU, verifica-se o esgotamento das vias recursais disponíveis.

O artigo 15, § 1º, do Regimento Interno da Turma Nacional de Uniformização estabelece que "Das decisões monocráticas do Presidente não caberá recurso". A jurisprudência do Superior Tribunal de Justiça é pacífica no sentido da irrecorribilidade das decisões monocráticas do Presidente da TNU perante aquela Corte Superior, conforme precedentes: AgRg na Pet 7.549/PR, PUIL: 1146 AM 2019/0007995-0, AgInt no PUIL 1.029/PB, AgInt no PUIL 248/RN, AgInt no PUIL 72/PR, AgRg na Pet 7.554/PR, AgInt no PUIL 857/RN e PUIL: 1758 DF 2020/0128344-0.

Quanto aos embargos de declaração, único recurso em tese cabível, não se verifica na decisão monocrática a ocorrência de omissão, contradição, obscuridade ou erro material que autorizem sua oposição, uma vez que [FUNDAMENTAÇÃO ESPECÍFICA DO CASO].

Diante do exposto, verifico que estão esgotadas as possibilidades recursais no presente caso, impondo-se o arquivamento do processo de assistência jurídica.

Comunique-se o assistido.

Arquive-se.

---

**NOTA:** A fundamentação sobre irrecorribilidade perante o STJ (precedentes AgRg na Pet 7.549/PR etc.) também pode ser aproveitada quando a **Turma** (Plenário) da TNU não conhece do recurso, pois o STJ igualmente não admite uniformização nesses casos. Porém, a estrutura e o restante do despacho serão diferentes — usar o Tipo 2 abaixo.

### Tipo 3 — Arquivamento por Vitória

**Aplica-se quando:**
- Acórdão/decisão favorável ao assistido já transitou em julgado, OU
- Acordo homologado e integralmente cumprido pela parte contrária, OU
- Resultado favorável obtido e restando apenas trâmite burocrático (baixa à origem, devolução dos autos) sem qualquer providência jurídica pendente, OU
- **TNU dá provimento ao incidente e determina restituição à Turma Recursal de origem para adequação** (ver regra abaixo)

**REGRA CRÍTICA — TNU dando provimento com restituição à origem:**
Quando a TNU (monocrática ou colegiada) dá provimento ao incidente de uniformização e determina a restituição do feito à Turma Recursal de origem para "adequação do julgado", isso é **VITÓRIA e ENCERRAMENTO da atuação da Categoria Especial**.

- A Categoria Especial (TNU/STJ) NÃO acompanha, NÃO aguarda e NÃO recebe intimação da Turma Recursal — isso é instância de 2ª Categoria
- A adequação pelo TR/JEF é responsabilidade exclusiva da DPU de 1ª Categoria que atuou na origem
- **NUNCA escrever:** "aguardar intimação da Turma Recursal", "acompanhar adequação", "avaliar manifestação quando do julgamento da TR"
- **Ação correta:** Arquivar com vitória + encaminhar ao setor COMUNICAÇÃO para rotear à DPU 1ª Categoria de origem

**Característica distintiva:** NÃO há recurso a combater, prazo a cumprir ou decisão desfavorável. O processo já produziu exatamente o resultado pretendido pela DPU/assistido. O que resta é puramente burocrático.

**Atuação correta da DPU:** Em regra, o Defensor da TNU/STJ não aguarda indefinidamente o trâmite formal de baixa — isso oneraria a caixa com casos já resolvidos. Arquiva-se o PAJ com vitória e remete-se ao Defensor de 1ª categoria atuante na respectiva Turma Recursal (ou 1º grau), que receberá o processo quando efetivamente houver a baixa e tomará as providências cabíveis (execução de custas, habilitação de herdeiros, comunicação ao assistido, etc).

**Distinção com Tipos 1 e 2:**
- Tipo 1/2 = arquiva-se porque NÃO há como vencer
- Tipo 3 = arquiva-se porque JÁ se venceu

**Estrutura:**
1. "Despacho de Arquivamento por Vitória"
2. Contextualização: processo, partes, assistido, origem, instância atual — **identificar explicitamente em qual polo a DPU/assistido figura (recorrente ou recorrido) e quem é a parte contrária**
3. Histórico processual resumido — chegando à decisão/acordo favorável
4. Identificação clara da vitória — **nunca dizer apenas "deu provimento": explicar que o provimento foi dado AO RECURSO DA DPU / DO ASSISTIDO, tornando inequívoco que isso representa vitória para o assistido. Se o recurso foi da parte contrária e foi negado, deixar igualmente claro.**
   - Se acórdão: transcrever dispositivo favorável + data do trânsito em julgado (quando houver)
   - Se acordo: cláusulas relevantes + comprovação de cumprimento
5. Constatação de que não há providência jurídica pendente na TNU/STJ — o que resta é trâmite burocrático (baixa, devolução à origem)
6. Remissão ao Defensor de 1ª categoria atuante na respectiva Turma Recursal (ou, conforme o caso, ao 1º grau) para tomar providências cabíveis quando do retorno dos autos
7. Registro de que o assistido deve ser informado do resultado favorável
8. "Comunique-se o assistido do resultado favorável."
9. "Arquive-se com vitória. Remetam-se os autos ao Defensor de 1ª categoria atuante na [Turma Recursal / Juízo de origem] para as providências cabíveis quando do retorno formal do processo."

**Tom:** técnico, objetivo, mas deixando clara a natureza da vitória.

**Regra: NÃO explicar no despacho a divisão de competências entre categorias da DPU.** Todo defensor sabe disso. Frases como "a atuação desta Defensoria de Categoria Especial, restrita aos Tribunais Superiores..." são desnecessárias e poluem o despacho. Basta encaminhar ao setor COMUNICAÇÃO para as providências — o destinatário entende.

**Regra crítica — comunicação ao assistido:**
- **NÃO comunicar "vitória"** quando o processo retorna a outra instância para adequação (ex: TNU dá provimento e devolve à TR). O assistido leigo vai interpretar que ganhou o pedido principal, quando na verdade o que houve foi apenas a uniformização da tese — o resultado concreto (concessão do benefício, por exemplo) depende ainda da adequação pela TR. Comunicação prematura gera confusão e falsas expectativas.
- **COMUNICAR obrigatoriamente** quando o processo se encerra definitivamente na TNU/STJ — seja vitória (acórdão favorável transitado, provimento que não volta a nenhuma instância) ou derrota (recursos esgotados, sem mais providências cabíveis). Nesse caso não há mais etapas: o assistido precisa saber do resultado final.

**Acompanhamento de trânsito (opcional):** se o trânsito formal ainda não ocorreu mas é questão de tempo, pode-se registrar o PAJ na watchlist de monitoramento automático (ver `/skills/watchlist-transito/SKILL.md` — a ser criada). Isso evita manter o PAJ na caixa ativa sem razão.

### Tipo 2 — Arquivamento Caso a Caso (TODOS os demais cenários)

**Este tipo abrange TODAS as hipóteses de arquivamento que NÃO sejam decisão monocrática do Presidente da TNU.** Inclui, entre outros: arquivamento em processos do STJ, arquivamento após acórdão desfavorável da TNU, arquivamento por inviabilidade de recurso após decisão do relator, e qualquer outro cenário.

**ATENÇÃO:** Estes arquivamentos são substancialmente mais complexos que o modelo padrão. Exigem análise aprofundada, interpretação jurídica detalhada, explicação minuciosa e justificação bem fundamentada das razões de inviabilidade recursal. A qualidade da redação deve ser equivalente à de uma peça jurídica — não é um mero formulário a preencher.

**Estrutura (expandir conforme a complexidade do caso):**
1. "Despacho de Arquivamento"
2. Contextualização: decisão, processo, partes, assistido, origem
3. Histórico processual detalhado: trajetória completa do caso
4. Análise aprofundada da decisão que motiva o arquivamento
5. Para CADA recurso em tese cabível:
   - Identificar o recurso
   - Analisar detalhadamente por que é inviável NAQUELE caso concreto
   - Fundamentar com dispositivos legais, regimentais e jurisprudência
   - Explicar a consequência prática da interposição (por que seria inútil ou prejudicial)
6. Quando o recurso seria em tese cabível mas sem chance real de êxito: demonstrar por que a jurisprudência é consolidada, por que os fatos do caso não permitem distinguishing, por que os argumentos já foram todos enfrentados
7. Impacto para o assistido: reconhecer o que a decisão significa concretamente para o assistido e explicar por que, mesmo assim, não há caminho recursal viável
8. Conclusão: demonstração fundamentada de esgotamento ou inviabilidade das vias recursais
9. "Comunique-se o assistido."
10. "Arquive-se."

**Diretrizes de qualidade:**
- A fundamentação deve ser completa e convincente — como se fosse ser lida por um corregedor ou em sede de reclamação
- Ser específico e concreto: explicar por que cada recurso é inviável NAQUELE caso, com referência aos fatos e fundamentos do processo
- Jamais usar formulações genéricas como "não há recurso cabível" sem explicar detalhadamente por quê
- Se for inviabilidade por mérito (jurisprudência consolidada contra), citar os precedentes específicos e demonstrar que os fatos do caso não se distinguem
- Se for inviabilidade processual (intempestividade, falta de prequestionamento, etc.), indicar o óbice específico com fundamentação
- Demonstrar que a análise foi exaustiva e que nenhuma via recursal foi negligenciada
- Tom objetivo, técnico e respeitoso — é despacho administrativo, mas com qualidade de peça jurídica
- A redação deve ser clara o suficiente para que o assistido (ou seu eventual advogado futuro) compreenda as razões

## Formatação — Regras Obrigatórias para Despacho no SISDPU

**O que NÃO incluir — o SISDPU já tem essas informações:**
- NÃO repetir número do PAJ, nome do assistido ou número do processo no corpo do despacho (estão no sistema)
- NÃO colocar data ao final
- NÃO colocar nome do Defensor ao final
- NÃO colocar cargo ("Defensor Público Federal") ao final
- NÃO colocar ofício ao final
- NÃO incluir cabeçalho institucional

**Estrutura correta:**
```
DESPACHO DE ARQUIVAMENTO [POR VITÓRIA / sem complemento]

[Corpo do despacho em prosa]

Comunique-se [quando cabível]. Arquive-se.
```

**Sobre agravo regimental em decisão monocrática do Presidente da TNU:**
O art. 15, §1º, do RITNU é expresso: "Das decisões monocráticas do Presidente não caberá recurso." O único recurso em tese admissível é embargos de declaração. NUNCA mencionar agravo regimental como recurso cabível contra monocrática do Presidente da TNU — isso é factualmente errado.

- Usar os marcadores de formatação padrão do sistema (`##`, `###`, `>`) para que o DOCX saia com negritos, parágrafos e hierarquia visual correta
- Salvar o .txt intermediário na subpasta de entrada do processo
- Usar `--tipo-peca despacho` no formatar_peca.py

## Pipeline Completo para Arquivamento

```
1. Elaborar texto da peça (.html) com marcadores HTML
2. Entregar .html ao Defensor
```

**Pasta de saída:** Salvar o .html na mesma subpasta dos documentos de entrada do processo — ex: `Entrada/02152/`. NÃO usar a pasta `/saida` genérica.
