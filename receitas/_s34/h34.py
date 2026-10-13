import sys, os, subprocess, json
sys.path.insert(0, os.path.expanduser("~/Developer/vectorcraft-mediakit"))
from vch import VC, VCError
K="#0B0B0C"; Y="#F5D80A"; GOLD="#D4A64A"; CREAM="#F3E3B5"; SEA="#0F3550"; MINT="#9FE3D0"; CORAL="#E9603A"
TRAT_S="/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027/acervo/tratado/"
TRAT_A="/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/AME CRIANCA/MEDIAKIT/copa-ame-v2/acervo/tratado/"
class P:
    def __init__(s, rid):
        s.dir=os.path.expanduser(f"~/Developer/vectorcraft-mediakit/receitas/{rid}"); os.makedirs(s.dir,exist_ok=True)
        s.vc=VC(); s.ex=s.vc.ex
        s.ex("file.new",{"width":1440,"height":810,"units":"Points"})
    def try_(s,cmd,params=None):
        try: return s.ex(cmd,params)
        except VCError as e:
            print("ERRO",cmd,str(e)[:400]); return None
    def paint(s,oid,fill=None,stroke=None,sw=1,opacity=None,gradient=None):
        s.ex("select.set",{"ids":[oid]})
        if gradient: s.ex("paint.setFill",{"gradient":gradient})
        elif fill is None: s.ex("paint.setFill",{"none":True})
        else: s.ex("paint.setFill",{"color":fill})
        if stroke is None: s.ex("paint.setStroke",{"none":True})
        else:
            s.ex("paint.setStroke",{"color":stroke}); s.ex("stroke.set",{"weight":sw})
        if opacity is not None: s.ex("transparency.set",{"ids":[oid],"opacity":opacity})
        s.ex("select.none"); return oid
    def rect(s,x,y,w,h,fill=K,radius=None,**k):
        p={"x":x,"y":y,"width":w,"height":h}
        if radius: p["radius"]=radius
        return s.paint(s.ex("shape.rectangle",p)["id"],fill,**k)
    def ell(s,cx,cy,rx,ry,fill=K,**k):
        return s.paint(s.ex("shape.ellipse",{"x":cx-rx,"y":cy-ry,"width":2*rx,"height":2*ry})["id"],fill,**k)
    def path(s,d,fill=None,**k):
        return s.paint(s.ex("path.create",{"d":d})["id"],fill,**k)
    def text(s,x,y,t,size=24,color="#FFFFFF",font="Helvetica Neue",style="Bold",**extra):
        r=s.ex("text.create",{"x":x,"y":y,"text":t,"font":font,"style":style,"size":size,"color":color,**extra}); return r["id"] if isinstance(r,dict) else r
    def export(s,name="teste"):
        pdf=f"{s.dir}/{name}.pdf"
        s.ex("document.exportPdf",{"path":pdf,"preserveEditing":False})
        subprocess.run(f"cd {s.dir} && pdftoppm -r 50 -png {name}.pdf preview",shell=True)
        return pdf
    def close(s): s.vc.close()
