"""Memory de aprendizado de classificações — refino contínuo via feedback JP.

Cada vez que JP corrige uma classificação, vira uma regra aqui. Próxima
execução do pipeline consulta essas regras ANTES das regras default
do classificar_caso.

Arquivo: dpuscript/memory/classif_aprendizadas.jsonl
Formato: 1 regra por linha em JSON.

Cada regra:
{
  "id": "uuid",
  "criado_em": "ISO",
  "padrao_alvo": "blob_decisao" | "desc_caixa" | "blob_recentes",
  "padrao_regex": "regex que casa",
  "classif_correta": "DECISAO_X_Y",
  "razao_jp": "explicação curta",
  "exemplo_paj_origem": "2026/039-XXXXX",
  "ativa": true,
  "matches_count": 0
}
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


MEMORY_DIR = Path(__file__).resolve().parent
MEMORY_FILE = MEMORY_DIR / "classif_aprendizadas.jsonl"


@dataclass
class Regra:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    criado_em: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .astimezone()
        .isoformat(timespec="seconds")
    )
    padrao_alvo: str = "blob_decisao"  # blob_decisao | desc_caixa | blob_recentes
    padrao_regex: str = ""
    classif_correta: str = ""
    razao_jp: str = ""
    exemplo_paj_origem: str = ""
    ativa: bool = True
    matches_count: int = 0

    def aplica(self, contexto: dict) -> bool:
        """Verifica se a regra casa com o contexto dado.

        contexto deve ter chaves: blob_decisao, desc_caixa, blob_recentes (uppercase).
        """
        if not self.ativa:
            return False
        alvo = contexto.get(self.padrao_alvo, "")
        if not alvo:
            return False
        try:
            return bool(re.search(self.padrao_regex, alvo, re.IGNORECASE))
        except re.error:
            return False


def carregar_regras() -> list[Regra]:
    """Lê todas as regras do JSONL. Retorna lista (ordem do arquivo)."""
    if not MEMORY_FILE.exists():
        return []
    regras = []
    for linha in MEMORY_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        try:
            d = json.loads(linha)
            regras.append(Regra(**d))
        except Exception:
            continue
    return regras


def salvar_regras(regras: list[Regra]) -> None:
    """Reescreve TODAS as regras (uso interno após update)."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    linhas = [json.dumps(asdict(r), ensure_ascii=False) for r in regras]
    MEMORY_FILE.write_text("\n".join(linhas) + ("\n" if linhas else ""), encoding="utf-8")


def adicionar_regra(
    padrao_regex: str,
    classif_correta: str,
    razao_jp: str,
    exemplo_paj_origem: str = "",
    padrao_alvo: str = "blob_decisao",
) -> Regra:
    """Adiciona nova regra aprendida ao memory. Append-only no JSONL."""
    regra = Regra(
        padrao_alvo=padrao_alvo,
        padrao_regex=padrao_regex,
        classif_correta=classif_correta,
        razao_jp=razao_jp,
        exemplo_paj_origem=exemplo_paj_origem,
    )
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(regra), ensure_ascii=False) + "\n")
    return regra


def desativar_regra(regra_id: str) -> bool:
    """Desativa uma regra pelo ID (se errou, marca como inativa, não deleta)."""
    regras = carregar_regras()
    achou = False
    for r in regras:
        if r.id == regra_id:
            r.ativa = False
            achou = True
            break
    if achou:
        salvar_regras(regras)
    return achou


def aplicar_regras_aprendidas(
    blob_decisao: str = "",
    desc_caixa: str = "",
    blob_recentes: str = "",
) -> tuple[str | None, Regra | None]:
    """Aplica regras aprendidas em sequência. Retorna (classif, regra) na primeira que casa.

    Se nenhuma casa, retorna (None, None) — classificar_caso cai nas regras default.

    Atualiza contador de matches da regra que disparou.
    """
    contexto = {
        "blob_decisao": (blob_decisao or "").upper(),
        "desc_caixa": (desc_caixa or "").upper(),
        "blob_recentes": (blob_recentes or "").upper(),
    }
    regras = carregar_regras()
    for r in regras:
        if r.aplica(contexto):
            r.matches_count += 1
            salvar_regras(regras)
            return r.classif_correta, r
    return None, None
