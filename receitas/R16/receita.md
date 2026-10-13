# R16. Texto com contorno, vazado e preenchimento em gradiente

Status: FUNCIONA

## Sequência (R16/teste.py)
1. Vazado com contorno: `text.create {..., color:"#FFFFFF"}` e `text.setRangeStyle {id:t, fill:"none", stroke:"#D4A64A", strokeWidth:6, strokeOptions:{join:"round", cap:"round"}}` (devolve {id, runs:1}).
2. Contorno de ponta viva, para comparar: `strokeOptions:{join:"miter", miterLimit:10}`.
3. Gradiente no texto: `select.set {ids:[t]}` + `paint.setFill {gradient:{kind:"linear", angle:90, stops:[{offset:0,color:"#D4A64A"},{offset:1,color:"#E9603A"}]}}`. Sem erro (devolve None). Atenção: aplicado ao objeto de texto inteiro, a seleção tem que ser o texto, não um intervalo.

## Aparência (zoom a 130 e 200 dpi)
- Contorno de 6 pt em "42K" a 420 pt: linha uniforme, cantos limpos, sem pontas estouradas com join round. Qualidade de estúdio.
- "AMA" com miter limit 10 e com round: os dois saem limpos (cantos retos de 90 graus não estouram); a diferença só apareceria em ângulos agudos, não testei fonte com ângulo agudo forte.
- Gradiente: o degradê dourado para coral cobre o bloco de texto inteiro de cima a baixo (angle:90 dá dourado em cima), sem deslocamento visível. A leitura sobre foto com 55% de azul é boa.

## Cuidados
- O contorno é centrado no caminho (metade para dentro, metade para fora): ele engorda a letra; para título muito justo (tracking negativo), os traços de letras vizinhas se tocam.
- Texto continua vivo: o PDF embute Helvetica Neue CondensedBlack em `pdffonts`; nada rasteriza (a foto do fundo é JPEG, 84 ppi efetivos). PDF de 396 KB.
- Não testei gradiente aplicado a intervalo de caracteres (só ao objeto inteiro).
