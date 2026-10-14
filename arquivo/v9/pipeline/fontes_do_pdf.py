#!/usr/bin/env python3
"""
fontes_do_pdf.py — recupera as fontes embutidas num PDF (kit antigo do cliente, manual de marca, apresentação) como TTF utilizáveis no render.

Uso: python3 fontes_do_pdf.py <arquivo.pdf> <pasta-de-saida> [--familias RocGrotesk,Anton]

O que faz: lê os FontDescriptor do PDF (pikepdf); fontes CFF (Type1C) são desubroutinizadas e reconstruídas com cmap pelos nomes
de glifo (AGL); fontes TrueType (CID, Identity-H) são mesclados por GID entre todos os subsets do mesmo nome e recebem cmap pelo
ToUnicode; depois tudo é convertido para TrueType (cu2qu), porque o Chromium embute TrueType como CIDFontType2 (o CFF reconstruído
saía como Type 3 no PDF). Imprime a cobertura de caracteres de cada fonte: um subset só tem os glifos que o PDF usou. Fallback por
caractere no CSS cobre o resto (--fonte-corpo), mas confira a cobertura antes de usar em título.

LICENÇA: a fonte continua sendo da fundição. Isto recupera o que o cliente já pagou e usou no kit anterior, para manter a identidade dele;
para fonte comercial (RocGrotesk, Helvetica World) a Motion ou o cliente precisa ter licença para entregar. Registre em pendencias.md.
"""
import argparse, io, re, sys
from collections import defaultdict
from pathlib import Path


