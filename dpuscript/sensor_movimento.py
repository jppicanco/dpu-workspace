#!/usr/bin/env python3
"""Sensor de movimento — acende um ALERTA na Central de Atuação quando o PAJ
teve movimentação no SISDPU POSTERIOR ao despacho já dado.

Por que SISDPU (e não e-Proc): o PAJ é único no SISDPU e suas movimentações
refletem TUDO que acontece no processo, independente de para qual ofício a
tramitação foi. Então basta consultar o SISDPU — não precisa e-Proc nem CNJ
(usa número/ano/unidade do próprio PAJ, que sempre existe).

Passivo por design: NÃO re-decide, NÃO atua, NÃO toca no despacho. Só grava
(ou remove) `alerta_movimento.json` na pasta do PAJ. A Central lê e mostra o
badge. A "conclusão" do PAJ continua resolvida pela reconciliação (saiu da
caixa → arquivado → some da Central) + pelo botão "Conclui no SIS".

Uso:
    python sensor_movimento.py [--only 2026/039-07447] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preparar_pajs as pp  # noqa: E402

ENTRADA = pp.ENTRADA_DIR


def _load(alias: str, pasta: Path):
    spec = importlib.util.spec_from_file_location(alias, str(pasta / "client.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


# Marcadores de movimentação RELEVANTE no SISDPU. As descrições do SISDPU têm
# vocabulário próprio (ricas em alguns casos: "decisão monocrática", "conheceu
# do agravo", "recomendação de arquivamento") — estende os termos do e-Proc
# (pp.TERMOS_DECISORIOS) sem alterá-los. Ruído (decurso, remessa, "número do
# processo") não entra, então segue como ⚪.
TERMOS_RELEVANTES_SIS = pp.TERMOS_DECISORIOS + (
    "decisão monocrática", "decisao monocratica", "monocrática", "monocratica",
    "arquivamento", "acórdão", "acordao", "sentença", "sentenca",
    "julgad", "conheceu", "conheço", "conheco", "negou", "homolog",
    "provido", "deu provimento", "recomendação de arquivamento",
)


def _relevante(texto: str) -> bool:
    return any(t in (texto or "").lower() for t in TERMOS_RELEVANTES_SIS)


def _ler_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _despacho_dt(s) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "").split(".")[0])
    except Exception:
        return None


async def _analisar_movs(sis, paj_norm: str, ref: datetime) -> dict | None:
    """Analisa as movimentações do PAJ no SISDPU posteriores à referência.

    Retorna None se não há nada novo. Caso haja, retorna dados do alerta —
    marcando como decisório se QUALQUER mov nova for decisória (a decisão pode
    estar no meio, com uma tramitação burocrática como mov mais recente).
    """
    partes = paj_norm.split("-")
    if len(partes) != 3:
        return None
    ano, unidade, numero = partes
    det = await sis.movimentacoes_paj(numero, ano, unidade)
    movs = (det or {}).get("movimentacoes") or []

    novas = []
    for m in movs:
        dt = pp.parse_data(m.get("data", "") or "")
        if dt and dt > ref:
            novas.append((dt, (m.get("descricao") or "").strip()[:200], str(m.get("seq", ""))))
    if not novas:
        return None

    novas.sort(key=lambda x: x[0], reverse=True)
    recente = novas[0]
    decisoria = next((n for n in novas if _relevante(n[1])), None)
    destaque = decisoria or recente  # prioriza a relevante sobre a mais recente
    return {
        "decisorio": decisoria is not None,
        "n_novas": len(novas),
        "data": destaque[0],
        "desc": destaque[1],
        "seq": destaque[2],
        "data_recente": recente[0],
        "descs": [f"seq{n[2]} {n[0].strftime('%d/%m')}: {n[1][:70]}" for n in novas],
    }


async def processar(only: str | None, dry_run: bool) -> int:
    if not ENTRADA.exists():
        print(f"ENTRADA não existe: {ENTRADA}")
        return 1

    # Expõe credenciais do .env em os.environ ANTES de carregar o client sisdpu
    # (o preparar_pajs faz isso só no main(); importá-lo não dispara). Sem isso
    # o login no SISDPU falha com user/senha vazios.
    env = pp.load_env(pp.ENV_FILE)
    for k, v in env.items():
        if v:
            os.environ[k] = v

    sis = _load("sisdpu_client", pp.MCP_DIR / "sisdpu")
    only_norm = pp.normalizar_paj(only) if only else None
    acesos = limpos = ignorados = erros = 0

    try:
        for pasta in sorted(ENTRADA.iterdir()):
            if not pasta.is_dir():
                continue
            paj = pasta.name
            if only_norm and paj != only_norm:
                continue

            atuacao = _ler_json(pasta / "atuacao.json")
            meta = _ler_json(pasta / "metadata.json")
            if atuacao.get("status") not in ("done", "recurso_pendente"):
                ignorados += 1
                continue

            # Referência = data do MOVIMENTO que o despacho tratou (a mov da caixa),
            # NÃO a data em que o Grok rodou (concluido_em pode ser dias depois e
            # esconderia movimentos ocorridos no intervalo).
            ref = pp.parse_data(meta.get("data_mov_caixa", "") or "") or _despacho_dt(atuacao.get("concluido_em"))
            if not ref:
                ignorados += 1
                continue

            alerta_path = pasta / "alerta_movimento.json"
            try:
                info = await _analisar_movs(sis, paj, ref)
            except Exception as e:
                print(f"  erro {paj}: {type(e).__name__}: {e}")
                erros += 1
                continue

            if only_norm and info:
                print(f"  [debug] {paj}: ref={ref} | {info['n_novas']} novas:")
                for d in info["descs"]:
                    print(f"      {d}")

            if info:
                dados = {
                    "tem_alerta": True,
                    "mov_data": info["data"].strftime("%d/%m/%Y %H:%M:%S"),
                    "mov_seq": info["seq"],
                    "mov_desc": info["desc"],
                    "decisorio": info["decisorio"],
                    "movs_novas": info["n_novas"],
                    "despacho_em": atuacao.get("concluido_em", ""),
                    "fonte": "SISDPU",
                    "gerado_em": datetime.now().isoformat(timespec="seconds"),
                }
                marca = "🔴 DECISÓRIO" if info["decisorio"] else "⚪ movimento"
                print(f"  {marca} {paj}: {info['n_novas']} nova(s) | destaque seq{info['seq']} "
                      f"{dados['mov_data']} | {info['desc'][:60]}")
                if not dry_run:
                    alerta_path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
                acesos += 1
            else:
                if alerta_path.exists():
                    if not dry_run:
                        alerta_path.unlink()
                    limpos += 1
    finally:
        try:
            await sis.fechar()
        except Exception:
            pass

    print(f"\n=== SENSOR: {acesos} aceso(s) | {limpos} limpo(s) | "
          f"{ignorados} ignorados (sem despacho) | {erros} erros ===")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Processar apenas este PAJ")
    ap.add_argument("--dry-run", action="store_true", help="Não grava nada, só mostra")
    args = ap.parse_args()
    return asyncio.run(processar(args.only, args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
