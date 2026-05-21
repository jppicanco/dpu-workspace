#!/usr/bin/env python3
"""
DPU-workspace dpuscript: preparar_pajs.py
=========================================

Coleta automatizada por PAJ novo/movimentado no SISDPU, baixando peças TNU,
decisões STJ/STF e montando pasta completa em Entrada\\dpuscript\\<PAJ>\\
pronta pra o Claude Code MAX trabalhar.

Arquitetura Python puro — zero LLM aqui. Filtros anti-lixo, destaque de
acórdãos, classificação por regra, teor literal incorporado. Toda inferência
jurídica fica com o MAX depois.

Uso:
    .venv\\Scripts\\python.exe preparar_pajs.py              # todos os PAJs novos/movimentados
    .venv\\Scripts\\python.exe preparar_pajs.py --only 2021/039-18791
    .venv\\Scripts\\python.exe preparar_pajs.py --dry-run    # lista alvos, não processa
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ----- Paths -----

SCRIPT_DIR = Path(__file__).resolve().parent
MCP_DIR = SCRIPT_DIR / "mcp_servers"
WORKSPACE = SCRIPT_DIR.parent
ENTRADA_DIR = WORKSPACE / "Entrada" / "dpuscript"
ARQUIVADOS_DIR = WORKSPACE / "Entrada" / "dpuscript_arquivados"
ESTADO_DIR = SCRIPT_DIR / "estado"
ESTADO_FILE = ESTADO_DIR / "pajs_processados.json"
LOG_DIR = SCRIPT_DIR / "logs"
STATE_FILE = LOG_DIR / "state.json"
_RUN_LOG_HANDLE = None  # arquivo do run atual, setado em run()
_RUN_STATE = {}          # estado atual da execucao
ENV_FILE = SCRIPT_DIR / ".env"
EPROC_PROFILE_DIR = SCRIPT_DIR / "eproc_profile"  # se existir → modo TNU autenticado

# sisdpu tem imports relativos internos — precisa do seu dir no sys.path
sys.path.insert(0, str(MCP_DIR / "sisdpu"))
# prazos/ é package local
sys.path.insert(0, str(SCRIPT_DIR))

# ----- Constantes -----

LIMITE_PECAS_TNU = 30  # top N peças TNU por PAJ (sem janela temporal — processos duram anos)
RATE_LIMIT_SISDPU_SEG = 2
TIMEOUT_TOTAL_SEG = 1800  # 30 min pra caixa cheia (peças TNU ampliadas)


# ----- Regex -----

PAJ_REGEX = re.compile(r"^(\d{4})/(\d{3})-(\d+)$")
CNJ_DIGITOS_REGEX = re.compile(r"\d{20}")

# Movimentacoes tautológicas / puramente administrativas — descartar do PROMPT_MAX.
# ATENÇÃO: filtro só aplica a movs FORA do conjunto preservado (top 3 por seq +
# todas dentro de 30 dias antes da data de retorno à caixa). Movs recentes
# passam sempre, mesmo que pareçam "lixo", porque explicam por que o PAJ voltou.
LIXO_PATTERNS = [
    re.compile(r"CANCELADO\s+AUTOMATICAMENTE.*arquivamento", re.IGNORECASE),
    re.compile(r"PAJ\s+em\s+decurso\s+(?:prazo|alterado)", re.IGNORECASE),
    re.compile(r"Decurso\s+inclu[ií]do\s+automaticamente", re.IGNORECASE),
    re.compile(r"^\s*Remessa\s+ao\s+Cart[óo]rio\s*\.?\s*$", re.IGNORECASE),
    re.compile(r"^\s*Despacho\s+cumprido\s*\.?\s*$", re.IGNORECASE),
    re.compile(r"^\s*N[ãa]o\s+Possui\s*\.?\s*$", re.IGNORECASE),
    re.compile(r"Decorrido\s+prazo\s+-\s+Refer\.\s+aos?\s+Eventos?\s*:", re.IGNORECASE),
    re.compile(r"Confirmada\s+a\s+intima[çc][ãa]o\s+eletr[ôo]nica\s+-\s+Refer\.\s+ao\s+Evento", re.IGNORECASE),
    re.compile(r"Publicado\s+no\s+DJE[N]?\s*-?\s*no\s+dia\s+\d{2}/\d{2}/\d{4}", re.IGNORECASE),
    re.compile(r"Disponibilizado\s+no\s+DJE[N]?\s*-?\s*no\s+dia\s+\d{2}/\d{2}/\d{4}", re.IGNORECASE),
]

# Frases que indicam trâmite puro (quando DESCRIÇÃO INTEIRA é isso, sem conteúdo)
TRAMITE_PURO_KEYWORDS = (
    "AGUARDANDO TRAMITA",
    "SEGUE ANEXO MI",
    "DESPACHO CUMPRIDO",
)

# Marcadores de movimentação com teor jurídico relevante (acórdão, decisão, voto)
ACORDAO_PATTERNS = re.compile(
    r"EMENTA|AC[OÓ]RD[AÃ]O|Voto\s+do\s+Relator|"
    r"CONHECER\s+E\s+(?:NEGAR|DAR)|CONHECIDO\s+E\s+(?:DES)?PROVIDO|"
    r"DECIS[AÃ]O\s+MONOCR|JULG(?:OU|ADO)|"
    r"TRANSIT[OA]U?\s+EM\s+JULGADO|"
    r"REMESSA\s+AO\s+STF|REMETIDO\s+AO\s+STF",
    re.IGNORECASE,
)

PRAZO_PATTERN = re.compile(
    r"Prazo:\s*(\d+)\s*dias.*?Status:\s*(ABERTO|FECHADO).*?"
    r"Data\s+final:\s*(\d{2}/\d{2}/\d{4})",
    re.DOTALL | re.IGNORECASE,
)

PARTE_PATTERN = re.compile(
    r"\((REQUERENTE|REQUERIDO|RECORRENTE|RECORRIDO|AUTOR|R[EÉ]U|MPF[^\)]*)\s*-\s*([^\)]+)\)",
    re.IGNORECASE,
)


# ----- Utilitários -----

def load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    # Grava tambem em arquivo, se houver handle aberto
    if _RUN_LOG_HANDLE is not None:
        try:
            _RUN_LOG_HANDLE.write(line + "\n")
            _RUN_LOG_HANDLE.flush()
        except Exception:
            pass


def update_state(**kwargs) -> None:
    """Atualiza o state.json com os campos passados. Mantem os ja existentes."""
    global _RUN_STATE
    _RUN_STATE.update(kwargs)
    _RUN_STATE["atualizado_em"] = datetime.now().isoformat()
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(_RUN_STATE, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def normalizar_paj(paj: str) -> str:
    """'2021/039-18791' -> '2021-039-18791' (safe para path Windows)."""
    return paj.replace("/", "-")


def decompor_paj(paj: str) -> tuple[str, str, str] | None:
    """'2021/039-18791' -> (ano='2021', unidade='39', numero='18791')."""
    m = PAJ_REGEX.match(paj.strip())
    if not m:
        return None
    ano = m.group(1)
    unidade = m.group(2).lstrip("0") or "0"
    numero = m.group(3)
    return ano, unidade, numero


def extrair_cnj(texto: str) -> str | None:
    if not texto:
        return None
    m = re.search(r"\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}", texto)
    if m:
        d = re.sub(r"\D", "", m.group(0))
        if len(d) == 20:
            return d
    m = CNJ_DIGITOS_REGEX.search(re.sub(r"\D", "", texto))
    if m:
        return m.group(0)
    return None


def formatar_cnj(digitos: str) -> str:
    if len(digitos) != 20:
        return digitos
    return f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.{digitos[16:]}"


def parse_data(s: str) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[: max(len(fmt) + 5, 10)], fmt[: len(fmt)])
        except ValueError:
            continue
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


# ----- Parse item da caixa SISDPU -----

def _parse_item(item_raw: str) -> dict | None:
    parts = [p.strip() for p in item_raw.split("\t")]
    header = parts[0] if parts else ""
    m = re.match(r"(\d{4}/\d{3}-\d+)\s*\n?\(?\s*(.*?)\s*\)?$", header, re.DOTALL)
    if not m:
        return None
    paj = m.group(1).strip()
    oficio = m.group(2).replace("E.", "").strip()
    assistido = parts[1] if len(parts) > 1 else ""
    data = parts[2] if len(parts) > 2 else ""
    descricao = parts[-1] if len(parts) >= 5 else ""
    return {
        "paj": paj,
        "oficio": oficio[:120],
        "assistido": assistido[:120],
        "data": data,
        "desc": descricao,
    }


# ----- Estado (dedup) -----

def estado_hash(data: str, desc: str) -> str:
    return hashlib.sha256(f"{data}||{desc[:200]}".encode("utf-8")).hexdigest()[:16]


def carregar_estado() -> dict:
    if not ESTADO_FILE.exists():
        return {"pajs": {}, "ultima_execucao": None}
    try:
        return json.loads(ESTADO_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"WARN estado corrompido ({e}), recriando")
        return {"pajs": {}, "ultima_execucao": None}


def salvar_estado(estado: dict) -> None:
    ESTADO_FILE.parent.mkdir(parents=True, exist_ok=True)
    ESTADO_FILE.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")


def reconciliar_caixa(
    estado: dict,
    itens_caixa: list[dict],
    dry_run: bool = False,
) -> dict:
    """Identifica PAJs órfãos (registrados em estado mas FORA da caixa SISDPU real)
    e move suas pastas pra ARQUIVADOS_DIR.

    PAJ órfão = JP concluiu no SISDPU → saiu da caixa → mas pasta local permanece.

    Args:
        estado: dict com chave "pajs" (PAJs ativos atualmente acompanhados)
        itens_caixa: lista de itens parseados da caixa (cada um com chave "paj")
        dry_run: se True, só lista o que seria movido, não move nada

    Returns:
        dict com:
            - 'orfaos': lista de PAJs órfãos detectados
            - 'arquivados': lista de PAJs efetivamente movidos
            - 'mantidos': PAJs no estado que continuam na caixa
            - 'erros': lista de erros (paj + motivo)
    """
    pajs_caixa = {it["paj"] for it in itens_caixa}
    pajs_estado = set(estado.get("pajs", {}).keys())
    orfaos = sorted(pajs_estado - pajs_caixa)
    mantidos = sorted(pajs_estado & pajs_caixa)

    arquivados: list[str] = []
    erros: list[dict] = []

    if not orfaos:
        log(f"reconciliação: 0 PAJs órfãos ({len(mantidos)} mantidos)")
        return {
            "orfaos": [],
            "arquivados": [],
            "mantidos": mantidos,
            "erros": [],
        }

    log(f"reconciliação: {len(orfaos)} órfãos detectados ({len(mantidos)} mantidos)")
    timestamp = datetime.now(timezone.utc).astimezone().isoformat()

    for paj in orfaos:
        paj_norm = normalizar_paj(paj)
        pasta_origem = ENTRADA_DIR / paj_norm
        pasta_destino = ARQUIVADOS_DIR / paj_norm

        if dry_run:
            existe = "exists" if pasta_origem.exists() else "missing"
            log(f"  [DRY] {paj}: {pasta_origem} ({existe}) -> {pasta_destino}")
            arquivados.append(paj)
            continue

        # Move pasta física se existir
        if pasta_origem.exists():
            try:
                ARQUIVADOS_DIR.mkdir(parents=True, exist_ok=True)
                if pasta_destino.exists():
                    # Já existe destino — adiciona sufixo timestamp pra não sobrescrever
                    pasta_destino = pasta_destino.with_name(
                        pasta_destino.name + "_" + timestamp[:10].replace("-", "")
                    )
                shutil.move(str(pasta_origem), str(pasta_destino))
                log(f"  arquivado: {paj} -> {pasta_destino.name}")
            except Exception as e:
                log(f"  ERRO ao mover {paj}: {e}")
                erros.append({"paj": paj, "erro": str(e)})
                continue
        else:
            log(f"  marcado arquivado (pasta inexistente): {paj}")

        # Move entrada do estado pra pajs_arquivados
        reg = estado["pajs"].pop(paj, {})
        reg["arquivado_em"] = timestamp
        reg["arquivado_motivo"] = "fora_da_caixa_sisdpu"
        estado.setdefault("pajs_arquivados", {})[paj] = reg
        arquivados.append(paj)

    if not dry_run and arquivados:
        salvar_estado(estado)
        log(f"reconciliação: {len(arquivados)} arquivados, {len(mantidos)} mantidos")

    return {
        "orfaos": orfaos,
        "arquivados": arquivados,
        "mantidos": mantidos,
        "erros": erros,
    }


def classificar_paj_estado(paj: str, mov_hash: str, estado: dict) -> str:
    reg = estado.get("pajs", {}).get(paj)
    if not reg:
        return "novo"
    if reg.get("mov_hash") != mov_hash:
        return "movimentado"
    return "inalterado"


# ----- Filtros anti-lixo -----

def mov_e_lixo(mov: dict) -> bool:
    """True se a mov é puramente administrativa/tautológica.

    NOTA IMPORTANTE: essa função é aplicada APENAS em movs fora do conjunto
    "preservado" (top 3 recentes + 30 dias antes da data de retorno à caixa).
    Ver selecionar_movs_preservar().
    """
    desc = (mov.get("descricao") or "").strip()
    if not desc:
        return True
    # Acórdão/decisão nunca é lixo
    if ACORDAO_PATTERNS.search(desc):
        return False
    # Descrição curta e tipo administrativo
    tipo = (mov.get("movimentacao") or "").strip()
    if len(desc) < 60 and tipo in ("Remessa ao Cartório", "Remessa ao Gabinete",
                                    "Cartório", "Gabinete"):
        return True
    # Patterns explícitos de lixo
    for p in LIXO_PATTERNS:
        if p.search(desc):
            return True
    # Trâmite puro: descrição curta + uma das keywords, sem decisão/sentença
    desc_up = desc.upper()
    if len(desc) < 400:
        for kw in TRAMITE_PURO_KEYWORDS:
            if kw in desc_up and not any(k in desc_up for k in ("DECISÃO", "SENTENÇA", "ACÓRDÃO", "DECISAO", "SENTENCA", "ACORDAO")):
                return True
    # MANDADO DE INTIMAÇÃO... encaminhado ao X Ofício (só trâmite interno)
    if re.search(r"MANDADO\s+DE\s+INTIMA[CÇ][AÃ]O\s+N[º°o]", desc, re.IGNORECASE):
        if "ENCAMINHAD" in desc_up and len(desc) < 400:
            return True
    return False


def selecionar_movs_preservar(movs: list[dict], data_caixa_str: str, top_n: int = 3, janela_dias: int = 30) -> set[str]:
    """Retorna conjunto de seqs que devem SEMPRE aparecer no PROMPT_MAX.

    Critério: união de
      (a) as top N movs mais recentes por seq;
      (b) todas as movs datadas até N dias antes da data de retorno à caixa.

    Essas movs são o motivo pelo qual o PAJ voltou pra caixa — o filtro
    anti-lixo NÃO atua sobre elas.
    """
    preservadas: set[str] = set()
    # (a) top N por seq
    for m in sorted(movs, key=_seq_int, reverse=True)[:top_n]:
        preservadas.add(str(m.get("seq", "?")))
    # (b) janela temporal
    data_caixa = parse_data(data_caixa_str) or datetime.now()
    corte = data_caixa - timedelta(days=janela_dias)
    for m in movs:
        dt = parse_data(m.get("data", "") or "")
        if dt and dt >= corte:
            preservadas.add(str(m.get("seq", "?")))
    return preservadas


def mov_tem_acordao(mov: dict) -> bool:
    return bool(ACORDAO_PATTERNS.search(mov.get("descricao") or ""))


def extrair_prazos_abertos(movs: list[dict]) -> list[dict]:
    """Procura prazos ABERTOS com data final futura nas descrições."""
    hoje = datetime.now()
    prazos: list[dict] = []
    for m in movs:
        desc = m.get("descricao") or ""
        for pm in PRAZO_PATTERN.finditer(desc):
            dias, status, data_final_str = pm.group(1), pm.group(2), pm.group(3)
            if status.upper() != "ABERTO":
                continue
            dt = parse_data(data_final_str)
            if not dt or dt < hoje - timedelta(days=1):
                continue
            # Identifica parte
            parte = "não identificada"
            # Janela de 400 chars antes do match pra pegar a parte
            inicio = max(0, pm.start() - 400)
            trecho = desc[inicio:pm.end()]
            pp = PARTE_PATTERN.search(trecho)
            if pp:
                parte = f"{pp.group(1).upper()} {pp.group(2).strip()}"
            prazos.append({
                "seq": m.get("seq", "?"),
                "data_mov": m.get("data", "?"),
                "dias": dias,
                "data_final": data_final_str,
                "parte": parte,
            })
    return prazos


# ----- Classificação por regra -----

def classificar_caso(
    status_paj: str,
    foro: str,
    movs_todas: list[dict],
    movs_relevantes: list[dict],
    desc_caixa: str,
    tem_decisao_baixada: bool,
    conteudos_baixados: list[str] | None = None,
) -> str:
    """Classificação determinística baseada em sinais textuais.

    Analisa o que está nas MOVS RECENTES (últimas 2 por seq desc) pra decidir
    o tipo do caso. Isso é o que explica por que o PAJ voltou à caixa.
    """
    status_up = (status_paj or "").upper()
    desc_up = (desc_caixa or "").upper()

    # Últimas 2 movs por seq (define o que aconteceu recente)
    ultimas = sorted(movs_todas, key=_seq_int, reverse=True)[:2]
    blob_recentes = " ".join((m.get("descricao") or "") for m in ultimas).upper()

    # Conteúdo das peças/decisões baixadas (teor real — onde o despacho diz "Abra-se vista", etc)
    blob_decisoes = " ".join(conteudos_baixados or []).upper()

    # 1. Status ARQUIVADO tem precedência
    if "ARQUIV" in status_up:
        # Trânsito em julgado só quando AFIRMATIVO (não "ocorrência ou não")
        transito_pattern = re.compile(
            r"TRANSITOU\s+EM\s+JULGADO|"
            r"TR[ÂA]NSITO\s+EM\s+JULGADO\s+(?:CONFIRMADO|OCORRIDO|VERIFICADO|CERTIFICADO|EM\s+\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        for m in movs_relevantes:
            dc = (m.get("descricao") or "")
            if transito_pattern.search(dc):
                return "ARQUIVADO_TRANSITADO"
        # STF suspendendo tema
        if "STF" in (desc_up + " " + blob_recentes) and any(k in (desc_up + " " + blob_recentes) for k in ("DEVOLUÇÃO", "DEVOLVER", "AGUARDAR")):
            return "ARQUIVADO_SUSPENSO_TEMA_STF"
        return "ARQUIVADO_TRAMITE_INTERNO"

    # 2. Vista ao MP — olha SISDPU + teor das peças baixadas
    if (re.search(r"VISTA\s+AO\s+(MP|MINIST[ÉE]RIO\s+P[ÚU]BLICO)|ABRA[- ]SE\s+VISTA\s+AO\s+MINIST[ÉE]RIO\s+P[ÚU]BLICO",
                  desc_up + " " + blob_recentes + " " + blob_decisoes)):
        return "VISTA_MP"

    # 3. Inclusão em pauta (intimação de julgamento)
    if re.search(r"INCLU[IÍ]D[OA]?\s+(?:d[eoa]\s+processo\s+)?(?:em|na)\s+pauta|INCLUS[AÃ]O\s+(?:em|na|d[oa])\s+pauta|PAUTA\s+DE\s+JULGAMENTO",
                 desc_up + " " + blob_recentes):
        return "INCLUSAO_EM_PAUTA"

    # 4. Retorno do assistido
    if re.search(r"RETORNO\s+D[OA]\s+ASSISTID|ASSISTID[OA]\s+RETORN|ASSISTID[OA]\s+COMPARECEU",
                 desc_up + " " + blob_recentes):
        return "RETORNO_ASSISTIDO"

    # 5. Retorno automático (PAJ volta sozinho após 1 ano parado)
    # Heurística: últimas 2 movs são ambas puro decurso automático
    if len(ultimas) >= 1:
        decurso_pattern = re.compile(r"DECURSO|CANCELADO\s+AUTOMATICAMENTE", re.IGNORECASE)
        if all(decurso_pattern.search(m.get("descricao") or "") for m in ultimas):
            return "RETORNO_AUTOMATICO_1ANO"

    # 6. Ciência tácita / renúncia ao prazo
    if re.search(r"CI[ÊE]NCIA\s+T[AÁ]CITA|CI[ÊE]NCIA,?\s+COM\s+REN[ÚU]NCIA", desc_up + " " + blob_recentes):
        return "INTIMACAO_SIMPLES_CIENCIA"

    # 7. Decisão STJ/STF/TNU baixada — olha TEOR da peça, não só SISDPU
    if tem_decisao_baixada:
        blob_analise = (blob_recentes + " " + blob_decisoes).upper()

        # Sinais estruturais
        sinal_colegiado = bool(re.search(
            r"POR\s+UNANIMIDADE|POR\s+MAIORIA|"
            r"A\s+TURMA\s+(?:NACIONAL\s+)?(?:DE\s+UNIFORMIZA[CÇ][AÃ]O\s+)?DECIDIU|"
            r"A\s+TURMA\s+(?:RECURSAL\s+)?DECIDIU|"
            r"VOTARAM\s+OS\s+(?:E\.|EXC|EMINENTES)|"
            r"ACORD(?:AM|AO)\s+OS\s+(?:E\.|EXC|MINISTROS|JUIZES|JU[ÍI]ZES|DESEMBARGADORES)",
            blob_analise,
        ))
        sinal_presidente = bool(re.search(
            r"PRESIDENTE\s+(?:D[OA]\s+)?(?:TURMA(?:\s+NACIONAL)?|TNU|STJ|TRIBUNAL)|"
            r"VICE[\s-]*PRESIDENTE|"
            r"DESPACHO\s+PRESIDENCIAL",
            blob_analise,
        ))
        sinal_monocratica = bool(re.search(
            r"DECIS[AÃ]O\s+MONOCR[AÁ]TICA|MONOCRATICAMENTE|DECID[OE]?\s+MONOCRAT|"
            r"RELATOR\s+DECIDE\s+MONOCRAT|DESPACHO\s+MONOCR[AÁ]TICO",
            blob_analise,
        ))
        sinal_desprovido = bool(re.search(
            r"DESPROVID[OA]|NEGAR\s+PROVIMENTO|N[ÃA]O\s+CONHECER|"
            r"N[ÃA]O\s+CONHECID[OA]|INADMITID[OA]|"
            r"PEDIDO\s+(?:DE\s+UNIFORMIZA[CÇ][AÃ]O\s+)?(?:N[AÃ]O\s+CONHECIDO|INADMITIDO)",
            blob_analise,
        ))
        sinal_provimento = bool(re.search(
            r"DOU[\s-]LHE\s+PROVIMENTO|D[AE]RAM?\s+PROVIMENTO|"
            r"CONHE[CÇ]O\s+E\s+DOU\s+PROVIMENTO|PEDIDO\s+CONHECIDO\s+E\s+PROVIDO",
            blob_analise,
        ))

        # 7.1 — Provimento TNU/STJ com restituição à origem → VITÓRIA Cat. Especial
        # Adequação pelo TR/JEF é responsabilidade da DPU 1ª Categoria — NÃO aguardar
        if sinal_provimento and re.search(
            r"RESTITUICAO|RESTITUIÇÃO|RESTITUI[OÃ]\s+DO\s+FEITO|"
            r"ADEQUA[CÇ][AÃ]O\s+DO\s+JULGADO|RETORNO\s+[AÀ]\s+ORIGEM|"
            r"DEVOLU[CÇ][AÃ]O\s+[AÀ]\s+ORIGEM",
            blob_analise,
        ):
            return "ARQUIVADO_VITORIA_PROVIMENTO"

        # 7.2 — Decisão COLEGIADA (turma julgou) — cabe SÓ embargos de declaração
        # se houver omissão/contradição/obscuridade. NÃO cabe agravo interno.
        # (Esta regra resolve o erro histórico onde "RELATOR in blob" pegava acórdãos.)
        if sinal_colegiado:
            if sinal_desprovido:
                if foro == "TNU":
                    return "DECISAO_COLEGIADA_TNU"
                if foro == "STJ":
                    return "DECISAO_COLEGIADA_STJ"
            if sinal_provimento:
                # provimento sem restituição — favorável mas com adequação pendente
                if foro == "TNU":
                    return "DECISAO_COLEGIADA_TNU_PROVIMENTO"
                if foro == "STJ":
                    return "DECISAO_COLEGIADA_STJ_PROVIMENTO"

        # 7.3 — Decisão MONOCRÁTICA do PRESIDENTE/VICE — IRRECORRÍVEL na maioria dos casos
        if sinal_monocratica and sinal_presidente:
            if foro == "TNU":
                return "DECISAO_MONOCRATICA_PRESIDENTE_TNU"
            if foro == "STJ":
                return "DECISAO_MONOCRATICA_PRESIDENTE_STJ"

        # 7.4 — Decisão MONOCRÁTICA do Relator desprovida → cabe agravo interno
        # (removido "RELATOR" como gatilho — todo acórdão menciona)
        if sinal_monocratica and sinal_desprovido and not sinal_presidente:
            if foro == "STJ":
                return "DECISAO_MONOCRATICA_RELATOR_STJ"
            if foro == "TNU":
                return "DECISAO_MONOCRATICA_RELATOR_TNU"
        # Colegiada negando provimento → ED cabem
        if re.search(r"POR\s+UNANIMIDADE.*(?:DESPROVID|NEGAR\s+PROVIMENTO)|"
                     r"CONHECER\s+E\s+NEGAR\s+PROVIMENTO", blob_analise):
            if foro == "STJ":
                return "DECISAO_COLEGIADA_STJ"
            if foro == "TNU":
                return "DECISAO_COLEGIADA_TNU"
        if foro == "STJ":
            return "DECISAO_MERITO_STJ_PENDENTE"
        if foro == "TNU":
            return "DECISAO_MERITO_TNU_PENDENTE"

    # 8. Foro sem decisão baixada
    if foro == "TNU":
        return "AGUARDA_JULGAMENTO_TNU"
    if foro == "STJ":
        return "AGUARDA_JULGAMENTO_STJ"

    return "OUTRO"


# ----- Foro -----

def detectar_foro(sisdpu_det: dict, datajud: dict | None, cnj_digitos: str | None,
                  desc_caixa: str = "") -> str:
    if cnj_digitos and len(cnj_digitos) == 20:
        j, tr = cnj_digitos[13], cnj_digitos[14:16]
        if j == "5" and tr == "01":
            return "STJ"

    textos = [desc_caixa or ""]
    if datajud:
        for k in ("orgao_julgador", "tribunal", "classe"):
            v = datajud.get(k)
            if isinstance(v, str):
                textos.append(v)
    for k, v in (sisdpu_det or {}).items():
        if isinstance(v, str):
            textos.append(v)
    for m in (sisdpu_det or {}).get("movimentacoes", []) or []:
        desc = m.get("descricao", "") or ""
        if desc:
            textos.append(desc[:500])
    blob = " ".join(textos).upper()

    if any(x in blob for x in ("TNU", "TURMA NACIONAL DE UNIFORMIZA", "EPROCTNU")):
        return "TNU"
    if any(x in blob for x in ("STJ", "SUPERIOR TRIBUNAL DE JUSTI")):
        return "STJ"
    return "OUTRO"


# ----- Download genérico PDF (STF e qualquer outro) -----

async def baixar_pdf_generico(url: str, timeout_s: int = 30) -> dict:
    try:
        import httpx
        import fitz

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
            ),
            "Accept": "application/pdf,*/*;q=0.8",
        }
        async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True,
                                     verify=False, headers=headers) as c:
            resp = await c.get(url)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            return {"conteudo": "", "pdf_bytes": b"", "erro": f"resposta não é PDF (ct={content_type})"}

        pdf_bytes = resp.content
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            paginas = []
            for pagina in doc:
                t = pagina.get_text()
                if t.strip():
                    paginas.append(t)
            texto = "\n\n".join(paginas)
        finally:
            doc.close()

        if not texto.strip():
            return {"conteudo": "", "pdf_bytes": pdf_bytes, "erro": "PDF sem texto (imagem escaneada?)"}

        return {"conteudo": texto, "pdf_bytes": pdf_bytes, "erro": None}
    except Exception as e:
        return {"conteudo": "", "pdf_bytes": b"", "erro": str(e)[:200]}


# ----- Seleção de peças TNU -----

def filtrar_pecas_tnu(documentos: list[dict]) -> list[dict]:
    """Top LIMITE_PECAS_TNU peças do processo, SEM janela temporal.

    Processos TNU duram anos; limitar por data cortaria peças-chave antigas.
    Prioridade: (1) eventos com DESPACHO/DECIS/SENTEN/ACORD/VOTO, depois (2) demais.
    Dentro de cada nível, ordena por data desc (mais recentes primeiro).
    Peças sem data válida vão pro final.
    """
    candidatos: list[tuple[int, float, dict]] = []
    for doc in documentos:
        dt = parse_data(doc.get("evento_data", "") or "")
        desc = (doc.get("evento_descricao", "") or "").upper()
        prio = 0 if any(kw in desc for kw in ("DESPACHO", "DECIS", "SENTEN", "ACORD", "VOTO")) else 1
        ts = -dt.timestamp() if dt else 0  # negativo pra ordenar desc; sem data = 0
        candidatos.append((prio, ts, doc))
    candidatos.sort(key=lambda x: (x[0], x[1]))
    out = []
    for _, _, doc in candidatos[:LIMITE_PECAS_TNU]:
        dt = parse_data(doc.get("evento_data", "") or "")
        out.append({**doc, "_data_parsed": dt.isoformat() if dt else ""})
    return out


def nome_arquivo_peca(doc: dict) -> str:
    """Nome único por peça: YYYY-MM-DD_ev{num}_{NOME_REAL}.

    Usa o nome real do doc (ex: DESPADEC1, PET1, COMP1, COMP2) retornado pelo
    e-Proc autenticado. Isso evita colisão quando várias peças pertencem ao
    mesmo evento (ev1 pode ter PET1 + COMP1 + COMP2 + PROC1 etc).
    """
    import re as _re
    dt = parse_data(doc.get("evento_data", "") or "")
    data_s = dt.strftime("%Y-%m-%d") if dt else "0000-00-00"
    ev = doc.get("evento_numero", "0")
    # Nome real do doc (sem caracteres problemáticos pra filesystem)
    nome_raw = (doc.get("nome", "") or "").strip()
    nome_safe = _re.sub(r"[^A-Za-z0-9_.-]", "_", nome_raw)[:40]
    if not nome_safe or nome_safe == "_":
        # fallback se não tiver nome real: usa doc_id curto
        nome_safe = f"DOC_{(doc.get('doc_id','') or '')[:8]}"
    return f"{data_s}_ev{ev}_{nome_safe}"


# ----- processar PAJ -----

async def processar_paj(alvo: dict, clients: dict) -> dict:
    paj = alvo["paj"]
    paj_norm = normalizar_paj(paj)
    pasta = ENTRADA_DIR / paj_norm
    pecas_dir = pasta / "peças"
    stj_dir = pasta / "decisoes_superiores"  # inclui STJ e STF
    pecas_dir.mkdir(parents=True, exist_ok=True)
    stj_dir.mkdir(parents=True, exist_ok=True)

    info = {
        "paj": paj,
        "pasta": str(pasta),
        "classe": alvo["classe"],
        "foro": "?",
        "classificacao": "?",
        "pecas_baixadas": 0,
        "decisoes_baixadas": 0,
        "erros": [],
    }

    dec = decompor_paj(paj)
    if not dec:
        info["erros"].append("PAJ mal-formado")
        return info
    ano, unidade, numero = dec

    # 1. SISDPU — movimentacoes_paj (tela Detalhamento com URLs STJ)
    update_state(subfase="sisdpu_movimentacoes")
    log(f"  [sisdpu] movimentacoes {paj}")
    try:
        det = await clients["sisdpu"].movimentacoes_paj(numero, ano, unidade)
    except Exception as e:
        info["erros"].append(f"sisdpu.movimentacoes_paj: {e}")
        det = {"erro": str(e), "movimentacoes": []}

    metadata = {
        "paj": paj,
        "paj_normalizado": paj_norm,
        "classe_evento": alvo["classe"],
        "assistido_caixa": alvo.get("assistido", ""),
        "oficio_caixa": alvo.get("oficio", ""),
        "data_mov_caixa": alvo.get("data", ""),
        "desc_mov_caixa": alvo.get("desc", ""),
        "primeira_deteccao": datetime.now(timezone.utc).astimezone().isoformat(),
        "detalhes_sisdpu": det,
    }

    # 2. CNJ
    fontes_cnj = " ".join([
        str(det.get("processo_judicial", "")),
        str(det.get("texto_pagina", "")),
        alvo.get("desc", ""),
    ])
    cnj_digitos = extrair_cnj(fontes_cnj)
    if cnj_digitos:
        metadata["processo_judicial"] = formatar_cnj(cnj_digitos)
        metadata["processo_judicial_digitos"] = cnj_digitos

    # 3. Foro detectado primeiro (antes de decidir se DataJud vale a pena)
    foro = detectar_foro(det, None, cnj_digitos, alvo.get("desc", ""))

    # 4. DataJud — só pra NÃO-TNU (TNU autenticado já dá mais dados que DataJud)
    datajud_data: dict | None = None
    if cnj_digitos and foro != "TNU":
        update_state(subfase="datajud", cnj=formatar_cnj(cnj_digitos))
        log(f"  [datajud] {formatar_cnj(cnj_digitos)}")
        try:
            datajud_data = await clients["datajud"].consultar_processo(cnj_digitos)
            (pasta / "datajud.json").write_text(
                json.dumps(datajud_data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            # Redetecta foro incluindo DataJud (pode ajustar de OUTRO pra STJ)
            foro = detectar_foro(det, datajud_data, cnj_digitos, alvo.get("desc", ""))
        except Exception as e:
            info["erros"].append(f"datajud: {e}")
    info["foro"] = foro
    metadata["foro_detectado"] = foro

    # 5. TNU — peças (AUTENTICADO se perfil existir, senão modo público)
    eventos_tnu: dict | None = None
    pecas_baixadas: list[dict] = []
    if foro in ("TNU",) and cnj_digitos:
        usa_autenticado = EPROC_PROFILE_DIR.is_dir() and any(EPROC_PROFILE_DIR.iterdir())
        update_state(subfase="tnu_listando_docs", modo_tnu=("autenticado" if usa_autenticado else "publico"))
        log(f"  [tnu] eventos + docs (modo={'AUTENTICADO' if usa_autenticado else 'publico'})")
        try:
            tnu_proc = await clients["tnu"].consultar_processo(formatar_cnj(cnj_digitos))
        except Exception as e:
            tnu_proc = {"erro": str(e)}
            info["erros"].append(f"tnu.consultar: {e}")

        docs_lista: list[dict] = []
        if usa_autenticado:
            try:
                docs_lista = await clients["eproc_auth"].listar_documentos_processo(formatar_cnj(cnj_digitos))
                log(f"  [tnu] autenticado listou {len(docs_lista)} docs")
            except Exception as e:
                import traceback
                log(f"  [tnu] FALHA autenticado: {type(e).__name__}: {e}")
                traceback.print_exc()
                info["erros"].append(f"eproc_auth.listar: {e}")
                usa_autenticado = False

        if not usa_autenticado:
            try:
                docs_result = await clients["tnu"].listar_documentos(formatar_cnj(cnj_digitos))
                docs_lista = docs_result.get("documentos", [])
            except Exception as e:
                info["erros"].append(f"tnu.listar_documentos: {e}")

        pecas_selecionadas = filtrar_pecas_tnu(docs_lista)
        eventos_tnu = {
            "consulta": tnu_proc,
            "modo": "AUTENTICADO" if usa_autenticado else "PUBLICO",
            "total_documentos": len(docs_lista),
            "pecas_selecionadas": pecas_selecionadas,
        }
        (pasta / "eventos_tnu.json").write_text(
            json.dumps(eventos_tnu, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        if usa_autenticado:
            # FASE A: baixa TODOS os PDFs em sequência rápida (sessão curta)
            update_state(subfase="tnu_baixando_pdfs", total_pecas=len(pecas_selecionadas))
            log(f"  [tnu] FASE A — baixando {len(pecas_selecionadas)} PDFs...")
            docs_baixados = []  # [(doc, nome_base, pdf_bytes, content_type)]
            for doc in pecas_selecionadas:
                nome_base = nome_arquivo_peca(doc)
                try:
                    res = await clients["eproc_auth"].baixar_pdf_bytes(doc)
                    erro = res.get("erro")
                    if erro:
                        info["erros"].append(f"peça {nome_base} download: {erro}")
                        continue
                    pdf_bytes = res.get("bytes", b"")
                    content_type = res.get("content_type", "")
                    # Salva PDF direto (se for PDF)
                    if pdf_bytes[:4] == b"%PDF" or "pdf" in content_type:
                        (pecas_dir / f"{nome_base}.pdf").write_bytes(pdf_bytes)
                    docs_baixados.append((doc, nome_base, pdf_bytes, content_type))
                except Exception as e:
                    info["erros"].append(f"peça {nome_base} download: {e}")
                await asyncio.sleep(0.3)
            log(f"  [tnu] FASE A OK — {len(docs_baixados)} PDFs em disco")

            # FASE B: extração de texto local (OCR só pra scans) — sem sessão e-Proc
            update_state(subfase="tnu_extraindo_texto_ocr")
            log(f"  [tnu] FASE B — extraindo texto (OCR só quando necessário)...")
            for doc, nome_base, pdf_bytes, content_type in docs_baixados:
                try:
                    if pdf_bytes[:4] == b"%PDF" or "pdf" in content_type:
                        res_txt = clients["eproc_auth"].extrair_texto_pdf(pdf_bytes)
                    else:
                        res_txt = clients["eproc_auth"].extrair_texto_html(pdf_bytes)
                    conteudo = res_txt.get("conteudo", "")
                    if conteudo.strip():
                        (pecas_dir / f"{nome_base}.txt").write_text(conteudo, encoding="utf-8")
                    pecas_baixadas.append({
                        "arquivo": f"peças/{nome_base}.txt" if conteudo.strip() else None,
                        "arquivo_pdf": f"peças/{nome_base}.pdf" if (pdf_bytes[:4] == b"%PDF") else None,
                        "evento": doc.get("evento_numero"),
                        "data": doc.get("evento_data"),
                        "nome_doc": doc.get("nome", ""),
                        "tamanho": len(conteudo),
                        "ocr_usado": res_txt.get("ocr_usado", False),
                    })
                except Exception as e:
                    info["erros"].append(f"peça {nome_base} extração: {e}")
            log(f"  [tnu] FASE B OK — {sum(1 for p in pecas_baixadas if p.get('tamanho',0)>0)} com texto extraído")
        else:
            # Modo público: mantém fluxo antigo (TNU ler_documento já faz tudo de uma vez)
            for doc in pecas_selecionadas:
                nome_base = nome_arquivo_peca(doc)
                try:
                    log(f"  [tnu] baixa {nome_base}")
                    res = await clients["tnu"].ler_documento(
                        doc["doc_id"], doc["evento_id"], doc["key"], doc["hash"],
                        doc.get("nome", ""),
                    )
                    if res.get("erro"):
                        info["erros"].append(f"peça {nome_base}: {res['erro']}")
                        continue
                    (pecas_dir / f"{nome_base}.txt").write_text(res.get("conteudo", ""), encoding="utf-8")
                    pecas_baixadas.append({
                        "arquivo": f"peças/{nome_base}.txt",
                        "arquivo_pdf": None,
                        "evento": doc.get("evento_numero"),
                        "data": doc.get("evento_data"),
                        "nome_doc": doc.get("nome", ""),
                        "tamanho": res.get("tamanho_caracteres", 0),
                    })
                except Exception as e:
                    info["erros"].append(f"peça {nome_base}: {e}")
                await asyncio.sleep(0.5)

    # 6. Decisões STJ/STF
    stj_salvos: list[dict] = []
    urls_decisoes: list[str] = []
    for u in (det.get("urls_decisoes") or det.get("urls_stj") or []):
        urls_decisoes.append(u)
    blobs = [alvo.get("desc", ""), json.dumps(datajud_data or {}, ensure_ascii=False, default=str)]
    for blob in blobs:
        for m in re.finditer(
            r"https?://[^\s\"'<>]*(?:stj\.jus\.br|stf\.jus\.br|portal\.stf|processo\.stj)[^\s\"'<>]*",
            blob or "",
        ):
            urls_decisoes.append(m.group(0))
    urls_decisoes = list(dict.fromkeys(urls_decisoes))[:8]
    for url in urls_decisoes:
        update_state(subfase="baixando_decisao_superior")
        log(f"  [decisao] {url[:80]}")
        try:
            if "stj.jus.br" in url:
                res = await clients["stj"].baixar_e_extrair_decisao(url)
                conteudo = res.get("conteudo", "")
                pdf_bytes = b""
                erro = res.get("erro")
            else:
                res = await baixar_pdf_generico(url)
                conteudo = res.get("conteudo", "")
                pdf_bytes = res.get("pdf_bytes", b"")
                erro = res.get("erro")
            if erro:
                log(f"    erro download: {erro[:150]}")
                info["erros"].append(f"decisao {url[:80]}: {erro}")
                continue
            h = hashlib.sha256(url.encode()).hexdigest()[:10]
            prefix = "STJ" if "stj.jus.br" in url.lower() else ("STF" if "stf" in url.lower() else "DEC")
            (stj_dir / f"{prefix}_{h}.txt").write_text(conteudo, encoding="utf-8")
            if pdf_bytes:
                (stj_dir / f"{prefix}_{h}.pdf").write_bytes(pdf_bytes)
            log(f"    salvo {prefix}_{h} ({len(conteudo)}ch txt, {len(pdf_bytes)}b pdf)")
            stj_salvos.append({
                "url": url,
                "arquivo_txt": f"decisoes_superiores/{prefix}_{h}.txt",
                "arquivo_pdf": f"decisoes_superiores/{prefix}_{h}.pdf" if pdf_bytes else None,
                "tribunal": prefix,
                "tamanho": len(conteudo),
            })
        except Exception as e:
            import traceback
            log(f"    EXC {type(e).__name__}: {e}")
            traceback.print_exc()
            info["erros"].append(f"decisao {url[:80]}: {e}")

    info["pecas_baixadas"] = len(pecas_baixadas)
    info["decisoes_baixadas"] = len(stj_salvos)

    # 7. Classificação por regra + seleção de movs preservadas
    movs = det.get("movimentacoes", []) or []
    seqs_preservar = selecionar_movs_preservar(movs, alvo.get("data", ""))

    # movs_relevantes = preservadas + acórdãos + (não-lixo)
    movs_relevantes: list[dict] = []
    for m in movs:
        seq_str = str(m.get("seq", "?"))
        if seq_str in seqs_preservar:
            movs_relevantes.append(m)
        elif mov_tem_acordao(m):
            movs_relevantes.append(m)
        elif not mov_e_lixo(m):
            movs_relevantes.append(m)

    # Coletar conteúdos baixados pra classificação ler o TEOR (não só SISDPU)
    conteudos_baixados: list[str] = []
    for s in stj_salvos:
        try:
            arq = pasta / (s.get("arquivo_txt") or s.get("arquivo", ""))
            if arq.exists():
                conteudos_baixados.append(arq.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass
    for p in pecas_baixadas:
        try:
            arq = pasta / p["arquivo"]
            if arq.exists():
                conteudos_baixados.append(arq.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass

    classificacao = classificar_caso(
        status_paj=det.get("status_paj", ""),
        foro=foro,
        movs_todas=movs,
        movs_relevantes=movs_relevantes,
        desc_caixa=alvo.get("desc", ""),
        tem_decisao_baixada=bool(stj_salvos) or bool(pecas_baixadas),
        conteudos_baixados=conteudos_baixados,
    )
    info["classificacao"] = classificacao
    metadata["classificacao"] = classificacao

    # Prazos abertos (heurística legada — extrai datas explícitas)
    prazos = extrair_prazos_abertos(movs)
    metadata["prazos_abertos"] = prazos
    info["prazos_abertos"] = len(prazos)

    # Detector de prazos processuais (rito-aware + ciência ficta e-Proc)
    # Calcula data-alvo aplicando regras TNU/STJ/JEF (sem dobra DPU, +10d e-Proc)
    try:
        from prazos.detector import detectar_prazos_novos
        prazos_detectados = detectar_prazos_novos(
            paj_norm=paj_norm,
            movs_antigas=[],  # primeira detecção: todas as movs como "novas"
            movs_novas=movs,
            assistido=det.get("assistido", "") or alvo.get("assistido", ""),
            foro=foro,
            classificacao=classificacao,
            aplicar_ciencia_ficta_eproc=True,
        )
        (pasta / "prazos_detectados.json").write_text(
            json.dumps(prazos_detectados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        info["prazos_detectados_count"] = len(prazos_detectados)
        # Adiciona ao metadata também pra ficar visível no PROMPT_MAX
        metadata["prazos_detectados"] = prazos_detectados
    except Exception as e:
        info["erros"].append(f"prazos_detectados: {e}")
        info["prazos_detectados_count"] = 0

    # Grava metadata final
    (pasta / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # 8. PROMPT_MAX.md
    prompt_max = gerar_prompt_max(
        metadata, datajud_data, eventos_tnu,
        pecas_baixadas, stj_salvos,
        movs, movs_relevantes, seqs_preservar, prazos,
    )
    (pasta / "PROMPT_MAX.md").write_text(prompt_max, encoding="utf-8")

    return info


# ----- PROMPT_MAX.md builder -----

def _melhor(det_val: str, caixa_val: str) -> str:
    det_val = (det_val or "").strip()
    caixa_val = (caixa_val or "").strip()
    if not det_val or len(det_val) < 8 or det_val[:1].islower():
        return caixa_val or det_val or "?"
    # Se caixa é mais longo e informativo, prefere
    if len(caixa_val) > len(det_val) * 1.5:
        return caixa_val
    return det_val


def _seq_int(m):
    try:
        return int(m.get("seq", "0") or "0")
    except Exception:
        return 0


def gerar_prompt_max(
    metadata: dict,
    datajud: dict | None,
    eventos_tnu: dict | None,
    pecas_baixadas: list[dict],
    stj_salvos: list[dict],
    movs_todas: list[dict],
    movs_relevantes: list[dict],
    seqs_preservar: set[str],
    prazos: list[dict],
) -> str:
    det = metadata.get("detalhes_sisdpu", {}) or {}
    paj = metadata.get("paj", "?")
    assistido = _melhor(det.get("assistido", ""), metadata.get("assistido_caixa", ""))
    oficio = _melhor(det.get("oficio", ""), metadata.get("oficio_caixa", ""))
    status = (det.get("status_paj") or "").strip() or "Ativo"
    cnj = metadata.get("processo_judicial", "(sem CNJ)")
    foro = metadata.get("foro_detectado", "?")
    classif = metadata.get("classificacao", "?")

    linhas: list[str] = []
    linhas.append(f"# PAJ {paj} — {assistido}")
    linhas.append("")
    linhas.append(f"- **Status no SISDPU**: {status}")
    linhas.append(f"- **Ofício**: {oficio}")
    linhas.append(f"- **Processo judicial**: {cnj}")
    linhas.append(f"- **Foro**: {foro}")
    linhas.append(f"- **Entrou na caixa em**: {metadata.get('data_mov_caixa','?')}")
    linhas.append(f"- **Classificação automática**: `{classif}`")
    linhas.append("")

    # Prazos abertos (só se houver)
    if prazos:
        linhas.append("## Prazos abertos detectados")
        linhas.append("")
        for p in prazos:
            linhas.append(
                f"- **{p['data_final']}** ({p['dias']} dias) — parte {p['parte']} "
                f"[Seq {p['seq']}, mov {p['data_mov']}]"
            )
        linhas.append("")

    # Helper pra render de uma mov
    def _render_mov(m: dict, trunc: int | None = None) -> list[str]:
        seq = m.get("seq", "?")
        data = m.get("data", "?")
        tipo = (m.get("movimentacao") or "").strip()
        fases = (m.get("fases") or "").strip()
        desc = (m.get("descricao") or "").strip()
        out = []
        head = f"### Seq. {seq} — {data}"
        if tipo:
            head += f"  |  {tipo}"
        out.append(head)
        if fases:
            out.append(f"_{fases}_")
        if desc:
            out.append("")
            out.append(desc[:trunc] if trunc else desc)
        out.append("")
        return out

    # ========== Movs preservadas (motivo do retorno à caixa) ==========
    preservadas_ordenadas = sorted(
        [m for m in movs_todas if str(m.get("seq", "?")) in seqs_preservar],
        key=_seq_int, reverse=True,
    )
    if preservadas_ordenadas:
        linhas.append("## Movimentações recentes (motivo do retorno à caixa)")
        linhas.append("")
        linhas.append(
            "_Últimas 3 movs + qualquer uma até 30 dias antes da entrada na caixa. "
            "Sempre preservadas integralmente, sem filtro — é o que explica a presença do PAJ hoje._"
        )
        linhas.append("")
        for m in preservadas_ordenadas:
            linhas.extend(_render_mov(m))

    # ========== Decisões de tribunais superiores — TEOR COMPLETO EMBUTIDO ==========
    if stj_salvos:
        linhas.append("## Decisões de tribunais superiores (teor completo embutido)")
        linhas.append("")
        # Ordena: STF e STJ primeiro; mais recentes (tamanho decrescente como proxy)
        for s in stj_salvos:
            trib = s.get("tribunal", "DEC")
            arq_txt = s.get("arquivo_txt") or s.get("arquivo")
            arq_pdf = s.get("arquivo_pdf")
            conteudo = ""
            # Lê o conteúdo do arquivo .txt
            try:
                txt_path = Path(metadata.get("paj_normalizado") and str(Path(s.get("arquivo_txt", "")).parent))
                # Mais seguro: reconstruir path absoluto
                arq_full = ENTRADA_DIR / metadata["paj_normalizado"] / arq_txt
                if arq_full.exists():
                    conteudo = arq_full.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

            linhas.append(f"### {trib} — {s['url']}")
            linhas.append("")
            if arq_pdf:
                linhas.append(f"_Arquivos locais: `{arq_txt}` + PDF `{arq_pdf}` ({s.get('tamanho',0)} chars)_")
            else:
                linhas.append(f"_Arquivo local: `{arq_txt}` ({s.get('tamanho',0)} chars)_")
            linhas.append("")
            if conteudo.strip():
                linhas.append("```")
                linhas.append(conteudo)
                linhas.append("```")
            linhas.append("")

    # ========== Acórdãos e decisões colegiadas nas movs (teor literal) ==========
    # Só os que NÃO estão em preservadas (pra evitar duplicar)
    movs_acordao_antigos = [
        m for m in movs_relevantes
        if mov_tem_acordao(m) and str(m.get("seq", "?")) not in seqs_preservar
    ]
    movs_acordao_antigos.sort(key=_seq_int, reverse=True)
    if movs_acordao_antigos:
        linhas.append("## Acórdãos e decisões colegiadas nas movimentações anteriores (teor literal)")
        linhas.append("")
        for m in movs_acordao_antigos:
            linhas.extend(_render_mov(m))

    # ========== Peças TNU baixadas — teor embutido inline (igual STJ/STF) ==========
    if pecas_baixadas:
        linhas.append("## Peças TNU baixadas (teor completo embutido)")
        linhas.append("")
        for p in pecas_baixadas:
            conteudo = ""
            try:
                arq_full = ENTRADA_DIR / metadata["paj_normalizado"] / p["arquivo"]
                if arq_full.exists():
                    conteudo = arq_full.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            linhas.append(
                f"### {p.get('nome_doc','Peça TNU')} — ev{p.get('evento','?')}  "
                f"({p.get('data','?')})"
            )
            linhas.append("")
            linhas.append(f"_Arquivo local: `{p['arquivo']}` ({p.get('tamanho',0)} chars)_")
            linhas.append("")
            if conteudo.strip():
                linhas.append("```")
                linhas.append(conteudo)
                linhas.append("```")
            linhas.append("")

    # ========== Histórico anterior relevante (movs filtradas) ==========
    historico_anterior = [
        m for m in movs_relevantes
        if str(m.get("seq", "?")) not in seqs_preservar and not mov_tem_acordao(m)
    ]
    if historico_anterior:
        linhas.append("## Histórico anterior relevante (movimentações filtradas)")
        linhas.append("")
        linhas.append("_Filtro anti-lixo aplicado: removidas confirmações tautológicas, decursos automáticos, remessas internas e trâmites puros._")
        linhas.append("")
        for m in sorted(historico_anterior, key=_seq_int, reverse=True)[:10]:
            linhas.extend(_render_mov(m, trunc=1200))

    # Arquivos extras na pasta (JSON brutos, PDFs das decisões, etc) — útil saber que existem
    paj_norm = metadata.get("paj_normalizado", "")
    pasta = ENTRADA_DIR / paj_norm
    arquivos_extras: list[str] = []
    if pasta.exists():
        for f in sorted(pasta.rglob("*")):
            if f.is_file() and f.name != "PROMPT_MAX.md":
                rel = f.relative_to(pasta).as_posix()
                arquivos_extras.append(rel)
    if arquivos_extras:
        linhas.append("## Arquivos disponíveis nesta pasta")
        linhas.append("")
        linhas.append("_Conteúdo embutido acima cobre o essencial. Arquivos abaixo ficam disponíveis para referência — abrir se o MAX precisar do bruto (metadados, JSON, PDFs, peças extras)._")
        linhas.append("")
        for arq in arquivos_extras:
            linhas.append(f"- `{arq}`")
        linhas.append("")

    linhas.append("---")
    linhas.append("")
    linhas.append(
        f"_Gerado automaticamente pelo dpuscript em {metadata.get('primeira_deteccao','?')}. "
        "Dados extraídos do SISDPU, DataJud, e-Proc TNU, STJ e STF. "
        "Sem inferência automática — todas as citações são literais do SISDPU/PDFs anexos._"
    )

    return "\n".join(linhas)


# ----- Carregar clients (importlib, evita colisão de client.py) -----

def carregar_clients() -> dict:
    def _load(pasta: Path, alias: str):
        spec = importlib.util.spec_from_file_location(alias, str(pasta / "client.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[alias] = mod
        spec.loader.exec_module(mod)
        return mod

    clients = {
        "sisdpu": _load(MCP_DIR / "sisdpu", "sisdpu_client"),
        "datajud": _load(MCP_DIR / "datajud", "datajud_client"),
        "tnu": _load(MCP_DIR / "tnu", "tnu_client"),
        "stj": _load(MCP_DIR / "stj", "stj_client"),
    }
    # eproc_auth é módulo local, importa direto
    if EPROC_PROFILE_DIR.is_dir() and any(EPROC_PROFILE_DIR.iterdir()):
        try:
            import eproc_auth_client  # type: ignore
            clients["eproc_auth"] = eproc_auth_client
        except Exception as e:
            print(f"WARN: eproc_auth_client falhou ao importar ({e}) — usando modo público", file=sys.stderr)
    return clients


# ----- main -----

async def run(only: str | None, dry_run: bool) -> int:
    ENTRADA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Abre log file pra essa execucao
    global _RUN_LOG_HANDLE
    run_start = datetime.now()
    run_log_path = LOG_DIR / f"run_{run_start.strftime('%Y-%m-%d_%H%M%S')}.log"
    try:
        _RUN_LOG_HANDLE = open(run_log_path, "w", encoding="utf-8")
    except Exception:
        _RUN_LOG_HANDLE = None

    update_state(
        status="iniciando",
        iniciado_em=run_start.isoformat(),
        log_file=str(run_log_path),
        only=only,
        dry_run=dry_run,
        fase="carregando_env",
    )

    env = load_env(ENV_FILE)
    if not env.get("SISDPU_USERNAME") or not env.get("SISDPU_PASSWORD"):
        print(f"ERRO: .env em {ENV_FILE} sem SISDPU_USERNAME/SISDPU_PASSWORD", file=sys.stderr)
        update_state(status="erro", erro="SISDPU credenciais ausentes")
        return 1
    # Expõe todas as credenciais do .env como env vars (SISDPU_*, EPROC_*, etc)
    for k, v in env.items():
        if v:
            os.environ[k] = v

    update_state(fase="carregando_clients")
    clients = carregar_clients()

    update_state(status="rodando", fase="baixando_caixa_sisdpu", paj_atual=None)
    log("baixando caixa SISDPU")
    try:
        result = await clients["sisdpu"].caixa_de_entrada()
    except Exception as e:
        log(f"FATAL caixa: {e}")
        return 2
    itens_raw = result.get("itens_tabela", [])
    itens = [x for x in (_parse_item(it) for it in itens_raw) if x]
    # Ordena por data de envio ascendente (mais antigo primeiro) — prazos vencem antes
    def _data_sort_key(item):
        dt = parse_data(item.get("data", ""))
        return dt or datetime.max
    itens.sort(key=_data_sort_key)
    total = len(itens)
    log(f"caixa: {total} PAJs válidos (ordenados por data asc)")

    if only:
        itens = [it for it in itens if it["paj"] == only]
        log(f"--only {only}: {len(itens)} item(ns)")

    estado = carregar_estado()

    # Reconciliação: remove PAJs que saíram da caixa SISDPU real (concluídos pelo JP)
    # Skip se --only (foco em PAJ específico) ou se flag desativada
    if not only and not getattr(run, "_no_reconciliar", False):
        update_state(fase="reconciliando_caixa")
        recon = reconciliar_caixa(estado, itens, dry_run=dry_run)
        update_state(
            reconciliacao_orfaos=len(recon["orfaos"]),
            reconciliacao_arquivados=len(recon["arquivados"]),
            reconciliacao_mantidos=len(recon["mantidos"]),
        )
        if getattr(run, "_reconciliar_apenas", False):
            log("--reconciliar-apenas: encerrando após reconciliação")
            return 0

    alvos = []
    pulados = 0
    for it in itens:
        mov_hash = estado_hash(it.get("data", ""), it.get("desc", ""))
        classe = classificar_paj_estado(it["paj"], mov_hash, estado)
        if classe == "inalterado":
            pulados += 1
            continue
        alvos.append({**it, "classe": classe, "mov_hash": mov_hash})
    log(f"{len(alvos)} PAJs pra processar, {pulados} inalterados")

    if dry_run:
        print(json.dumps([{k: v for k, v in a.items() if k != "desc"} for a in alvos],
                         indent=2, ensure_ascii=False))
        return 0

    processados: list[dict] = []
    falhas: list[dict] = []
    update_state(
        total_pajs=len(alvos),
        processados=0,
        falhas_count=0,
        fase="processando_pajs",
    )
    for i, alvo in enumerate(alvos, 1):
        log(f"[{i}/{len(alvos)}] {alvo['paj']} ({alvo['classe']})")
        update_state(
            paj_atual=alvo["paj"],
            paj_index=i,
            paj_classe=alvo["classe"],
            fase="processando_paj",
        )
        try:
            info = await processar_paj(alvo, clients)
            processados.append(info)
            update_state(processados=len(processados), falhas_count=len(falhas))
            estado["pajs"][alvo["paj"]] = {
                "mov_hash": alvo["mov_hash"],
                "ultima_mov_data": alvo.get("data", ""),
                "ultima_preparacao": datetime.now(timezone.utc).astimezone().isoformat(),
                "pasta": info["pasta"],
                "foro": info["foro"],
                "classificacao": info["classificacao"],
            }
            estado["ultima_execucao"] = datetime.now(timezone.utc).astimezone().isoformat()
            salvar_estado(estado)
        except Exception as e:
            log(f"  FALHA: {e}")
            falhas.append({"paj": alvo["paj"], "erro": str(e)})
        await asyncio.sleep(RATE_LIMIT_SISDPU_SEG)

    try:
        await clients["sisdpu"].fechar()
    except Exception:
        pass
    if "eproc_auth" in clients:
        try:
            await clients["eproc_auth"].fechar()
        except Exception:
            pass

    # Resumo final
    update_state(
        status="concluido",
        fase="fim",
        paj_atual=None,
        finalizado_em=datetime.now().isoformat(),
        processados=len(processados),
        falhas_count=len(falhas),
    )
    log("=" * 60)
    log(f"FIM: {len(processados)} processados, {len(falhas)} falhas")
    for p in processados:
        log(f"  {p['paj']}  [{p['foro']}]  {p['classificacao']}  peças={p['pecas_baixadas']}  decisoes={p['decisoes_baixadas']}")
        for e in p.get("erros", []):
            log(f"    erro: {e[:200]}")
    if falhas:
        log("FALHAS:")
        for f in falhas:
            log(f"  {f['paj']}: {f['erro'][:200]}")

    return 0 if not falhas else 3


def main() -> int:
    parser = argparse.ArgumentParser(description="dpuscript — prepara pastas de PAJs")
    parser.add_argument("--only", help="Processar apenas este PAJ (ex: 2021/039-18791)")
    parser.add_argument("--dry-run", action="store_true", help="Lista alvos sem processar")
    parser.add_argument(
        "--reconciliar-apenas",
        action="store_true",
        help="Roda só reconciliação (move PAJs órfãos pra arquivados) e sai",
    )
    parser.add_argument(
        "--no-reconciliar",
        action="store_true",
        help="Pula reconciliação (não move PAJs órfãos)",
    )
    args = parser.parse_args()
    # Flags persistidas no objeto run pra serem lidas dentro da coroutine
    run._reconciliar_apenas = args.reconciliar_apenas
    run._no_reconciliar = args.no_reconciliar
    try:
        return asyncio.run(asyncio.wait_for(run(args.only, args.dry_run), timeout=TIMEOUT_TOTAL_SEG))
    except asyncio.TimeoutError:
        print(f"TIMEOUT: {TIMEOUT_TOTAL_SEG}s", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
