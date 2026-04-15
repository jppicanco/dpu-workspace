"""
Cliente para a API Publica do DataJud (CNJ).

Consulta processos judiciais por numero CNJ unificado.
API gratuita, sem cadastro, cobre todos os tribunais.
Docs: https://datajud-wiki.cnj.jus.br/api-publica/
"""

import re
import httpx

BASE_URL = "https://api-publica.datajud.cnj.jus.br"
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

HEADERS = {
    "Authorization": f"APIKey {API_KEY}",
    "Content-Type": "application/json",
}

# Mapeamento segmento J.TR -> alias do endpoint
_TRIBUNAL_MAP = {
    "4.01": "trf1",
    "4.02": "trf2",
    "4.03": "trf3",
    "4.04": "trf4",
    "4.05": "trf5",
    "4.06": "trf6",
    "5.01": "stj",
    "5.00": "stf",
}

# Justica estadual (8.XX)
_TRIBUNAL_ESTADUAL = {
    "8.01": "tjac", "8.02": "tjal", "8.03": "tjap", "8.04": "tjam",
    "8.05": "tjba", "8.06": "tjce", "8.07": "tjdf", "8.08": "tjes",
    "8.09": "tjgo", "8.10": "tjma", "8.11": "tjmt", "8.12": "tjms",
    "8.13": "tjmg", "8.14": "tjpa", "8.15": "tjpb", "8.16": "tjpr",
    "8.17": "tjpe", "8.18": "tjpi", "8.19": "tjrj", "8.20": "tjrn",
    "8.21": "tjrs", "8.22": "tjro", "8.23": "tjrr", "8.24": "tjsc",
    "8.25": "tjsp", "8.26": "tjse", "8.27": "tjto",
}
_TRIBUNAL_MAP.update(_TRIBUNAL_ESTADUAL)


def _limpar_numero(numero: str) -> str:
    """Remove formatacao do numero CNJ, deixando so digitos."""
    return re.sub(r"[^0-9]", "", numero)


def _extrair_tribunal(numero: str) -> str | None:
    """Extrai o segmento J.TR do numero CNJ formatado ou puro.

    Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
    Posicoes (sem pontuacao, 20 digitos): J=pos 13, TR=pos 14-15
    """
    digitos = _limpar_numero(numero)
    if len(digitos) != 20:
        return None
    j = digitos[13]
    tr = digitos[14:16]
    return f"{j}.{tr}"


def _get_endpoint(segmento: str) -> str | None:
    """Retorna o alias do endpoint DataJud para o segmento do tribunal."""
    alias = _TRIBUNAL_MAP.get(segmento)
    if alias:
        return f"{BASE_URL}/api_publica_{alias}/_search"
    return None


async def consultar_processo(numero: str) -> dict:
    """Consulta um processo judicial pelo numero CNJ.

    Args:
        numero: Numero no formato CNJ (ex: '5034182-15.2024.4.02.5101')

    Returns:
        dict com dados do processo ou erro.
    """
    digitos = _limpar_numero(numero)
    if len(digitos) != 20:
        return {"erro": f"Numero CNJ invalido (esperados 20 digitos, recebidos {len(digitos)}): {numero}"}

    segmento = _extrair_tribunal(numero)
    endpoint = _get_endpoint(segmento) if segmento else None
    if not endpoint:
        return {"erro": f"Tribunal nao mapeado para segmento '{segmento}' do numero {numero}"}

    query = {
        "query": {
            "match": {
                "numeroProcesso": digitos
            }
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(endpoint, json=query, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return {"erro": f"Processo nao encontrado no DataJud: {numero}", "tribunal": segmento}

    source = hits[0].get("_source", {})
    return _formatar_processo(source, numero)


def _formatar_processo(source: dict, numero_original: str) -> dict:
    """Formata os dados brutos do DataJud em um dict legivel."""
    resultado = {
        "numero": numero_original,
        "classe": source.get("classe", {}).get("nome", ""),
        "codigo_classe": source.get("classe", {}).get("codigo"),
        "sistema": source.get("sistema", {}).get("nome", ""),
        "formato": source.get("formato", {}).get("nome", ""),
        "orgao_julgador": source.get("orgaoJulgador", {}).get("nome", ""),
        "tribunal": source.get("tribunal", ""),
        "grau": source.get("grau", ""),
        "data_ajuizamento": source.get("dataAjuizamento", ""),
        "data_ultima_atualizacao": source.get("dataHoraUltimaAtualizacao", ""),
        "nivel_sigilo": source.get("nivelSigilo"),
    }

    # Assuntos
    assuntos = source.get("assuntos", [])
    if assuntos:
        resultado["assuntos"] = [
            a.get("nome", "") for a in assuntos if a.get("nome")
        ]

    # Movimentacoes (ultimas 20)
    movs = source.get("movimentos", [])
    if movs:
        resultado["total_movimentacoes"] = len(movs)
        resultado["ultimas_movimentacoes"] = [
            _formatar_movimento(m) for m in movs[:20]
        ]

    return resultado


def _formatar_movimento(mov: dict) -> dict:
    """Formata uma movimentacao do processo."""
    entry = {
        "data": mov.get("dataHora", ""),
        "nome": mov.get("nome", ""),
    }
    complementos = mov.get("complementosTabelados", [])
    if complementos:
        entry["complementos"] = [
            f"{c.get('nome', '')}: {c.get('valor', '')}"
            for c in complementos
            if c.get("nome") or c.get("valor")
        ]
    return entry


async def movimentacoes_processo(numero: str, ultimas: int = 20) -> dict:
    """Retorna as movimentacoes de um processo judicial.

    Args:
        numero: Numero CNJ do processo.
        ultimas: Quantidade de movimentacoes a retornar.
    """
    resultado = await consultar_processo(numero)
    if "erro" in resultado:
        return resultado

    movs_completas = resultado.get("ultimas_movimentacoes", [])
    return {
        "numero": numero,
        "classe": resultado.get("classe", ""),
        "orgao_julgador": resultado.get("orgao_julgador", ""),
        "total_movimentacoes": resultado.get("total_movimentacoes", 0),
        "movimentacoes": movs_completas[:ultimas],
    }
