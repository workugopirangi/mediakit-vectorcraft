# R01. Duotone de foto

Status: FUNCIONA

## Sequência que funciona (R01/teste.py)
1. `file.place {path, link:false}` e `object.setBounds {x,y,width,height,reference:0}` para cobrir a área.
2. `edit.colors.toGrayscale {ids:[img], includeImages:true}` (age só na cópia embutida; o arquivo original não muda).
3. `shape.rectangle` com a cor clara (amarelo #F5D80A) do mesmo tamanho da foto, `paint.setStroke {none:true}`.
4. `transparency.set {ids:[ret], blend:"Multiply"}`.
5. `select.set {ids:[img, ret]}` e `object.group {}`.
6. Retângulo da área visível por cima, `select.set {ids:[grupo, mascara]}`, `object.clippingMask.make {}`.
Fundo escuro da marca (#0B0B0C) vem do preto da foto em Multiply: sombras ficam pretas, altas luzes viram amarelo.

## Aparência
Qualidade de estúdio no PNG: transição suave de preto a amarelo, sem banding visível, borda do recorte limpa. Efeito é o clássico duotone Nike-like.

## Defeitos e cuidados
- A imagem sai no PDF a 85 ppi efetivos, só porque a foto de origem tem 853 px de largura esticada em 720 pt. Não é defeito do VectorCraft; vale usar foto maior ou cobrir menos área.
- Não rasteriza nada: a imagem continua como foto RGB original e o Multiply sai como transparência viva (`/BM /Multiply`, confirmado no PDF). Só testei no poppler (pdftoppm). Preview/Chrome não foram conferidos, risco de blend permanece teórico.
- Não testei `adjustBalance` nem a variante `recolor.apply` (o Multiply bastou).
- PDF: 578 KB.
