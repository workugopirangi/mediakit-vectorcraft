# R43. Marca-texto (highlighter) e sublinhado irregular

Status: FUNCIONA (4 técnicas boas; 1 técnica quebrada: roughen direto em traço grosso)

## Técnicas que funcionaram
1. Marca-texto com bordas irregulares (a melhor): retângulo amarelo criado DEPOIS do texto (fica por cima) + roughen + Multiply.
```
shape.rectangle {x:76,y:215,width:630,height:52} + paint.setFill {color:"#F5D80A"} + paint.setStroke {none:true}
effect.apply {effect:"distort.roughen", ids:[id], params:{size:3, relative:false, detail:25, points:"smooth", seed:4}}
transparency.set {ids:[id], blend:"Multiply"}
```
Multiply deixa o texto preto legível por baixo do amarelo, borda levemente serrilhada de marcador.
2. Traço de marca-texto: `path.create {d:"M 84 410 C 250 402 420 416 620 405 S 740 408 760 406"}` + `paint.setStroke {color:"#E9603A"}` + `stroke.set {weight:46, cap:"round", join:"round"}` + `transparency.set {blend:"Multiply", opacity:85}`. Pontas redondas, caimento natural, bom.
3. Sublinhado rabiscado: retângulo fino (16 pt) + `effect.apply {effect:"stylize.scribble", params:{angle:-8, strokeWidth:3, spacing:4, curviness:30, variation:1.5, seed:2}}`. Vira hachura de caneta; denso, serve para sublinhado de destaque.
4. Sublinhado com pincel: `brush.new {type:"calligraphic", name:"marca", params:{angle:20, roundness:30, size:10}}` + `brush.apply {name:"marca", ids:[id]}` num path com traço 8 pt. Saiu com afinamento natural nas pontas, bonito.

## Defeito encontrado
- `distort.roughen` aplicado a um TRAÇO grosso aberto (30 a 46 pt, cap round) com size 4 pt e detail 30/pol gera espinhos enormes (dezenas de pt), inutilizável. Com size 1.2 / detail 10 sai suave. Se o efeito estiver no traço, os parâmetros se comportam fora de escala; o mesmo roughen (size 3, detail 30) no retângulo preenchido, ou depois de `object.path.outlineStroke`, sai discreto e correto. Regra: roughen só em formas preenchidas ou depois de `outlineStroke`.

## Gotchas
- `transparency.set {blend:"Multiply"}` retorna vazio mas funciona (conferido no render).
- Nenhuma imagem: tudo vetor (pdfimages vazio, PDF 47 KB).
- Aplicar o efeito antes do Multiply, na ordem que o Appearance executa, não deu conflito.
