"""Roda todas as receitas na versão travada do VectorCraft e compara com a linha de base.
Uso: python3 scripts/rodar_receitas.py [--gravar-base]
Sai 1 se alguma receita que rodava parou de rodar. "Desenha diferente" não para nada: vai para o Ugo olhar."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from mediakit import receitas  # noqa: E402

BASE = RAIZ / "receitas" / "_linha-de-base.json"

if __name__ == "__main__":
    res = receitas.rodar(RAIZ / "receitas")
    rodam = sum(r["roda"] for r in res.values())
    mudaram = [k for k, r in res.items() if r["mudou"]]
    if "--gravar-base" in sys.argv:
        BASE.write_text(json.dumps({k: r["roda"] for k, r in res.items()}, indent=1, sort_keys=True) + "\n")
        print(f"linha de base: {rodam} de {len(res)} rodam")
        sys.exit(0)
    q = receitas.quebradas(json.loads(BASE.read_text()), res)
    print(f"{rodam} de {len(res)} rodam; quebradas desde a base: {q or 'nenhuma'}; "
          f"desenham diferente (olhe): {mudaram or 'nenhuma'}")
    sys.exit(1 if q else 0)
