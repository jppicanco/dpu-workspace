# SKILL: Pesquisa Juridica e Banco de Fontes Verificadas

## Objetivo

Realizar pesquisa juridica abrangente e compilar um **Banco de Fontes Verificadas** antes da elaboracao de qualquer peca juridica. O Banco e a UNICA fonte de verdade para citacoes diretas na peca.

**Principio fundamental:** TODA citacao direta (decisao, sumula, doutrina, dado estatistico) DEVE ter fonte verificavel. Sem fonte verificavel = NAO CITAR.

---

## Quando Usar

**RECOMENDADO** antes de iniciar a elaboracao de qualquer peca juridica (agravo interno, embargos de declaracao, memoriais, etc.).

Esta skill deve ser executada **ANTES** da triagem ou, no minimo, **ANTES** de iniciar a redacao da peca.

Se o Defensor optar por modo rapido (sem pesquisa), o sistema continua funcionando — mas sem o Banco, as citacoes devem ser controladas pela regra de ouro (sem fonte verificavel, nao cite).

---

## Pipeline Correto

```
1. Receber documentos do processo
2. PESQUISA JURIDICA (esta skill)
   2a. Extracao de citacoes dos PDFs (pesquisar.py)
   2b. Pesquisa de precedentes vinculantes (BNP via MCP)
   2c. Pesquisa de jurisprudencia unificada (CJF via MCP)
   2d. Verificacao de legislacao (Planalto)
3. Gerar Banco de Fontes Verificadas
4. Apresentar Banco ao Defensor para revisao
5. Elaborar peca (usando APENAS fontes do Banco)
6. Formatacao DOCX/PDF (com notas de rodape das fontes)
7. Copiar DOCX/PDF para pasta de entrada do processo
```

---

## Fases da Pesquisa

### FASE 1 — Extracao dos Documentos Fornecidos

Extrair citacoes verificaveis dos PDFs fornecidos pelo Defensor (pasta `/entrada` ou anexos).

**O que extrair:**
- Numeros de processos citados (REsp, AgRg, PUIL, PEDILEF, etc.)
- Sumulas e teses mencionadas
- Nomes de ministros/relatores
- Dispositivos legais citados
- Trechos de ementas ou acordaos
- Dados estatisticos com fonte

**Para cada citacao encontrada, registrar:**
- Texto exato da citacao
- Documento de origem (nome do PDF)
- Pagina onde foi encontrada
- Contexto (trecho ao redor)

**Arquivos marcados como "PARADIGMA"** sao precedentes verificados pelo Defensor — extrair integralmente como fontes de alta confianca.

### FASE 2 — Pesquisa de Precedentes Vinculantes (BNP via MCP)

Usar a ferramenta MCP `buscar_precedentes` para buscar precedentes vinculantes no Banco Nacional de Precedentes (BNP) do CNJ.

**Ferramenta:** `buscar_precedentes`
**Parametros:**
- `busca` (string): Query de busca usando sintaxe BNP
- `orgaos` (string, padrao: "STF,STJ"): Orgaos separados por virgula
- `tipos` (string, padrao: "RG,RR,SV,SUM"): Tipos de precedente
- `max_resultados` (int, padrao: 10): Maximo de resultados (1-50)

**Sintaxe de busca BNP:**

| Operador | Funcao | Exemplo |
|----------|--------|---------|
| `+termo` | Palavra obrigatoria (AND) | `+pensao +morte` |
| `-termo` | Palavra excluida (NOT) | `+servidor -militar` |
| `"frase"` | Frase exata | `"pensao por morte"` |
| `termo` | Busca simples | `aposentadoria` |

**ATENCAO:** Os operadores booleanos E, OU, NAO, AND, OR, NOT **NAO** funcionam no BNP. Use apenas `+termo` e `-termo`.

**Estrategia de busca progressiva (do especifico ao geral):**
1. Se o numero do tema e conhecido: `"tema 1066"`
2. Instituto juridico especifico: `+aposentadoria +especial +EPI`
3. Termos mais amplos: `+aposentadoria +especial`
4. Generico: `+previdenciario +aposentadoria`

**Hierarquia de precedentes (prioridade):**

| Prioridade | Tipo | Forca vinculante |
|-----------|------|------------------|
| 1 | RG (Repercussao Geral — STF) | Vinculante erga omnes |
| 2 | RR (Recurso Repetitivo — STJ) | Vinculante |
| 3 | SV (Sumula Vinculante — STF) | Vinculante |
| 4 | SUM (Sumula — STF/STJ) | Altamente persuasivo |
| 5 | IRDR/IAC/PUIL | Persuasivo |

**Para cada precedente encontrado, registrar no Banco:**
- Citacao completa (tipo, numero, orgao, tese)
- Tipo de precedente (RG, RR, SV, SUM, etc.)
- Status (vigente, superado, distinguido)
- URL de verificacao (quando disponivel)
- Confianca: ALTA (se URL disponivel), MEDIA (se apenas referencia textual)

