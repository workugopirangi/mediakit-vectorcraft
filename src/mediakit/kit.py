"""Monta um kit: uma função por página, na ordem, num documento só; exporta PDF e .vectorcraft."""
import json
import time
from pathlib import Path

from mediakit.pagina import Pagina
from mediakit.vc import VC, conferir_versao


def montar(nome, paginas, saida_pdf, saida_vc, pw=1920, ph=1080, gap=2000, escala=75, vc=None):
    conferir_versao()
    t0 = time.time()
    proprio = vc is None
    vc = vc or VC()
    ex = vc.ex
    retornos, avisos, aceitas = {}, [], []
    try:
        ex("file.new", {"name": nome, "width": pw, "height": ph, "units": "Pixels"})
        for n, fn in enumerate(paginas):
            retornos[fn.__name__] = fn(Pagina(ex, n, pw, ph, gap, avisos, aceitas))
        for n in range(len(paginas)):
            ex("select.allOnArtboard", {"artboard": n})
            ex("object.scale", {"sx": escala, "sy": escala, "origin": [n * gap, 0], "strokes": True, "corners": True})
            ex("select.none")
            ex("artboard.setProps", {"index": n, "width": pw * escala / 100, "height": ph * escala / 100})
        Path(saida_pdf).parent.mkdir(parents=True, exist_ok=True)
        ex("document.exportPdf", {"path": str(saida_pdf), "preserveEditing": False})
        ex("file.saveAs", {"path": str(saida_vc)})
        # Ao lado do PDF, para a checagem (outro processo) mostrar ao Ugo qual foto ficou abaixo da régua.
        (Path(saida_pdf).parent / "avisos-foto.json").write_text(json.dumps(avisos, ensure_ascii=False, indent=1) + "\n")
        (Path(saida_pdf).parent / "sobreposicoes-aceitas.json").write_text(
            json.dumps(aceitas, ensure_ascii=False, indent=1) + "\n")
    finally:
        if proprio:
            vc.close()
    return {"pdf": Path(saida_pdf), "vectorcraft": Path(saida_vc), "segundos": round(time.time() - t0, 1),
            "retornos": retornos, "avisos_foto": avisos}
