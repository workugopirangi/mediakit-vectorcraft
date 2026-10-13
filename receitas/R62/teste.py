import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R62")
d.ex("document.rasterEffectsSettings", {"resolution": 300})
d.rect(0, 0, 1440, 810, CREAM)
# textura simples de papel: faixas muito sutis
for i in range(0, 810, 6): d.rect(0, i, 1440, 1, "#E8D49C", opacity=35)
d.text(60, 120, "BASTIDORES", "Helvetica Neue", "Condensed Black", 100, SEA)
d.text(60, 160, "Colagem: polaroid, fita e post-it com rotação e sombra", "Helvetica Neue", "Bold", 22, CORAL)

def shadow_hard(x, y, w, h, dx=8, dy=8, rot=0, cx=None, cy=None):
    return d.rect(x + dx, y + dy, w, h, K, opacity=100)

def polaroid(x, y, photo, ang, soft=True, w=330, h=400, crop_focus=0):
    parts = []
    fr = d.rect(x, y, w, h, "#FFFFFF"); parts.append(fr)
    if soft:
        d.ex("select.set", {"ids": [fr]})
        d.ex("effect.apply", {"effect": "stylize.dropShadow", "params": {"blur": 10, "x": 3, "y": 8, "opacity": 45, "color": "#000000", "mode": "multiply"}})
    im = d.image(photo, x + 20 - 112, y + 20, 515)  # proporcional, altura 290; a máscara recorta o quadrado
    m = d.rect(x + 20, y + 20, 290, 290, K)
    d.ex("select.set", {"ids": [im, m]}); g = d.ex("object.clippingMask.make")["id"]; parts.append(g)
    t = d.text(x + 30, y + 360, "Ubatuba, 2026", "Helvetica Neue", "Medium", 24, SEA); parts.append(t)
    d.ex("select.set", {"ids": parts}); grp = d.ex("object.group", {})["id"]
    d.ex("object.rotate", {"angle": ang})
    d.ex("select.none"); return grp

def tape(cx, cy, ang, w=130, h=40):
    t = d.rect(cx - w / 2, cy - h / 2, w, h, GOLD, opacity=72, rotation=ang)
    return t

# fotos quadradas: usar as de acervo (proporção livre: duas serão cortadas pela máscara; aqui a imagem é esticada? evitar: ver defeitos)
p1 = polaroid(80, 220, SP + "/tratado/c-tendas.jpg", 4)
p2 = polaroid(470, 250, SP + "/tratado/c-asas.jpg", -5)
tape(245, 225, -6); tape(635, 255, 7)
# post-it com sombra dura, tudo agrupado e rotacionado
sx, sy = 880, 260
sh = d.rect(sx + 10, sy + 10, 280, 280, K)
pi = d.rect(sx, sy, 280, 280, "#FFE55C")
t1 = d.text(sx + 24, sy + 70, "LEMBRAR:", "Helvetica Neue", "Condensed Black", 44, K)
t2 = d.text(sx + 24, sy + 120, "pedir logo vetorial\nao patrocinador", "Helvetica Neue", "Bold", 24, K, leading=30)
d.ex("select.set", {"ids": [sh, pi, t1, t2]}); d.ex("object.group", {}); d.ex("object.rotate", {"angle": -3}); d.ex("select.none")
d.ex("select.none")
tape(sx + 140, sy - 2, 3, 120, 36)
# etiqueta rotacionada com sombra macia (grupo: forma com efeito + texto)
tk = d.rect(1000, 600, 340, 110, CORAL, radius=10)
d.ex("select.set", {"ids": [tk]}); d.ex("effect.apply", {"effect": "stylize.dropShadow", "params": {"blur": 8, "x": 4, "y": 6, "opacity": 50}})
tt = d.text(1028, 668, "COTA OURO", "Helvetica Neue", "Condensed Black", 56, "#FFFFFF")
d.ex("select.set", {"ids": [tk, tt]}); d.ex("object.group", {}); d.ex("object.rotate", {"angle": 4}); d.ex("select.none")
p = d.export(); report(p); d.close()
