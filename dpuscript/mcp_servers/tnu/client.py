"""
Cliente para consulta publica de processos no e-Proc da TNU.

Acessa o sistema publico da Turma Nacional de Uniformizacao (CJF)
sem necessidade de autenticacao. Usa httpx para requisicoes HTTP
e parsing do HTML retornado.

Referencia: documentacao/guia_consulta_eproc_tnu.md
"""

import re
import httpx

BASE_URL = "https://eproctnu.cjf.jus.br/eproc"
EXTERNO_URL = f"{BASE_URL}/externo_controlador.php"
CONTROLADOR_URL = f"{BASE_URL}/controlador.php"

TIMEOUT = 45


def _limpar_numero(numero: str) -> str:
    """Remove toda pontuacao do numero CNJ, deixando so digitos."""
    return re.sub(r"[^0-9]", "", numero)


def _html_to_text(html: str) -> str:
    """Converte HTML para texto limpo."""
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


async def consultar_processo(numero: str) -> dict:
    """Consulta dados publicos de um processo na TNU.

    Args:
        numero: Numero CNJ (ex: '5034182-15.2024.4.02.5101')

    Returns:
        dict com dados do processo, eventos e links de documentos.
    """
    digitos = _limpar_numero(numero)
    if len(digitos) != 20:
        return {"erro": f"Numero CNJ invalido (esperados 20 digitos): {numero}"}

    url = (
        f"{EXTERNO_URL}?acao=processo_seleciona_publica"
        f"&num_processo={digitos}"
        f"&acao_origem=processo_consulta_publica"
        f"&acao_retorno=processo_consulta_publica"
    )

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    html = resp.text

    if "Nenhum processo encontrado" in html or len(html) < 500:
        return {"erro": f"Processo nao encontrado na TNU: {numero}"}

    dados = _extrair_dados_processo(html, numero)
    dados["url_consulta"] = url
    return dados


def _extrair_dados_processo(html: str, numero: str) -> dict:
    """Extrai dados estruturados do HTML do e-Proc TNU."""
    dados = {"numero": numero}

    # Converter todo o HTML para texto para facilitar extracao
    text = _html_to_text(html)

    # Classe da acao
    m = re.search(r'Classe da a[çc][ãa]o:\s*(.+?)(?:\n|Processos)', text)
    if m:
        dados["classe"] = m.group(1).strip()

    # Relator
    m = re.search(r'Relator\(a\):\s*(.+?)(?:\n|Classe)', text)
    if m:
        dados["relator"] = m.group(1).strip()

    # Orgao julgador / Colegiado
    m = re.search(r'Colegiado:\s*(.+?)(?:\n|Relator)', text)
    if m:
        dados["colegiado"] = m.group(1).strip()

    # Situacao
    m = re.search(r'Situa[çc][ãa]o:\s*(.+?)(?:\n|rg)', text)
    if m:
        dados["situacao"] = m.group(1).strip()

    # Data de autuacao
    m = re.search(r'Data de autua[çc][ãa]o:\s*(.+?)(?:\n|Situa)', text)
    if m:
        dados["data_autuacao"] = m.group(1).strip()

    # Assuntos
    assuntos = re.findall(r'(\d{6})\s+([^,\n]+?)(?:,\s*[^,\n]+?,\s*DIREITO)', text)
    if assuntos:
        dados["assuntos"] = [f"{cod} - {desc.strip()}" for cod, desc in assuntos]

    # Partes — REQUERENTE, REQUERIDO etc
    partes = []
    for m in re.finditer(r'(REQUERENTE|REQUERIDO|AUTOR|R[EÉ]U|RECORRENTE|RECORRIDO|INTERESSADO)\s*[-–]?\s*([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+)', text):
        nome = m.group(2).strip()
        if len(nome) > 3:
            partes.append({"tipo": m.group(1).strip(), "nome": nome})
    if partes:
        dados["partes"] = partes

    # Eventos e documentos — extrair do HTML diretamente
    eventos = _extrair_eventos(html)
    if eventos:
        dados["eventos"] = eventos
        dados["total_eventos"] = len(eventos)

    return dados


