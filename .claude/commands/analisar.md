Analise os documentos do processo para determinar a atuação cabível (arquivamento ou recurso).

## Documentos

Os documentos podem estar:
- Na pasta `/entrada` (se organizados previamente)
- Em caminho indicado pelo argumento: $ARGUMENTS
- Anexados diretamente na conversa

Se $ARGUMENTS estiver vazio e `/entrada` estiver vazia, pergunte ao João onde estão os documentos.

## Procedimento

Siga RIGOROSAMENTE o fluxo de trabalho do CLAUDE.md:

### 1. Leitura dos Documentos (ETAPA 1 do CLAUDE.md)
- Se $ARGUMENTS aponta arquivo(s) específico(s), leia SOMENTE esses arquivos (NÃO leia outros da mesma pasta)
- Se $ARGUMENTS aponta uma pasta, leia todos os arquivos da pasta
- Identifique e catalogue cada peça processual
- Extraia: partes, número do processo, origem, matéria, pretensão
- Arquivos com "PARADIGMA" no nome são precedentes verificados
- Identifique a TESE JURÍDICA CENTRAL e a MATÉRIA do caso (previdenciário, assistencial, etc.)

### 2. Pesquisa Automática de Precedentes (ETAPA 1.5 do CLAUDE.md)
Execute AUTOMATICAMENTE, sem perguntar ao João:
- **BNP:** Use `buscar_precedentes` com termos extraídos da tese jurídica do caso
- **CJF:** Use `buscar_jurisprudencia_cjf` para buscar jurisprudência relevante
- Integre resultados relevantes ao Banco de Fontes Verificadas
- Se não houver resultados relevantes, informe ao João e prossiga

### 3. Triagem (ETAPA 2 do CLAUDE.md)
- Leia e siga `/skills/triagem/SKILL.md`
- Identifique: tribunal (TNU ou STJ), tipo de decisão, recursos cabíveis
- Avalie a viabilidade recursal
- Consulte os regimentos em `/regimentos/` quando necessário

### 4. Apresentação da Recomendação
Apresente ao João em formato estruturado:

```
TRIBUNAL: [TNU | STJ]
DECISÃO: [tipo, autoridade, data]
MATÉRIA: [previdenciário, assistencial, etc.]
RECURSOS CABÍVEIS: [lista com base legal]
RECOMENDAÇÃO: [ARQUIVAMENTO | RECURSO | VIABILIDADE DUVIDOSA]
RECURSO RECOMENDADO: [qual, se aplicável]
JUSTIFICATIVA: [fundamentação concisa]
RISCOS: [riscos identificados]

PRECEDENTES ENCONTRADOS (BNP/CJF):
- [listar precedentes vinculantes relevantes encontrados]
- [listar jurisprudência relevante encontrada]
- [ou "Nenhum precedente vinculante específico encontrado"]
```

### 5. Aguardar Decisão
- Se ARQUIVAMENTO: aguarde confirmação para prosseguir com a skill de arquivamento
- Se RECURSO: aguarde confirmação para prosseguir com a skill do recurso identificado (os precedentes já estarão no Banco de Fontes para uso na peça)
- Se VIABILIDADE DUVIDOSA: apresente argumentos pró e contra, aguarde decisão do João

NÃO prossiga para a elaboração da peça sem confirmação explícita do João.
