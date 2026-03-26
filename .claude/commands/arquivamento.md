Elabore o despacho de arquivamento do PAJ de forma direta e simplificada. Este é um despacho administrativo interno para o sistema da DPU — não é peça judicial.

A decisão pelo arquivamento já foi tomada por João. NÃO faça triagem, NÃO avalie viabilidade recursal, NÃO analise cabimento de recurso, NÃO sugira interposição de recurso. Vá direto para a elaboração do despacho.

## Proibições expressas

- NÃO use `pesquisar.py` — leia o PDF diretamente com a ferramenta Read
- NÃO faça pesquisa jurídica de nenhum tipo
- NÃO execute `validar_peca.py` nem `formatar_peca.py`
- NÃO gere DOCX nem PDF

## Documentos

Os documentos podem estar:
- Em caminho indicado pelo argumento: $ARGUMENTS
- Anexados diretamente na conversa
- Na pasta `Entrada/` (se organizados previamente)

Se $ARGUMENTS estiver vazio e nenhum arquivo foi fornecido, pergunte ao João onde estão os documentos.

## Procedimento

### 1. Leitura dos Documentos
- Leia o PDF diretamente com a ferramenta Read (NÃO use pesquisar.py)
- Se $ARGUMENTS aponta arquivo(s) específico(s), leia SOMENTE esses arquivos (NÃO leia outros da mesma pasta)
- Se $ARGUMENTS aponta uma pasta, leia todos os arquivos da pasta
- Identifique: partes, número do processo, origem, matéria, pretensão, decisão que motiva o arquivamento
- Identifique o tribunal (TNU ou STJ) e quem proferiu a decisão (verificar assinatura eletrônica: "Presidente" = Presidente da TNU; "Juiz Federal" = Relator)

### 2. Elaboração do Despacho

#### Decisão monocrática do Presidente da TNU (art. 15, RI-TNU)

Este é o cenário mais comum e tem argumentação padrão consolidada. Adapte o modelo abaixo ao caso concreto:

---

## Despacho de Arquivamento

Trata-se de Decisão monocrática proferida pelo Ministro Presidente da Turma Nacional de Uniformização nos autos do Pedido de Uniformização de Interpretação de Lei Federal (TURMA) nº [NÚMERO DO PROCESSO], interposto por [NOME DO ASSISTIDO], assistido pela Defensoria Pública da União, em face de [PARTE CONTRÁRIA], com origem no processo nº [NÚMERO ORIGEM].

O Pedido de Uniformização foi apresentado em face de acórdão proferido pela [TURMA RECURSAL DE ORIGEM] que [RESUMO DA DECISÃO RECORRIDA].

O assistido alegou no recurso [SÍNTESE DOS ARGUMENTOS DO PEDILEF].

O Ministro Presidente da TNU [NÃO CONHECEU / NEGOU SEGUIMENTO / INADMITIU] o Pedido de Uniformização, fundamentando que [SÍNTESE DOS FUNDAMENTOS DA DECISÃO].

Diante do [NÃO CONHECIMENTO / NEGATIVA DE SEGUIMENTO / INADMISSÃO] do Pedido de Uniformização pela Presidência da TNU, verifica-se o esgotamento das vias recursais disponíveis.

O artigo 15, § 1º, do Regimento Interno da Turma Nacional de Uniformização estabelece que "Das decisões monocráticas do Presidente não caberá recurso". A jurisprudência do Superior Tribunal de Justiça é pacífica no sentido da irrecorribilidade das decisões monocráticas do Presidente da TNU perante aquela Corte Superior, conforme precedentes: AgRg na Pet 7.549/PR, PUIL: 1146 AM 2019/0007995-0, AgInt no PUIL 1.029/PB, AgInt no PUIL 248/RN, AgInt no PUIL 72/PR, AgRg na Pet 7.554/PR, AgInt no PUIL 857/RN e PUIL: 1758 DF 2020/0128344-0.

Quanto aos embargos de declaração, único recurso em tese cabível contra decisão do Presidente da TNU (art. 30 do RI-TNU), não se verifica na decisão monocrática a ocorrência de omissão, contradição, obscuridade ou erro material que autorizem sua oposição. [FUNDAMENTAÇÃO ESPECÍFICA: explicar por que a decisão não contém vício — ex: "A decisão enfrentou expressamente os fundamentos do recurso, expondo de forma clara as razões da inadmissão. Não houve omissão quanto a argumento central do Pedilef, nem contradição interna na fundamentação."]

Diante do exposto, verifico que estão esgotadas as possibilidades recursais no presente caso, impondo-se o arquivamento do processo de assistência jurídica.

Comunique-se o assistido.

Arquive-se.

---

#### Demais cenários (STJ, acórdão TNU, decisão de relator, etc.)

Para todos os outros casos, siga as diretrizes do **Tipo 2** descritas em `/skills/arquivamento/SKILL.md`. A análise deve ser mais detalhada, fundamentando a inviabilidade de cada recurso em tese cabível naquele caso concreto. NÃO mencione ED.

### 3. Entrega
- Salve como `.html` na subpasta do processo em `Entrada/` (ex: `Entrada/02152/despacho_arquivamento.html`)
- Use HTML básico: `<h2>`, `<h3>`, `<p>`, `<b>`, `<i>` — renderiza direto no sistema web da DPU
- Apresente o texto completo ao João para revisão
- NÃO gere DOCX nem PDF (é despacho administrativo, inserido diretamente no sistema da DPU)
