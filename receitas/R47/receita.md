# R47. Linhas de rota (circuito, turnê)

Status: FUNCIONA

## Comandos que funcionaram
```
path.create {d:"M 120 300 C 300 120 520 480 760 260 S 1100 200 1280 330"}
paint.setFill {none:true}; paint.setStroke {color:"#9FE3D0"}
stroke.set {weight:6, cap:"round", dash:[0,14], endArrow:"Arrow", arrowAlign:"tip"}      # pontilhado redondo contínuo com seta
stroke.set {weight:5, cap:"round", dash:[16,10], startArrow:"Circle", endArrow:"ArrowOpen"}  # tracejado, círculo no início, seta aberta
stroke.set {weight:10, cap:"round", endArrow:"TriangleBar"}                              # sólida
shape.ellipse + text.create   # marcadores numerados
text.createInPath {path:id, mode:"onPath", text:"São Paulo  Taubaté  São José  Ubatuba", size:26, font:"Helvetica Neue", style:"Bold", color:"#FFFFFF"} -> {id}
```

## Veredito
Qualidade de estúdio. `dash [0,14]` com cap round gera pontos redondos perfeitos e igualmente espaçados em curva (zoom 200 ppi); setas funcionam também em traço pontilhado e tracejado (o risco anotado no plano não se confirmou). Texto na curva acompanha o path e as letras ficam legíveis. Vetor puro: 0 imagens.

## Defeitos e armadilhas
- A seta "Arrow" em traço fino (6 pt) fica pequena e de contorno fraco sobre pontilhado; para destaque usar TriangleBar/Triangle e traço ≥ 8 pt ou `stroke.setAdvanced {arrowScale}` (não testei).
- `text.createInPath` descarta o paint do path (o traço some, só fica o texto): se quiser linha + texto, duplique o path antes.
- Marcadores devem ser posicionados com pontos reais da curva; marquei dois fora da linha (erro de coordenada meu, não do comando). Para exatidão calcule o ponto da bezier em Python (de Casteljau) e coloque o marcador ali.
- Em curvas muito fechadas o dash [0,gap] distorce o espaçamento nas voltas internas (não testado a fundo).
