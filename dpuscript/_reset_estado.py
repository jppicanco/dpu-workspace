"""Remove PAJs do estado (pra forçar reprocessamento). Uso: _reset_estado.py <paj>..."""
import json
import sys
from pathlib import Path

pajs = sys.argv[1:]
p = Path(__file__).parent / "estado" / "pajs_processados.json"
if not p.exists():
    print("(estado vazio)")
    raise SystemExit(0)
d = json.loads(p.read_text(encoding="utf-8"))
if not pajs:
    d = {"pajs": {}, "ultima_execucao": None}
    print("estado zerado")
else:
    for paj in pajs:
        if d["pajs"].pop(paj, None) is not None:
            print(f"removido {paj}")
        else:
            print(f"(já não existia) {paj}")
p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