**Ferramenta auxiliar:** `gerar_relatorio_precedentes` — gera relatorio formatado em Markdown dos resultados. Usar quando o Defensor quiser revisar os precedentes encontrados antes de incluir no Banco.

### FASE 3 — Pesquisa de Jurisprudencia Unificada (CJF via MCP)

Usar a ferramenta MCP `buscar_jurisprudencia_cjf` para buscar jurisprudencia na base unificada do CJF (abrange STF, STJ e todos os TRFs).

**Ferramenta:** `buscar_jurisprudencia_cjf`

**O que pesquisar:**
- Julgados citados nos documentos do processo (confirmar existencia)
- Julgados relevantes sobre a materia (temas repetitivos, sumulas)
- Teses fixadas em recursos repetitivos
- Decisoes de TRFs que reforcem a tese

**Para cada julgado encontrado, registrar:**
- Numero completo do processo
- Orgao julgador (turma, secao)
- Relator
- Data de julgamento
- Ementa ou trecho relevante
- URL de acesso ao inteiro teor (quando disponivel)

**REGRA CRITICA:** Jurisprudencia sem URL verificavel ou sem referencia rastreavel nos documentos NAO ENTRA no Banco com confianca ALTA.

### FASE 4 — Verificacao de Legislacao

Verificar e complementar legislacao relevante em fontes oficiais.

**Sites autorizados:**
- planalto.gov.br (legislacao federal)
- normas.leg.br (normas complementares)

**O que pesquisar:**
- Dispositivos legais citados nos documentos
- Legislacao correlata a materia do processo
- Verificar se a redacao citada esta vigente

**Para cada legislacao, registrar:**
- Dispositivo completo (artigo, paragrafo, inciso)
- URL oficial do Planalto
- Indicacao de vigencia

### FASE 5 — Compilacao do Banco de Fontes Verificadas

Reunir todas as fontes das fases anteriores em um unico arquivo JSON estruturado.

**Executar o script para extracao inicial dos PDFs:**
```bash
python skills/pesquisa-juridica/pesquisar.py \
  --fontes "Entrada/XXXXX" \
  --processo "XXXXX-XX.XXXX.X.XX.XXXX" \
  --saida "Entrada/XXXXX/banco_fontes_verificadas.json"
```

O script:
1. Extrai citacoes dos PDFs fornecidos (Fase 1)
2. Gera estrutura JSON inicial do Banco

**Apos o script, Claude deve:**
1. Ler o JSON gerado
2. Adicionar fontes encontradas nas Fases 2, 3 e 4 (MCP + web)
3. Atribuir IDs sequenciais (F001, F002, ...)
4. Salvar JSON atualizado

---

## Estrutura do Banco de Fontes Verificadas

```json
{
  "metadados": {
    "data_geracao": "2026-03-06T21:00:00",
    "processo": "5003886-26.2022.4.04.7202",
    "total_fontes": 15,
    "versao": "2.0"
  },
  "fontes": [
    {
      "id": "F001",
      "tipo": "jurisprudencia",
      "citacao": "REsp 1.234.567/SP, Rel. Min. Fulano, 1a Turma, DJe 15/03/2024",
      "trecho_relevante": "A complementacao retroage a DER...",
      "verificacao": {
        "metodo": "documento",
        "documento": "55_PET1.pdf",
        "pagina": 3
      },
      "confianca": "ALTA"
    },
    {
      "id": "F002",
      "tipo": "legislacao",
      "citacao": "Art. 21, par. 3o, Lei 8.212/91",
      "trecho_relevante": "texto do dispositivo...",
      "verificacao": {
        "metodo": "url",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8212cons.htm"
      },
      "confianca": "ALTA"
    },
    {
      "id": "F003",
      "tipo": "precedente_vinculante",
      "citacao": "Tema 999 STJ (Recurso Repetitivo) — Tese: ...",
      "trecho_relevante": "tese fixada pelo colegiado...",
      "verificacao": {
        "metodo": "url",
        "url": "https://pangeabnp.pdpj.jus.br/..."
      },
      "confianca": "ALTA",
      "origem_mcp": "bnp-api"
    },
    {
      "id": "F004",
      "tipo": "sumula",
      "citacao": "Sumula 7/STJ",
      "trecho_relevante": "A pretensao de simples reexame de prova nao enseja recurso especial.",
      "verificacao": {
        "metodo": "url",
        "url": "https://scon.stj.jus.br/SCON/sumulas/..."
      },
      "confianca": "ALTA"
    },
    {
      "id": "F005",
      "tipo": "jurisprudencia_web",
      "citacao": "REsp 1.888.888/CE, Rel. Min. Fulano, 2a Turma, DJe 10/01/2025",
      "trecho_relevante": "ementa relevante...",
      "verificacao": {
        "metodo": "url",
        "url": "https://www.cjf.jus.br/..."
      },
      "confianca": "ALTA",
      "origem_mcp": "cjf-jurisprudencia"
    }
  ]
}
```

### Tipos de fonte aceitos

