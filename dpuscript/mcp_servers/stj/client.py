"""Cliente HTTP para buscar decisoes do STJ (PDF) e extrair texto."""

import re
import httpx
import fitz  # PyMuPDF


async def baixar_e_extrair_decisao(url: str) -> dict:
    """Baixa um PDF de decisao do STJ e extrai o texto.

    O STJ usa uma pagina intermediaria (/mediado/) que retorna HTML com
    um iframe apontando para o PDF real (/documento/). Esta funcao
    detecta a pagina intermediaria e segue para o PDF direto.

    Args:
        url: URL completa (processo.stj.jus.br)

    Returns:
        dict com: conteudo (str), tamanho (int), url (str), erro (str|None)
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")

            # Pagina intermediaria do STJ: HTML com iframe/link para o PDF real
            if "text/html" in content_type:
                url_pdf = _extrair_url_pdf_da_pagina(resp.text, url)
                if not url_pdf:
                    return {
                        "conteudo": "",
                        "tamanho": 0,
                        "url": url,
                        "erro": "Pagina intermediaria sem link para PDF",
                    }
                # Buscar o PDF real
                resp = await client.get(url_pdf)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")

            if "application/pdf" not in content_type:
                return {
                    "conteudo": "",
                    "tamanho": 0,
                    "url": url,
                    "erro": f"Resposta nao e PDF (content-type: {content_type})",
                }

            texto = _extrair_texto_pdf(resp.content)

            if not texto.strip():
                return {
                    "conteudo": "",
                    "tamanho": 0,
                    "url": url,
                    "erro": "PDF sem texto extraivel (possivelmente imagem escaneada)",
                }

            return {
                "conteudo": texto,
                "tamanho": len(texto),
                "url": url,
                "erro": None,
            }

    except httpx.TimeoutException:
        return {"conteudo": "", "tamanho": 0, "url": url, "erro": "Timeout ao baixar PDF do STJ"}
    except httpx.HTTPStatusError as e:
        return {"conteudo": "", "tamanho": 0, "url": url, "erro": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"conteudo": "", "tamanho": 0, "url": url, "erro": str(e)}


def _extrair_url_pdf_da_pagina(html: str, url_original: str) -> str | None:
    """Extrai a URL direta do PDF da pagina intermediaria do STJ.

    O STJ retorna HTML com um iframe e um link 'Clique aqui para download'
    apontando para /processo/dj/documento/?...&formato=PDF
    """
    # Buscar no href do link de download ou no src do iframe
    match = re.search(
        r'(?:href|src)=["\'](/processo/dj/documento/\?[^"\']+)["\']',
        html,
    )
    if match:
        path = match.group(1)
        # Montar URL absoluta
        base = re.match(r'(https?://[^/]+)', url_original)
        if base:
            return base.group(1) + path
    return None


def _extrair_texto_pdf(pdf_bytes: bytes) -> str:
    """Extrai texto de todas as paginas de um PDF usando PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        paginas = []
        for pagina in doc:
            texto = pagina.get_text()
            if texto.strip():
                paginas.append(texto)
        return "\n\n".join(paginas)
    finally:
        doc.close()
