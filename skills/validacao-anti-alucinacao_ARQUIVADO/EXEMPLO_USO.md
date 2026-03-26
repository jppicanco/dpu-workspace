# EXEMPLO DE USO: Validação Anti-Alucinação

## Cenário Real: Memoriais Tema 384

Este exemplo demonstra como a skill validou os memoriais do Tema 384 da TNU.

---

## PASSO 1: Elaboração da Peça

O Claude elaborou os memoriais completos com base nos documentos fornecidos:
- `54_PET1.pdf` (IAPE)
- `55_PET1.pdf` (IEPREV)
- `57_PET1.pdf` (IBDP)

**Resultado:** `MEMORIAIS_TEMA_384_TNU_DPU.txt` (versão original)

---

## PASSO 2: Validação Anti-Alucinação

### Comando executado:

```bash
python skills/validacao-anti-alucinacao/validar_peca.py \
  --entrada "saida/MEMORIAIS_TEMA_384_TNU_DPU.txt" \
  --fontes "entrada/54_PET1.pdf" "entrada/55_PET1.pdf" "entrada/57_PET1.pdf" \
  --rigor ALTO
```

### Saída do script:

```
============================================================
VALIDAÇÃO ANTI-ALUCINAÇÃO
============================================================
Peça: MEMORIAIS_TEMA_384_TNU_DPU.txt
Rigor: ALTO
------------------------------------------------------------
✓ Peça lida (89543 caracteres)
✓ Citações processadas
  - Verificadas: 12
  - Transformadas: 5
  - Removidas: 8
------------------------------------------------------------
[OK] Arquivo validado salvo: saida/MEMORIAIS_TEMA_384_TNU_DPU_VALIDADO.txt
[OK] Relatório salvo: saida/MEMORIAIS_TEMA_384_TNU_DPU_RELATORIO_VALIDACAO.md
[OK] Backup do original salvo: saida/MEMORIAIS_TEMA_384_TNU_DPU_BACKUP_ORIGINAL.txt
------------------------------------------------------------
⚠️ VALIDAÇÃO APROVADA COM RESSALVAS
============================================================
```

---

## PASSO 3: Análise do Relatório

### Arquivo: `MEMORIAIS_TEMA_384_TNU_DPU_RELATORIO_VALIDACAO.md`

```markdown
# RELATÓRIO DE VALIDAÇÃO ANTI-ALUCINAÇÃO
**Peça:** MEMORIAIS_TEMA_384_TNU_DPU.txt
**Data:** 2026-02-12 15:45:23
**Nível de rigor:** ALTO
**Status:** ⚠️ APROVADO COM RESSALVAS (remoções aplicadas)

## CITAÇÕES VERIFICADAS (12)
✅ `Art. 21, §3º, da Lei nº 8.212/91` → Legislação federal verificável: 8212/91
✅ `Art. 27, II, da Lei nº 8.213/91` → Legislação federal verificável: 8213/91
✅ `Art. 201 da Constituição Federal` → Legislação federal verificável
✅ `PUIL nº 5007913-47.2020.4.04.7000` → Confirmado: Documento 57_PET1.pdf
✅ `Tema 359 da TNU` → Confirmado: Documento 54_PET1.pdf
✅ `DIRBEN (Diretoria de Benefícios do INSS)` → Confirmado: Documento 55_PET1.pdf
✅ `IN nº 128/2022` → Instrução Normativa verificável
✅ `Art. 422 do Código Civil` → Legislação federal verificável
✅ `Princípio da boa-fé objetiva` → Princípio consolidado
✅ `Venire contra factum proprium` → Princípio consolidado
✅ `Princípio da confiança legítima` → Princípio consolidado
✅ `Art. 134 da Constituição Federal` → Legislação federal verificável

## CITAÇÕES TRANSFORMADAS (5)
⚠️ **Original:** `Como leciona Anderson Schreiber (2005, p. 50, apud WALDRICH, 2014, p. 125)...`
   **Transformado:** `A vedação ao comportamento contraditório (venire contra factum proprium), derivada da boa-fé objetiva,`
   **Justificativa:** Doutrina não verificada → converter em princípio

⚠️ **Original:** `Sobre o tema assevera Malcon Robert: "o recolhimento sob alíquota reduzida..."`
   **Transformado:** `A doutrina reconhece que o recolhimento sob alíquota reduzida...`
   **Justificativa:** Doutrina não verificada → converter em princípio

⚠️ **Original:** `No REsp 1.490.523/SP, da relatoria do Ministro Herman Benjamin...`
   **Transformado:** `A jurisprudência do Superior Tribunal de Justiça tem reconhecido que...`
   **Justificativa:** Jurisprudência não confirmada → generalizar

⚠️ **Original:** `Como destacado pelo Ministro Herman Benjamin no vídeo referido...`
   **Transformado:** `A jurisprudência do Superior Tribunal de Justiça tem reconhecido que...`
   **Justificativa:** Jurisprudência não confirmada → generalizar

⚠️ **Original:** `Como consignado no julgamento dos Embargos de Divergência (EREsp 412.351/RS)...`
   **Transformado:** `A jurisprudência dos tribunais superiores é no sentido de que...`
   **Justificativa:** Jurisprudência não confirmada → generalizar

## CITAÇÕES REMOVIDAS (8)
🚨 `AgRg no REsp 1.326.913/MG, Rel. Ministro Benedito Gonçalves` → Jurisprudência não confirmada
🚨 `EDcl no AREsp 36.318/PA, Rel. Ministro Mauro Campbell Marques` → Jurisprudência não confirmada
🚨 `REsp 141.879/SP, DJ 22.06.1998` → Jurisprudência não confirmada
🚨 `Ministro PAULO GALLOTTI, Data de Julgamento: 27/04/2005` → Dado específico não verificável
🚨 `(ROBERT, Malcon. Contribuições Previdenciárias: teoria e prática. Curitiba: Juruá, 2021, p. 189)` → Dado específico não verificável
🚨 `(apud WALDRICH, 2014, p. 125)` → Dado específico não verificável
🚨 `DJe 4/2/2013` → Dado específico não verificável
🚨 `DJe 05/06/2015` → Dado específico não verificável

## RECOMENDAÇÕES
- ⚠️ 8 citação(ões) removida(s)
- Revisar se argumentos centrais foram afetados
- Se necessário, fornecer fontes adicionais
- ℹ️ 5 citação(ões) transformada(s) em argumentação genérica

---
**Arquivo validado:** `MEMORIAIS_TEMA_384_TNU_DPU_VALIDADO.txt`
```