| Tipo | Descricao | Verificacao obrigatoria |
|------|-----------|------------------------|
| `jurisprudencia` | Julgado extraido dos documentos | documento + pagina |
| `jurisprudencia_web` | Julgado encontrado na web ou via MCP CJF | URL do inteiro teor |
| `precedente_vinculante` | Precedente do BNP (RG, RR, SV, etc.) | URL do BNP ou referencia |
| `legislacao` | Dispositivo legal | URL do Planalto |
| `sumula` | Sumula de tribunal superior | URL oficial |
| `tese_repetitiva` | Tese fixada em repetitivo | URL oficial |
| `doutrina` | Citacao doutrinaria | documento + pagina (livro/artigo nos PDFs) |
| `paradigma` | Precedente verificado pelo Defensor | documento marcado PARADIGMA |

### Niveis de confianca

| Nivel | Criterio |
|-------|----------|
| `ALTA` | Fonte primaria verificavel (URL acessivel ou documento+pagina) |
| `MEDIA` | Fonte indireta mas rastreavel (citacao dentro de outro julgado) |
| `BAIXA` | NAO ACEITAR — descartar antes de incluir no Banco |

**Apenas fontes com confianca ALTA ou MEDIA entram no Banco.**

---

## Apresentacao ao Defensor

Apos compilar o Banco, apresentar ao Defensor:

```
BANCO DE FONTES VERIFICADAS — Processo {numero}

Total de fontes: {n}

PRECEDENTES VINCULANTES ({n}):  [via BNP/MCP]
- [F003] Tema 999 STJ (RR) — Fonte: BNP (pangeabnp.pdpj.jus.br)

JURISPRUDENCIA ({n}):
- [F001] REsp 1.234.567/SP — Fonte: 55_PET1.pdf, p. 3
- [F005] REsp 1.888.888/CE — Fonte: CJF (cjf.jus.br/...)

LEGISLACAO ({n}):
- [F002] Art. 21, par. 3o, Lei 8.212/91 — Fonte: planalto.gov.br

SUMULAS ({n}):
- [F004] Sumula 7/STJ — Fonte: URL (scon.stj.jus.br/...)

PARADIGMAS ({n}):
- [F006] PUIL 5007913-47... — Fonte: PARADIGMA_55_PET1.pdf

Deseja adicionar, remover ou modificar alguma fonte antes de iniciar a redacao?
```

**Aguardar confirmacao do Defensor antes de prosseguir.**

---

## Uso do Banco Durante a Redacao

Ao elaborar a peca, o Claude deve:

1. **Consultar o Banco** antes de cada citacao direta
2. **Usar o marcador `[Fxxx]`** apos cada citacao, onde `xxx` e o ID da fonte no Banco
3. **NAO citar nada** que nao esteja no Banco
4. Se precisar de uma fonte que nao esta no Banco, informar ao Defensor e solicitar inclusao

**Exemplo de redacao com marcadores:**

```
A complementacao de contribuicoes previdenciarias retroage a data de entrada do requerimento[F001], conforme estabelece o art. 21, par. 3o, da Lei 8.212/91[F002]. Nesse sentido, o Superior Tribunal de Justica, no julgamento do Tema 999, fixou tese vinculante no sentido de que o recolhimento complementar nao configura extemporaneidade[F003].
```

Os marcadores `[Fxxx]` serao convertidos em notas de rodape pelo `formatar_peca.py`.

---

## Regras Criticas

### REGRA 1: Sem fonte, nao cite
Qualquer citacao direta (numero de processo, nome de ministro, data de julgamento, dado estatistico, trecho doutrinario) sem entrada correspondente no Banco DEVE ser descartada ou convertida em argumentacao generica.

### REGRA 2: Fonte verificavel significa rastreavel
- URL que pode ser clicada e conferida
- Documento + pagina que pode ser aberta e verificada
- NAO aceitar: "segundo a jurisprudencia", "conforme entendimento consolidado" como fonte

### REGRA 3: Preferencia por fontes primarias
1. Documentos fornecidos pelo Defensor (maxima confianca)
2. Precedentes vinculantes do BNP (API oficial do CNJ)
3. Jurisprudencia do CJF (base unificada oficial)
4. Sites oficiais dos tribunais (URL verificavel)
5. Legislacao oficial (Planalto)
6. Citacao indireta rastreavel (julgado citado dentro de outro julgado nos documentos)

### REGRA 4: Transparencia total
O Defensor deve poder verificar CADA fonte. Nenhuma fonte deve exigir "confianca" no Claude — tudo deve ser conferivel pelo Defensor de forma independente.

### REGRA 5: Na duvida, nao inclua
Se ha qualquer duvida sobre a veracidade ou acessibilidade de uma fonte, NAO inclua no Banco. Prefira ter menos fontes seguras do que muitas fontes duvidosas.

---

---

## Output

Esta skill gera:
1. **`Entrada/XXXXX/banco_fontes_verificadas.json`** — Banco de Fontes (JSON estruturado)
2. **Resumo para o Defensor** — Apresentado na conversa para revisao

**Versao:** 2.0
**Data:** 2026-03-06