def _extrair_eventos(html: str) -> list[dict]:
    """Extrai eventos da tabela do e-Proc.

    O e-Proc usa tabela com classes infraTrClara/infraTrEscura para eventos.
    Cada evento tem: numero, data/hora, descricao, documentos vinculados.
    """
    eventos = []

    # Encontrar todas as linhas de evento (rows com classe infraTr*)
    # Padrão: <tr class="infraTr..."><td>NUM</td><td>DATA</td><td>DESCRICAO...</td></tr>
    rows = re.findall(
        r'<tr[^>]*class=["\']infraTr(?:Clara|Escura)["\'][^>]*>(.*?)</tr>',
        html, re.DOTALL
    )

    for row_html in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)

        # Evento tipico tem pelo menos 3 cells: numero, data, conteudo
        # Mas precisamos filtrar linhas que nao sao eventos (ex: tabela de assuntos/partes)
        if len(cells) < 2:
            continue

        # Verificar se primeira cell tem um numero de evento
        first_text = re.sub(r'<[^>]+>', '', cells[0]).strip()

        # Eventos tem numero sequencial (1-999) na primeira coluna
        # Excluir codigos de assunto (6 digitos) e outros falsos positivos
        if re.match(r'^\d{1,3}$', first_text) and len(cells) >= 3:
            num = first_text
            data = re.sub(r'<[^>]+>', ' ', cells[1]).strip()
            descricao = _html_to_text(cells[2])

            evento = {
                "numero": num,
                "data": data,
                "descricao": descricao[:500] if descricao else "",
            }

            # Extrair links de documentos de TODAS as celulas (docs podem estar em qualquer coluna)
            row_html_completo = "".join(cells)
            docs = _extrair_links_documentos(row_html_completo)
            if docs:
                evento["documentos"] = docs

            eventos.append(evento)

    return eventos


def _extrair_links_documentos(html_evento: str) -> list[dict]:
    """Extrai links de documentos de um evento."""
    docs = []

    # Normalizar &amp; para & antes de buscar
    html_norm = html_evento.replace("&amp;", "&")
    for m in re.finditer(
        r'acao=acessar_documento(?:_publico)?&doc=([^&"\']+)&evento=([^&"\']+)&key=([^&"\']+)&hash=([^&"\'>\s]+)',
        html_norm
    ):
        # Extrair nome do documento do texto do link
        # Procurar o texto entre > e < logo apos o link
        doc_id = m.group(1)
        evento_id = m.group(2)
        key = m.group(3)
        hash_val = m.group(4)

        # Buscar nome do doc proximo ao link
        pos = m.end()
        nome_match = re.search(r'>([^<]+)<', html_evento[pos:pos+200])
        nome = nome_match.group(1).strip() if nome_match else f"DOC_{doc_id[:8]}"

        docs.append({
            "doc_id": doc_id,
            "evento_id": evento_id,
            "key": key,
            "hash": hash_val,
            "nome": nome,
        })

    return docs


async def listar_documentos(numero: str) -> dict:
    """Lista todos os documentos de um processo na TNU."""
    resultado = await consultar_processo(numero)
    if "erro" in resultado:
        return resultado

    todos_docs = []
    for evento in resultado.get("eventos", []):
        for doc in evento.get("documentos", []):
            todos_docs.append({
                "evento_numero": evento["numero"],
                "evento_data": evento["data"],
                "evento_descricao": evento["descricao"][:100],
                **doc,
            })

    return {
        "numero": numero,
        "total_documentos": len(todos_docs),
        "documentos": todos_docs,
    }


async def ler_documento(doc_id: str, evento_id: str, key: str, hash_val: str, nome_documento: str = "") -> dict:
    """Acessa o conteudo real de um documento do e-Proc.

    Usa acessar_documento_implementacao (AJAX) em vez de acessar_documento_publico.
    """
    url = (
        f"{CONTROLADOR_URL}?acao=acessar_documento_implementacao"
        f"&acao_origem=acessar_documento_publico"
        f"&doc={doc_id}"
        f"&evento={evento_id}"
        f"&key={key}"
        f"&hash={hash_val}"
        f"&nome_documento={nome_documento}"
        f"&termosPesquisados="
    )

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    html = resp.text
    texto = _html_to_text(html)

    if not texto or len(texto) < 50:
        return {
            "erro": "Conteudo do documento vazio ou muito curto.",
            "html_bruto_trecho": html[:500],
        }

    return {
        "nome_documento": nome_documento,
        "conteudo": texto,
        "tamanho_caracteres": len(texto),
    }
