import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R58")
d.rect(0, 0, 1440, 810, K)
pics = ["c-capa-composta.jpg", "c-paifilho.jpg", "c-projecao-composta.jpg", "c-beira-composta.jpg"]
for i, n in enumerate(pics):
    x, y = (i % 2) * 720, (i // 2) * 405
    im = d.image(AM + "/tratado/" + n, x, y, 720, 405)
d.text(60, 760, "Kit leve para e-mail", "Helvetica Neue", "Condensed Black", 80, Y)
d.text(60, 700, "Texto vetorial continua nítido", "Helvetica Neue", "Bold", 28, "#FFFFFF")
def exp(name, **kw):
    r = d.ex("document.exportPdf", dict(path=d.dir + "/" + name, **kw)); print(name, r["bytes"], r["warnings"])
exp("A-padrao.pdf")
exp("B-sem-embutir.pdf", preserveEditing=False)
exp("C-leve.pdf", preserveEditing=False, thumbnails=False, fastWebView=True,
    compression={"color": {"downsample": "bicubic", "ppi": 150, "abovePpi": 225, "compression": "jpeg", "quality": "high"}})
exp("C2-150ppi.pdf", preserveEditing=False, thumbnails=False, fastWebView=True,
    compression={"color": {"downsample": "bicubic", "ppi": 150, "abovePpi": 160, "compression": "jpeg", "quality": "high"}})
exp("D-minimo.pdf", preserveEditing=False, thumbnails=False, fastWebView=True,
    compression={"color": {"downsample": "bicubic", "ppi": 110, "abovePpi": 165, "compression": "jpeg", "quality": "medium"}})
subprocess.run(["pdftoppm", "-r", "50", "-png", d.dir + "/C-leve.pdf", d.dir + "/preview"])
d.close()
