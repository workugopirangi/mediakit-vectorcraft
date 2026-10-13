"""Aplica o logo da World Tennis nas cenas limpas da Sprint (rota 'compor')."""
import json, os, subprocess, sys
from PIL import Image
CL = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT")
WT = os.path.join(CL, "sprint-world-tennis")
K = os.path.join(CL, "sprint-2027")
S = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT/pipeline/compor.py")
A = os.path.join(WT, "acervo")
wt = Image.open(os.path.join(A, "logo-world-tennis.png")).convert("RGBA")
sp = Image.open(os.path.join(K, "acervo/logo.png")).convert("RGBA")
H = 300
sp2 = sp.resize((int(sp.width * H / sp.height), H))
wt2 = wt.resize((int(wt.width * H * 0.82 / wt.height), int(H * 0.82)))
L = Image.new("RGBA", (sp2.width + 80 + wt2.width, H), (0, 0, 0, 0))
L.alpha_composite(sp2, (0, 0))
L.alpha_composite(Image.new("RGBA", (4, int(H * 0.7)), (255, 255, 255, 200)), (sp2.width + 38, int(H * 0.15)))
L.alpha_composite(wt2, (sp2.width + 80, int(H * 0.09)))
L.save(os.path.join(A, "lockup-testeira.png"))
wt.rotate(90, expand=True).save(os.path.join(A, "wt-vertical.png"))
lotes = {
    "c-portico": [{"quad": [600, 30, 1440, 30, 1440, 170, 600, 170], "logo": os.path.join(A, "lockup-testeira.png")},
                  {"quad": [440, 230, 560, 230, 560, 640, 440, 640], "logo": os.path.join(A, "wt-vertical.png")},
                  {"quad": [1452, 230, 1600, 230, 1600, 640, 1452, 640], "logo": os.path.join(A, "wt-vertical.png")}],
    "c-tendas": [{"quad": [0, 312, 425, 318, 425, 398, 0, 398], "logo": os.path.join(A, "logo-world-tennis.png")},
                 {"quad": [432, 318, 785, 318, 785, 376, 432, 378], "texto": "POP UP WORLD TENNIS", "cor": "#FFFFFF"},
                 {"quad": [1055, 536, 1228, 542, 1214, 842, 1052, 828], "logo": os.path.join(A, "wt-vertical.png")},
                 {"quad": [1188, 218, 1352, 218, 1352, 300, 1188, 300], "logo": os.path.join(K, "acervo/logo.png")}],
}
for cena, lote in lotes.items():
    j = os.path.join(A, f"compor-{cena}-wt.json")
    json.dump(lote, open(j, "w"), ensure_ascii=False, indent=1)
    out = os.path.join(A, f"{cena}-wt-composta.png")
    r = subprocess.run([sys.executable, S, os.path.join(K, "acervo/limpo", cena + ".png"), out, "--lote", j], capture_output=True, text=True)
    print(cena, r.returncode, (r.stdout + r.stderr).strip()[-300:])