def main():
    import pikepdf
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    from fontTools.cffLib import CFFFontSet
    from fontTools.fontBuilder import FontBuilder
    from fontTools.agl import toUnicode
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen

    ap = argparse.ArgumentParser(); ap.add_argument("pdf"); ap.add_argument("saida"); ap.add_argument("--familias", default=None)
    a = ap.parse_args(); out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)
    fams = [f.strip() for f in a.familias.split(",")] if a.familias else None
    pdf = pikepdf.open(a.pdf)

    def parse_tounicode(data):
        t = data.decode("latin-1"); m = {}
        for blk in re.findall(r"beginbfchar(.*?)endbfchar", t, re.S):
            for x, y in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                if len(y) <= 4: m[int(x, 16)] = int(y, 16)
        for blk in re.findall(r"beginbfrange(.*?)endbfrange", t, re.S):
            for x, y, z in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                for i in range(int(x, 16), int(y, 16) + 1): m[i] = int(z, 16) + i - int(x, 16)
        return m

    cff_sub = defaultdict(list); tt_sub = defaultdict(list)
    for obj in pdf.objects:
        try:
            if not isinstance(obj, pikepdf.Dictionary) or obj.get("/Type") != "/Font": continue
            if obj.get("/Subtype") == "/Type0":
                desc = obj["/DescendantFonts"][0]; fd = desc["/FontDescriptor"]
            else:
                fd = obj.get("/FontDescriptor")
            if fd is None: continue
            nome = str(fd["/FontName"]).split("+")[-1]
            if fams and not any(f.lower() in nome.lower() for f in fams): continue
            if "/FontFile3" in fd: cff_sub[nome].append(fd["/FontFile3"].read_bytes())
            elif "/FontFile2" in fd: tt_sub[nome].append((fd["/FontFile2"].read_bytes(), parse_tounicode(obj["/ToUnicode"].read_bytes()) if "/ToUnicode" in obj else {}))
        except Exception: pass

    def salvar_tt(nome, fb_font, cmap):
        fam = nome.split("-")[0]; estilo = nome.split("-")[1] if "-" in nome else "Regular"
        peso = {"Regular": 400, "Light": 300, "Medium": 500, "Bold": 700, "ExtraBold": 800, "WideExtraBold": 800, "WideMedium": 500, "Black": 900}.get(estilo, 400)
        fb = FontBuilder(font=fb_font)
        fb.setupNameTable({"familyName": fam, "styleName": estilo, "psName": nome, "fullName": nome})
        if "OS/2" not in fb_font: fb.setupOS2(usWeightClass=peso, sTypoAscender=fb_font["hhea"].ascent, sTypoDescender=fb_font["hhea"].descent, usWinAscent=fb_font["hhea"].ascent, usWinDescent=-fb_font["hhea"].descent)
        if "post" not in fb_font: fb.setupPost()
        p = out / f"{nome}.ttf"; fb_font.save(p)
        print(f"{nome}: {len(cmap)} caracteres → {''.join(sorted(chr(u) for u in cmap if 32 < u < 400))}")

    # CFF → charstrings desubroutinizados → TrueType (cu2qu)
    for nome, subs in cff_sub.items():
        glyphs = {}
        for data in subs:
            try:
                cff = CFFFontSet(); cff.decompile(io.BytesIO(data), None); cff.desubroutinize(); td = cff[0]; cs = td.CharStrings
                for g in cs.keys():
                    if g in glyphs: continue
                    c = cs[g]; rp = RecordingPen(); c.draw(rp); p2 = T2CharStringPen(c.width, None)
                    for op, args in rp.value: getattr(p2, op)(*args)
                    glyphs[g] = (p2.getCharString(), c.width)
            except Exception as e: print(nome, "subset ignorado:", repr(e)[:80], file=sys.stderr)
        if not glyphs: continue
        if ".notdef" not in glyphs: glyphs[".notdef"] = (T2CharStringPen(500, None).getCharString(), 500)
        order = [".notdef"] + sorted(k for k in glyphs if k != ".notdef")
        cmap = {ord(u): g for g in order if len(u := toUnicode(g)) == 1}
        fb = FontBuilder(1000, isTTF=False); fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap)
        fb.setupCFF(nome, {"FullName": nome, "FamilyName": nome.split("-")[0]}, {g: glyphs[g][0] for g in order}, {})
        fb.setupHorizontalMetrics({g: (int(round(glyphs[g][1])), 0) for g in order}); fb.setupHorizontalHeader(ascent=900, descent=-200); fb.setupPost()
        src = fb.font; gs = src.getGlyphSet()
        fb2 = FontBuilder(1000, isTTF=True); fb2.setupGlyphOrder(order); fb2.setupCharacterMap(cmap); tg = {}
        for g in order:
            pen = TTGlyphPen(gs); gs[g].draw(Cu2QuPen(pen, 1.0, reverse_direction=True)); tg[g] = pen.glyph()
        fb2.setupGlyf(tg); fb2.setupHorizontalMetrics({g: (int(round(glyphs[g][1])), 0) for g in order}); fb2.setupHorizontalHeader(ascent=900, descent=-200)
        salvar_tt(nome, fb2.font, cmap)

    # TrueType: mesclar subsets por GID
    for nome, subs in tt_sub.items():
        try:
            ref = {}
            for _, tu in subs: ref.update(tu)
            fonts = [(TTFont(io.BytesIO(d)), tu) for d, tu in subs]
            n = max(max(f["maxp"].numGlyphs for f, _ in fonts), (max(ref) + 1) if ref else 1)
            base, _ = max(fonts, key=lambda x: x[0]["maxp"].numGlyphs)
            order = [".notdef"] + [f"g{i}" for i in range(1, n)]
            for f, _ in fonts: f.setGlyphOrder([".notdef"] + [f"g{i}" for i in range(1, f["maxp"].numGlyphs)])
            base.setGlyphOrder(order); glyf = base["glyf"]; hmtx = base["hmtx"]
            for g in order:
                if g not in glyf.glyphs: glyf[g] = Glyph(); hmtx[g] = (0, 0)
            for f, tu in fonts:
                for gid in tu:
                    g = order[gid] if gid < n else None
                    if g and g in f["glyf"].glyphs and f["glyf"][g].numberOfContours != 0 and glyf[g].numberOfContours == 0:
                        glyf[g] = f["glyf"][g]; hmtx[g] = f["hmtx"][g]
            base["maxp"].numGlyphs = n
            cmap = {u: order[g] for g, u in ref.items() if g < n and u > 31 and glyf[order[g]].numberOfContours != 0}
            FontBuilder(font=base).setupCharacterMap(cmap)
            salvar_tt(nome, base, cmap)
        except Exception as e: print(nome, "ERRO", repr(e)[:120], file=sys.stderr)


if __name__ == "__main__":
    main()
