# R20. Texto em caminho livre (curva, onda, arco)

Status: FUNCIONA

## Sequência que funcionou (R20/teste.py)
1. `path.create {d:"M120,330 C 380,60 760,60 1020,330"}` (curva livre, sem preenchimento, sem traço: `paint.setFill {none:true}`, `paint.setStroke {none:true}`).
2. `text.createInPath {path:<id>, mode:"onPath", text, size, font, style, color}` devolve o id do texto (a tinta do caminho é descartada pelo comando).
3. Ajuste: `select.set {ids:[texto]}` e `type.pathOptions {start:0.02, alignToPath:"baseline", spacing:4}`. Sem parâmetros, devolve as opções atuais (`effect:"rainbow"`, `flip:false`, `start:0`, `end:null`).

## Casos testados e resultado (sobre foto aérea c-arena.jpg)
- Arco (Bezier cúbica única): letras acompanham, sem sobreposição, curva suave.
- Onda com 3 segmentos (C + S + S) com texto longo: segue bem, sem pinçar nas inflexões. Letras ao redor do cume ficam levemente abertas do lado convexo (comportamento esperado de texto em curva).
- Curva em S apertada (raio pequeno, 34 pt): zoom a 220 ppi sem letras sobrepostas, só abertura entre letras no lado de fora.

O risco "curvas em S podem pinçar letras" NÃO se confirmou nestes casos.

## Veredito visual
Estúdio. Fontes embutidas (pdffonts: Helvetica Neue Condensed Black, Avenir Next Demi Bold, Futura Medium), texto segue vivo (editável), nada rasterizado fora a foto.

## Armadilhas
- O texto precisa caber no comprimento do caminho, senão corta (não testei o aviso de estouro).
- Legibilidade em foto agitada depende de tarja/escurecimento (usei azul-mar a 55 %).
- Posição final do texto sobre o caminho: usar `start` (0..1) em vez de mover.