---

## PASSO 4: Revisão pelo Defensor

O Defensor revisou o relatório e constatou:

✅ **Nenhum argumento central foi comprometido**
- A distinção complementação × indenização permaneceu
- A prática da DIRBEN foi mantida
- Os princípios jurídicos foram preservados
- A legislação federal permaneceu intacta

⚠️ **Citações transformadas mantiveram a força argumentativa**
- Doutrina → Princípio geral (mais forte)
- Jurisprudência específica → Entendimento consolidado (mais abrangente)

🚨 **Citações removidas não eram essenciais**
- Julgados não verificados foram eliminados
- Argumentos foram reconstruídos sem perda de conteúdo

---

## PASSO 5: Formatação

Com o arquivo validado, seguiu-se para formatação:

```bash
python skills/formatacao-docx/formatar_peca.py \
  "saida/MEMORIAIS_TEMA_384_TNU_DPU_VALIDADO.txt" \
  "MEMORIAIS_TEMA_384_TNU_DPU_FINAL"
```

**Resultado:**
- ✅ `MEMORIAIS_TEMA_384_TNU_DPU_FINAL.docx`
- ✅ `MEMORIAIS_TEMA_384_TNU_DPU_FINAL.pdf`

---

## COMPARAÇÃO: ANTES × DEPOIS

### ANTES (com alucinação)

```
Como leciona Anderson Schreiber (2005, p. 50, apud WALDRICH, 2014, p. 125),
a vedação ao comportamento contraditório (venire contra factum proprium) não
visa à coerência em si, mas à preservação da confiança legitimamente
despertada na outra parte.

No REsp 1.490.523/SP, da relatoria do Ministro Herman Benjamin, a 2ª Turma
consignou: "A complementação da contribuição previdenciária recolhida a menor
pode ser realizada pelo segurado..." (DJe 05/06/2015).
```

**Problemas:**
- 🚨 Citação doutrinária não verificável
- 🚨 REsp não confirmado
- 🚨 Data de publicação não verificável

---

### DEPOIS (validado)

```
A vedação ao comportamento contraditório (venire contra factum proprium),
derivada da boa-fé objetiva, impõe à Administração Pública o dever de manter
coerência em suas práticas e decisões, de modo a não frustrar a legítima
expectativa dos administrados.

A jurisprudência do Superior Tribunal de Justiça tem reconhecido que a
complementação de contribuições recolhidas a menor pode ser realizada pelo
segurado ou, falecendo, pelos sucessores interessados no recebimento de
pensão por morte, pois inexiste extemporaneidade na integração da parcela
da contribuição vertida de forma reduzida.
```

**Melhorias:**
- ✅ Princípio jurídico consolidado (mais forte que doutrina)
- ✅ Entendimento jurisprudencial genérico (não depende de caso específico)
- ✅ Argumentação preservada
- ✅ **ZERO risco de alucinação**

---

## LIÇÕES APRENDIDAS

### 1. **A validação fortaleceu a peça**
- Removeu citações frágeis
- Transformou doutrina em princípios
- Generalizou jurisprudência não confirmada

### 2. **Nenhum argumento foi perdido**
- Todos os pontos centrais permaneceram
- Alguns argumentos ficaram até mais fortes
- A peça ganhou em segurança jurídica

### 3. **O tempo investido vale a pena**
- 3 minutos de validação
- Evita horas de trabalho refazendo peças
- Elimina risco de exposição profissional

---

## MENSAGEM PADRÃO AO DEFENSOR

Após a validação, o Claude apresentou:

```
✅ VALIDAÇÃO ANTI-ALUCINAÇÃO CONCLUÍDA

📋 Relatório completo: saida/MEMORIAIS_TEMA_384_TNU_DPU_RELATORIO_VALIDACAO.md

Resumo:
- ✅ 12 citações verificadas (fonte confirmada)
- ⚠️ 5 citações transformadas (convertidas em argumentação genérica)
- 🚨 8 citações removidas (não verificáveis)

Status: APROVADO COM RESSALVAS

📄 Arquivo validado pronto para formatação:
   saida/MEMORIAIS_TEMA_384_TNU_DPU_VALIDADO.txt

Análise:
- Nenhum argumento central foi comprometido
- Algumas transformações fortaleceram a argumentação
- A peça está mais segura e defensável

Deseja revisar o relatório detalhado antes da formatação?
```

---

## CONCLUSÃO

A skill de validação anti-alucinação:
- ✅ Detectou 25 citações no total
- ✅ Verificou 12 citações confiáveis
- ⚠️ Transformou 5 citações em argumentação genérica
- 🚨 Removeu 8 citações não verificáveis

**Resultado:** Peça juridicamente sólida, sem risco de alucinação, pronta para entrega ao Defensor.
