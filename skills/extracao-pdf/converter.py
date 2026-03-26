#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor PDF para TXT com OCR seletivo.

Extrai texto nativo de paginas com texto e aplica OCR (Tesseract)
apenas nas paginas que sao imagem pura. Detecta "armadilhas" onde
cabecalhos/rodapes sao texto nativo mas o conteudo e escaneado.

Adaptado para sistemas EPROC, STJ e PJe.

Uso:
    python skills/extracao-pdf/converter.py arquivo.pdf
    python skills/extracao-pdf/converter.py arquivo1.pdf arquivo2.pdf
    python skills/extracao-pdf/converter.py Entrada/pasta/

Dependencias: PyMuPDF (fitz), pytesseract, Pillow
Tesseract OCR instalado com idioma portugues (por.traineddata)

Versao: 1.0
Data: 2026-03-13
"""

import sys
import os
import io
import re
import time

# Forcar UTF-8 no stdout do Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from pathlib import Path

# Tentar importar pytesseract (opcional — OCR so funciona se instalado)
try:
    import pytesseract
    TESSERACT_DISPONIVEL = True
except ImportError:
    TESSERACT_DISPONIVEL = False

# Configurar caminho do Tesseract no Windows
if TESSERACT_DISPONIVEL:
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    tesseract_encontrado = False
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_encontrado = True
            break
    if not tesseract_encontrado:
        TESSERACT_DISPONIVEL = False

# Limiar: pagina com menos caracteres de conteudo que isso e considerada "imagem"
LIMIAR_TEXTO = 30

# Padroes de cabecalho/rodape que NAO contam como conteudo real
# Adaptado para EPROC, STJ e PJe
PADROES_CABECALHO_RODAPE = [
    # EPROC / TNU / CJF
    "SCES, TRECHO 3",
    "www.cjf.jus.br",
    "turma.uniformi@cjf.jus.br",
    "Poder Judici",
    "CONSELHO DA JUSTI",
    "Turma Nacional de Uniformiza",
    "eproctnu.cjf.jus.br",
    "eproc/externo_controlador",
    # STJ
    "Documento eletr",
    "assinado eletronicamente",
    "Lei 11.419",
    "Codigo de Controle do Documento",
    "Código de Controle do Documento",
    "Publicacao no DJEN",
    "Publicação no DJEN",
    # PJe (compatibilidade)
    "Documento id",
    "Assinado eletronicamente por",
    "ConsultaDocumento",
    "Numero do documento",
    "Número do documento",
    "pje1g.trf",
    "pje2g.trf",
    "pje.trf",
]

# Padroes regex para linhas de rodape (numeros de processo isolados, IDs de documento)
PADROES_REGEX_RODAPE = [
    r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$",  # numero de processo sozinho na linha
    r"^\d{12}\s*\.V\d",                            # ID de documento EPROC
    r"^Signat.rio",                                 # linha de signatario
]

# Padroes que indicam pagina de assinatura eletronica (boilerplate inteiro)
PADROES_ASSINATURA = [
    "codigo verificador",
    "código verificador",
    "codigo CRC",
    "código CRC",
    "consulta_autenticidade",
    "Informacoes adicionais da assinatura",
    "Informações adicionais da assinatura",
]


def linha_e_cabecalho_rodape(linha):
    """Verifica se uma linha e cabecalho/rodape institucional."""
    linha_lower = linha.lower().strip()
    if not linha_lower:
        return True
    # Padroes de texto
    for padrao in PADROES_CABECALHO_RODAPE:
        if padrao.lower() in linha_lower:
            return True
    # Padroes regex
    for padrao_re in PADROES_REGEX_RODAPE:
        if re.match(padrao_re, linha.strip()):
            return True
    return False


def texto_e_apenas_cabecalho(texto):
    """Detecta se o texto extraido e apenas cabecalho/rodape (PDF escaneado com overlay)."""
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    if not linhas:
        return True
    linhas_conteudo = 0
    for linha in linhas:
        if not linha_e_cabecalho_rodape(linha):
            linhas_conteudo += 1
    return linhas_conteudo < 2


def pagina_e_assinatura(texto):
    """Detecta se a pagina inteira e boilerplate de assinatura eletronica."""
    texto_lower = texto.lower()
    matches = sum(1 for p in PADROES_ASSINATURA if p.lower() in texto_lower)
    return matches >= 2


def filtrar_cabecalho_rodape(texto):
    """Remove linhas de cabecalho/rodape do texto extraido."""
    linhas = texto.split("\n")
    linhas_filtradas = []
    for linha in linhas:
        if not linha_e_cabecalho_rodape(linha):
            linhas_filtradas.append(linha)
    # Remover linhas em branco extras no inicio e fim
    resultado = "\n".join(linhas_filtradas).strip()
    return resultado


def pagina_tem_texto(pagina):
    """Verifica se uma pagina tem texto nativo extraivel (nao apenas cabecalho)."""
    texto = pagina.get_text("text").strip()
    if len(texto) <= LIMIAR_TEXTO:
        return False, texto
    if texto_e_apenas_cabecalho(texto):
        return False, texto
    return True, texto


def ocr_pagina(pagina, dpi=300):
    """Renderiza pagina como imagem e aplica OCR."""
    if not TESSERACT_DISPONIVEL:
        return None
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = pagina.get_pixmap(matrix=mat)
    img = Image.open(BytesIO(pix.tobytes("png")))
    texto = pytesseract.image_to_string(img, lang="por")
    return texto.strip()


def converter_pdf(caminho_pdf, caminho_saida=None):
    """Converte PDF para TXT com OCR seletivo. Retorna caminho do TXT."""
    caminho_pdf = Path(caminho_pdf)
    if not caminho_pdf.exists():
        print(f"  ERRO: Arquivo nao encontrado: {caminho_pdf}")
        return None

    if caminho_saida:
        caminho_txt = Path(caminho_saida)
    else:
        caminho_txt = caminho_pdf.with_suffix(".txt")

    doc = fitz.open(str(caminho_pdf))
    total = len(doc)

    print(f"  Arquivo: {caminho_pdf.name}")
    print(f"  Paginas: {total}")
    if not TESSERACT_DISPONIVEL:
        print(f"  AVISO: Tesseract nao disponivel — OCR desabilitado (texto nativo OK)")

    resultado = []
    pags_texto = 0
    pags_ocr = 0
    pags_assinatura = 0
    pags_sem_texto = 0
    inicio = time.time()

    for i, pagina in enumerate(doc):
        num = i + 1
        tem_texto, texto = pagina_tem_texto(pagina)

        if tem_texto:
            # Verificar se e pagina de assinatura eletronica
            if pagina_e_assinatura(texto):
                resultado.append(f"--- Pagina {num}/{total} [assinatura eletronica] ---\n")
                resultado.append("[Pagina de assinatura eletronica omitida]")
                pags_assinatura += 1
            else:
                texto_limpo = filtrar_cabecalho_rodape(texto)
                resultado.append(f"--- Pagina {num}/{total} [texto nativo] ---\n")
                resultado.append(texto_limpo)
                pags_texto += 1
        else:
            # Pagina sem texto nativo (ou so cabecalho) — tentar OCR
            if TESSERACT_DISPONIVEL:
                print(f"    Pagina {num}/{total}: aplicando OCR...", end="", flush=True)
                texto_ocr = ocr_pagina(pagina)
                if texto_ocr:
                    texto_ocr_limpo = filtrar_cabecalho_rodape(texto_ocr)
                    if texto_ocr_limpo:
                        resultado.append(f"--- Pagina {num}/{total} [OCR] ---\n")
                        resultado.append(texto_ocr_limpo)
                        pags_ocr += 1
                        print(" OK")
                    else:
                        resultado.append(f"--- Pagina {num}/{total} [pagina em branco] ---\n")
                        pags_sem_texto += 1
                        print(" (vazia)")
                else:
                    resultado.append(f"--- Pagina {num}/{total} [pagina em branco ou ilegivel] ---\n")
                    pags_sem_texto += 1
                    print(" (ilegivel)")
            else:
                # Sem Tesseract — extrair o que tiver (mesmo que pouco)
                texto_raw = pagina.get_text("text").strip()
                if texto_raw:
                    resultado.append(f"--- Pagina {num}/{total} [texto parcial - sem OCR] ---\n")
                    resultado.append(filtrar_cabecalho_rodape(texto_raw))
                else:
                    resultado.append(f"--- Pagina {num}/{total} [imagem - OCR necessario] ---\n")
                pags_sem_texto += 1

        resultado.append("\n\n")

    doc.close()
    elapsed = time.time() - inicio

    # Salvar TXT
    caminho_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write("".join(resultado))

    # Resumo
    partes = [f"{pags_texto} texto nativo"]
    if pags_ocr > 0:
        partes.append(f"{pags_ocr} OCR")
    if pags_assinatura > 0:
        partes.append(f"{pags_assinatura} assinatura")
    if pags_sem_texto > 0:
        partes.append(f"{pags_sem_texto} sem texto")
    print(f"  Resultado: {' + '.join(partes)}")
    print(f"  Tempo: {elapsed:.1f}s")
    print(f"  Salvo em: {caminho_txt}")

    return str(caminho_txt)


def main():
    if len(sys.argv) < 2:
        print("Uso: python skills/extracao-pdf/converter.py <arquivo.pdf|pasta>")
        print()
        print("Exemplos:")
        print("  python skills/extracao-pdf/converter.py Entrada/processo.pdf")
        print("  python skills/extracao-pdf/converter.py Entrada/2026/Marco/")
        sys.exit(1)

    arquivos = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            arquivos.extend(sorted(p.glob("*.pdf")))
            arquivos.extend(sorted(p.glob("*.PDF")))
        elif p.is_file() and p.suffix.lower() == ".pdf":
            arquivos.append(p)
        else:
            print(f"  Ignorando: {arg}")

    if not arquivos:
        print("Nenhum PDF encontrado.")
        sys.exit(1)

    print(f"=== Conversor PDF para TXT (OCR seletivo) ===")
    print(f"    {len(arquivos)} arquivo(s) para processar\n")

    for pdf in arquivos:
        converter_pdf(pdf)
        print()

    print("=== Concluido ===")


if __name__ == "__main__":
    main()
