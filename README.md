# DPU Workspace — Guia de Uso no Claude Code

## Instalação

1. Copie toda a pasta `dpu-workspace` para o seu computador, por exemplo:
   `C:\DPU\dpu-workspace\`

2. No Claude Code (app ou PowerShell), navegue até a pasta:
   ```
   cd C:\DPU\dpu-workspace
   ```

3. O Claude Code detectará automaticamente o arquivo `CLAUDE.md` e seguirá suas instruções.

## Como Usar

### Fluxo Básico

**Opção A — Arrastar arquivos direto no Claude Code (mais prático):**
1. Abra o Claude Code na pasta `dpu-workspace`
2. Arraste os PDFs do processo para a janela do Claude Code (no app do Windows)
3. Diga: **"Analise o processo e elabore a peça cabível"**
4. O sistema fará automaticamente: triagem → identificação do recurso → elaboração → formatação
5. A peça pronta estará em `saida\`

**Opção B — Usar a pasta de entrada:**
1. Coloque os PDFs do processo na pasta `entrada\`
2. Abra o Claude Code na pasta `dpu-workspace`
3. Diga: **"Analise o processo na pasta entrada e elabore a peça cabível"**
4. Mesmo fluxo automático

**Opção C — Indicar o caminho do arquivo:**
1. Abra o Claude Code na pasta `dpu-workspace`
2. Diga: **"Analise o arquivo C:\Users\JoaoPaulo\Downloads\processo_123.pdf e elabore a peça cabível"**

### Comandos Úteis

**Análise completa (triagem + elaboração):**
```
Analise o processo na pasta entrada e elabore a peça cabível
```

**Apenas triagem (sem elaborar):**
```
Faça a triagem do processo na pasta entrada
```

**Apenas arquivamento:**
```
Elabore o despacho de arquivamento para o processo na pasta entrada
```

**Com paradigmas (precedentes verificados):**
Coloque os paradigmas na pasta `entrada\` com o prefixo "PARADIGMA" no nome do arquivo, por exemplo: `PARADIGMA_resp_123456.pdf`
```
Analise o processo e os paradigmas na pasta entrada e elabore a peça cabível
```

**Forçar tipo de recurso:**
```
Elabore embargos de declaração contra a decisão do processo na pasta entrada
```

### Estrutura de Pastas

```
dpu-workspace\
├── CLAUDE.md              ← Orquestrador (não editar salvo para ajustes)
├── README.md              ← Este arquivo
├── skills\                ← Skills de cada tipo de peça
│   ├── triagem\           
│   ├── arquivamento\      
│   ├── tnu\               
│   │   ├── embargos-declaracao\
│   │   └── agravo-interno\
│   ├── stj\
│   │   ├── agravo-interno\
│   │   ├── embargos-declaracao\
│   │   ├── embargos-divergencia\
│   │   └── agravo-resp\
│   └── formatacao-docx\
├── regimentos\            ← Regimentos internos (TNU e STJ)
├── entrada\               ← Coloque os PDFs aqui
└── saida\                 ← Peças prontas saem aqui
```

### Dicas
- Limpe a pasta `entrada\` antes de cada novo processo
- Os nomes dos arquivos de saída incluem o tipo de peça e número do processo
- Se o sistema recomendar "viabilidade duvidosa", ele pausará e pedirá sua decisão
- Você pode pedir ajustes na peça gerada antes de formatar o .docx final

### Skills Disponíveis
- ✅ Triagem processual
- ✅ Arquivamento (padrão TNU e caso a caso)
- ✅ Embargos de declaração na TNU
- ✅ Agravo interno na TNU
- ✅ Agravo interno no STJ
- ✅ Embargos de declaração no STJ
- ✅ Embargos de divergência no STJ
- ✅ Formatação .docx
- 🔲 Pedido de uniformização ao STJ (a criar)
- 🔲 Recurso extraordinário ao STF (a criar)
- 🔲 Agravo regimental penal no STJ (a criar)
- 🔲 AREsp detalhado (a criar)

### Criando Novas Skills
Para adicionar um novo tipo de peça:
1. Crie a pasta em `skills\` (ex: `skills\tnu\nova-skill\`)
2. Crie o `SKILL.md` seguindo o padrão das skills existentes
3. Adicione a referência na árvore recursal do `CLAUDE.md`
