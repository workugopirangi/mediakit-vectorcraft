# R22. Selo dentado e sunburst

Status: FUNCIONA

## Sequência que funcionou (R22/teste.py)
1. `shape.star {cx,cy,radius1:R,radius2:R*0.93,points:24}` (dentes regulares; radius2 perto do radius1 dá serrilha curta). `select.set` + `paint.setFill {color}` + `paint.setStroke {none:true}`.
2. `effect.apply {effect:"stylize.roundCorners", params:{radius:R*0.02}}` com a estrela selecionada (efeito vivo, arredonda as pontas dos dentes).
3. Anel interno concêntrico: `object.path.offsetPath {offset:-R*0.11, joins:"round"}` (devolve `{ids}` novo, acima do original); pintar sem fill, traço de 2 pt.
4. Círculo interno `shape.ellipse` (r = 0,62 R, traço 1,5 pt) e rótulo `text.create` (Helvetica Neue Condensed Black).
5. Octógono de contraste: `shape.polygon {cx,cy,radius:110,sides:8}` + `object.path.offsetPath {offset:-14,joins:"round"}`.
Testado em três tamanhos (R=170 ouro, 130 prata, 100 bronze) com cores de metal.

## Veredito visual
Estúdio. Zoom a 200 ppi: dentes regulares, pontas levemente arredondadas, anel interno acompanha o contorno dentado em distância constante, sem emendas.

## Prova de que é vetor
`pdfimages -list`: só a foto de fundo aparece como imagem. O efeito `roundCorners` é um efeito vivo mas saiu como curva no PDF (não rasterizou). Fontes embutidas (Helvetica Neue Condensed Black e Bold).

## Armadilhas
- Primeira tentativa do anel interno com uma segunda `shape.star` menor deu um zigue-zague duro e feio. Usar `offsetPath` é o certo.
- Rótulo centralizado "no olho": para texto centralizado com precisão, medir a largura (ver R21) ou usar `text.setStyle` com alinhamento central em área.
- Rótulo longo (BRONZE) fica apertado no círculo de R=100; manter a razão tamanho_fonte = 0,36 R só até 5 letras.
