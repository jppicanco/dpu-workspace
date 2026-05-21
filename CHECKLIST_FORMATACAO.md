# ✅ Checklist de Formatação de Peças

Use este checklist para garantir que todas as peças sejam formatadas corretamente.

---

## Antes de Salvar o Arquivo .txt

### ✅ 1. Marcadores de Formatação

**Verifique se o texto usa os marcadores corretos:**

- [ ] `## Título` para títulos principais (I, II, III...)
- [ ] `### Subtítulo` para subtópicos
- [ ] `> Citação` para citações longas (uma linha por `>`)
- [ ] Linhas em branco separando parágrafos
- [ ] **NENHUM** uso de `**negrito**` ou `*itálico*` (não funciona!)

**Exemplo correto:**
```
## I – INTRODUÇÃO

Primeiro parágrafo.

Segundo parágrafo.

### Subtópico

Texto aqui.

> Citação longa.
```

### ✅ 2. Encoding UTF-8

**Ao salvar o arquivo .txt:**

```python
# ✅ CORRETO
with open('saida/peca.txt', 'w', encoding='utf-8') as f:
    f.write(texto)

# ❌ INCORRETO
with open('saida/peca.txt', 'w') as f:  # Corrompe acentos!
    f.write(texto)
```

---

## Pipeline Obrigatório

### ✅ CHECKPOINT 1: Formatação DOCX/PDF

```python
import sys
sys.path.append(r'skills/_shared/formatacao-docx')
from formatar_peca import criar_documento, salvar_documento

# Ler arquivo da peça
with open('saida/PECA.txt', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Criar documento
doc = criar_documento(
    conteudo_txt=conteudo,
    enderecamento='EXCELENTÍSSIMO SENHOR...',
    titulo_peca='TIPO DA PEÇA',
    subtitulo='Processo nº XXXXX',
    numero_processo='PUIL/REsp XXXXX',
    texto_pedido='Resumo do pedido',
    itens_sumario=['I – Tópico 1', 'II – Tópico 2']
)

# Salvar
salvar_documento(doc, 'PECA_FINAL.docx')
```

**Verifique:**
- [ ] DOCX gerado
- [ ] PDF gerado
- [ ] Tamanho do PDF razoável (>100KB para peças longas)
- [ ] DOCX e PDF copiados para a pasta de entrada do processo

---

## Verificação Final do PDF

### ✅ Checklist de Qualidade

```python
import PyPDF2

with open('saida/PECA_FINAL.pdf', 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    print(f'Páginas: {len(pdf.pages)}')
    print(f'Primeira página:\n{pdf.pages[0].extract_text()[:200]}')
    print(f'Última página:\n{pdf.pages[-1].extract_text()[-200:]}')
```

**Verifique:**
- [ ] Número de páginas correto (não só 1 página!)
- [ ] Acentos corretos (não `�` ou caracteres estranhos)
- [ ] Títulos formatados (negrito + borda dourada)
- [ ] Parágrafos separados (não texto corrido)
- [ ] Barra lateral com Pedido e Sumário
- [ ] Rodapé com PAJ ou número do processo
- [ ] Assinatura presente (João Paulo Gondim Picanço)

---

## Erros Comuns e Soluções

| Erro | Causa | Solução |
|------|-------|---------|
| PDF com 1 página só | Arquivo .txt sem marcadores `##` | Adicionar marcadores e regenerar |
| Acentos corrompidos (�) | Arquivo salvo sem `encoding='utf-8'` | Recriar arquivo com encoding correto |
| Texto sem parágrafos | Faltam linhas em branco | Adicionar linhas em branco entre parágrafos |
| Títulos sem formatação | Usou `**negrito**` em vez de `##` | Substituir por marcadores corretos |
| PDF vazio/corrompido | Arquivo de entrada corrompido | Verificar encoding do arquivo original |

---

## Comandos Rápidos de Diagnóstico

### Verificar encoding de arquivo:
```bash
file -i saida/peca.txt  # Linux/Mac
# Deve mostrar: charset=utf-8
```

### Verificar marcadores no arquivo:
```bash
grep "^##" saida/peca.txt  # Deve listar todos os títulos
```

### Verificar tamanho do PDF:
```bash
ls -lh saida/peca.pdf  # Tamanho em KB
```

### Contar páginas do PDF:
```python
import PyPDF2
with open('saida/peca.pdf', 'rb') as f:
    print(f'Páginas: {len(PyPDF2.PdfReader(f).pages)}')
```

---

## Em Caso de Problemas

1. **Verificar arquivo .txt original:**
   - Tem marcadores `##` e `###`?
   - Foi salvo com `encoding='utf-8'`?
   - Tem linhas em branco entre parágrafos?

2. **Regenerar do zero:**
   - Criar novo arquivo .txt COM marcadores
   - Salvar COM `encoding='utf-8'`
   - Executar pipeline completo

---

**Última atualização:** 2026-02-12
**Versão:** 1.0
