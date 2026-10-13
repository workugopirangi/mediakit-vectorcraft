# R50. Cartões de KPI e numerais gigantes

Status: FUNCIONA

## Comandos que funcionaram
```
shape.rectangle {x,y,width:400,height:520,radius:18} + paint.setFill {color:"#0b2a40"}         # cartão
shape.rectangle (60x5) na cor do KPI                                                           # filete
text.create {font:"Helvetica Neue", style:"Bold", size:20, color}  + text.setRangeStyle {id, tracking:160}   # rótulo em caixa alta com espaçamento
text.create {text:"1.200atletas", size:150, style:"Condensed Black", color:"#FFFFFF"}           # numeral + unidade no mesmo texto
text.setRangeStyle {id, start:<byte>, end:<byte>, size:50, fill:"#E9603A"}                      # unidade menor e colorida (offsets em BYTES)
text.setRangeStyle {id, start, end, position:"superscript", fill}                              # % sobrescrito (testado: sobe e encolhe sozinho)
shape.rectangle (largura-72 x 1.5) + transparency.set {opacity:35}                              # régua fina
```
Nota: `text.create` NÃO aceita `tracking`; o espaçamento vai por `text.setRangeStyle {tracking}` (ou `text.setStyle`).

## Medição do alinhamento ótico (pixel, render a 144 ppi, borda esquerda esperada em x+36)
- Rótulo (Bold 20) e frase de apoio (Regular 22): começam em x+36 a x+37,5. Ok.
- Numeral Condensed Black 150 pt: borda esquerda do "1" 7,5 pt à direita da linha do rótulo (side bearing do 1); do "5" 3 pt à direita. Para alinhar ótico: deslocar o texto do numeral para a esquerda por dígito (aprox -7,5 pt para "1", -3 pt para "5" nesse corpo; escala com o corpo: cerca de 5% do tamanho para o 1, 2% para o 5).
- Não existe "optical margin alignment" (já anotado no plano).

## Veredito
Qualidade de estúdio: hierarquia clara (filete, rótulo espaçado, numeral gigante, régua, frase), unidade colorida e % sobrescrito funcionam, texto continua texto no PDF (fontes embutidas, selecionável, 0 imagens).

## Defeitos e armadilhas
- Meu primeiro tamanho (220 pt) estourou o cartão de 400 pt: "1.200" em Condensed Black 150 pt ocupa ~ 250 pt; palavras longas como a unidade "atletas" em 50 pt estouraram o cartão (vi no render). Medir largura antes (ou fit com `text.areaOptions`) e usar unidade curta (mil, %).
- Offsets de `start`/`end` do setRangeStyle são em BYTES UTF-8 (ex.: "çã" valem 2 bytes cada); usei só ASCII no numeral.
- Superscript em 150 pt sai grande (o `%` ficou de ~60% do corpo): combinar com `size` próprio se quiser menor.
