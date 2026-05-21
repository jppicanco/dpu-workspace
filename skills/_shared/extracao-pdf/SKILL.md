# SKILL: Extracao de PDF com OCR Seletivo

## Objetivo

Converter PDFs grandes ou escaneados em arquivos TXT legiveis, com OCR seletivo por pagina. Resolve o limite de 20 paginas do Read tool e a incapacidade de ler PDFs escaneados.

---

## Quando Usar

**SEMPRE** — converter todo PDF antes de ler. O conversor e instantaneo para texto nativo (0.0s) e so aplica OCR nas paginas que precisam.

**NAO converter quando:**
- Arquivo ja tem .txt ao lado (ja foi convertido)

---

## Como Invocar

```bash
# Arquivo unico
python skills/_shared/extracao-pdf/converter.py "Entrada/processo.pdf"

# Pasta inteira
python skills/_shared/extracao-pdf/converter.py "Entrada/2026/Marco/"

# Multiplos arquivos
python skills/_shared/extracao-pdf/converter.py arquivo1.pdf arquivo2.pdf
```

**Timeout recomendado:** 600000ms (10 min) para PDFs com muitas paginas escaneadas.

---

## Output

O conversor gera um `.txt` ao lado do PDF original:
- `Entrada/processo.pdf` → `Entrada/processo.txt`

O TXT contem marcadores de pagina:
```
--- Pagina 1/50 [texto nativo] ---
conteudo da pagina...

--- Pagina 2/50 [OCR] ---
conteudo extraido por OCR...

--- Pagina 3/50 [assinatura eletronica] ---
[Pagina de assinatura eletronica omitida]
```

---

## Integracao com pesquisar.py

O `pesquisar.py` detecta automaticamente se existe um `.txt` ao lado do PDF. Se existir, le o TXT em vez do PDF — removendo o limite de 30 paginas.

Fluxo:
```
PDF grande → converter.py → .txt → pesquisar.py le o .txt → Banco de Fontes
```

---

## Comportamento por Tipo de Pagina

| Tipo | Deteccao | Acao |
|------|----------|------|
| Texto nativo | >30 chars de conteudo real | Extrai direto (instantaneo) |
| Escaneada | Pouco/nenhum texto | OCR via Tesseract (~2s/pag) |
| Armadilha | Cabecalho nativo + conteudo escaneado | Detecta e aplica OCR |
| Assinatura | Boilerplate de assinatura eletronica | Marca como omitida |

---

## Sistemas Suportados

Detecta e filtra cabecalhos/rodapes de:
- **EPROC** (TNU, CJF)
- **STJ** (DJe, assinatura eletronica)
- **PJe** (TRFs)

---

## Dependencias

- **PyMuPDF** (fitz) — ja instalado
- **Pillow** — ja instalado
- **pytesseract** — ja instalado
- **Tesseract OCR** — instalador em `%TEMP%\tesseract-installer.exe`
  - Ao instalar, marcar idioma **Portuguese** (por)
  - Sem Tesseract: texto nativo funciona, OCR fica desabilitado

**Versao:** 1.0
**Data:** 2026-03-13
