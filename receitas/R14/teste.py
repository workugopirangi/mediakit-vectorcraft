import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R14"); ex = p.ex
p.rect(0, 0, 1440, 810, W)
im = p.img(PH + "f7.jpg", -50, 0, 540, 810)
m = p.rect(0, 0, 440, 810, "#FF0000"); ex("select.set", {"ids": [m]}); ex("object.arrange.bringToFront", {})
ex("select.set", {"ids": [im, m]}); ex("object.clippingMask.make", {})
p.text(500, 130, "SOBRE O EVENTO", "Helvetica Neue", "Bold", 14, CORAL, tracking=250)
p.text(500, 220, "Uma corrida que\nmovimenta a cidade", "Helvetica Neue", "Condensed Black", 80, SEA, leading=76, tracking=-5)
TXT = ("A Sprint Ubatuba Run nasceu em 2023 com 800 corredores e hoje reúne mais de 12 mil pessoas em três dias de programação na orla. "
 "A largada acontece em frente ao pórtico principal, e os percursos de 5, 10 e 21 quilômetros passam por praias, calçadões e pelo centro histórico.\n"
 "Para as marcas parceiras, o evento entrega presença física e digital: pórtico de largada, camisetas, tendas de ativação, medalhas e conteúdo "
 "produzido durante todo o fim de semana. Cada cota inclui direitos de imagem e relatório de resultados.\n"
 "O público é majoritariamente adulto, com renda média e alta, e viaja de cidades vizinhas para participar. Mais da metade dos inscritos compartilha "
 "fotos e vídeos da prova nas redes sociais nos dias seguintes, o que prolonga a exposição das marcas patrocinadoras.\n"
 "A organização trabalha com cronometragem oficial, equipe médica, hidratação a cada dois quilômetros e uma estrutura pensada para atletas de todos os níveis, "
 "do iniciante ao elite. A edição de 2027 amplia a arena de ativações e inclui uma feira de saúde e esportes aberta à comunidade.")
r = ex("text.create", {"x": 500, "y": 400, "text": TXT, "font": "Source Sans 3", "style": "Regular", "size": 15, "color": K, "area": {"width": 860, "height": 255, "fit": "none"}})
print(r); t = r["id"]
ex("text.setStyle", {"ids": [t], "leading": 22})
ex("select.set", {"ids": [t]}); print(ex("text.setFormat", {"spaceAfter": 8}))
ex("select.set", {"ids": [t]})
print(ex("text.areaOptions", {"ids": [t], "columns": 3, "gutter": 28, "inset": 0, "verticalAlign": "top"}))
p.export()
