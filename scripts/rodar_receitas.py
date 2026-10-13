"""Roda todas as receitas na versão travada do VectorCraft. Prova de que trocar a versão não quebrou nada.
Uso: python3 scripts/rodar_receitas.py [--gravar-base]"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "receitas" / "_linha-de-base.json"


def rodar():
    res = {}
    for t in sorted((RAIZ / "receitas").glob("R*/teste.py")):
        try:
            r = subprocess.run([sys.executable, str(t)], cwd=t.parent, capture_output=True, text=True, timeout=120)
            res[t.parent.name] = r.returncode == 0
        except subprocess.TimeoutExpired:
            res[t.parent.name] = False
        print(t.parent.name, "ok" if res[t.parent.name] else "FALHOU", flush=True)
    # As receitas regravam o PDF de prova; devolve os que o Ugo viu (os gerados agora são reproduzíveis).
    subprocess.run(["git", "-C", str(RAIZ), "checkout", "--", "receitas"], check=False)
    return res


if __name__ == "__main__":
    res = rodar()
    if "--gravar-base" in sys.argv:
        BASE.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        print(f"linha de base: {sum(res.values())} de {len(res)} rodam")
        sys.exit(0)
    base = json.loads(BASE.read_text())
    quebradas = [k for k, ok in base.items() if ok and not res.get(k)]
    print(f"{sum(res.values())} de {len(res)} rodam; quebradas desde a base: {quebradas or 'nenhuma'}")
    sys.exit(1 if quebradas else 0)
