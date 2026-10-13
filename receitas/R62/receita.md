# R62. Fita adesiva, etiquetas e papel rotacionados

Status: FUNCIONA

## Comandos que funcionaram
- Polaroid: moldura `shape.rectangle` branca + `effect.apply {effect:"stylize.dropShadow", params:{blur:10, x:3, y:8, opacity:45, color:"#000000", mode:"multiply"}}` na moldura; foto em `file.place` + `object.setBounds {x,y,width:515, reference:0, proportional:true}` (só largura, para manter proporção) coberta por um quadrado 290x290 com `object.clippingMask.make`; legenda `text.create`; `select.set {ids:[moldura, grupo-da-foto, legenda]}`, `object.group`, `object.rotate {angle:4}` (graus, anti-horário, em torno do centro do grupo).
- Fita: `shape.rectangle {rotation:-6, ...}` (rotação em graus em torno do centro, direto na criação) + `paint.setFill` ouro + `transparency.set {opacity:72}`. Lê como fita translúcida (o papel aparece por baixo).
- Post-it com sombra dura: retângulo preto deslocado +10/+10, papel amarelo por cima, dois textos; grupo e `object.rotate {angle:-3}`. Sombra dura vetorial.
- Etiqueta com sombra macia: forma + dropShadow, texto, grupo, `object.rotate {angle:4}`.

## Prova
- teste.pdf, 1,03 MB. As fotos ficam a 234 ppi sem distorção (x e y iguais em `pdfimages`); as 3 sombras macias viram imagem+smask a 300 ppi (1697x1967, 1724x1989, 1607x718), recortadas ao tamanho da sombra e rotacionadas junto com o grupo, sem corte do halo. Fontes embutidas (Condensed Black, Bold, Medium).
- Conferi o preview: rotações limpas, sem serrilhado visível a 50 ppi.

## Gotchas
- Cometi um erro útil: `d.image(..., w, h)` com os dois valores ESTICA a imagem (a 415 x 234 ppi, distorcida). Para recortar quadrado de foto 16:9, passar só a largura/altura que preserva a proporção e deixar a máscara cortar.
- Rotacionar um grupo gira também a sombra: a sombra macia gira junto (a luz parece vir de outro lado). Para luz consistente, aplicar a sombra DEPOIS de rotacionar (aplicar o efeito no grupo já rotacionado: não testei) ou usar sombra dura desenhada deslocada em coordenadas de página.
- Texto criado depois de `object.rotate` não gira; agrupar antes de rotacionar.
- A rotação do `shape.rectangle` (`rotation`) só vale para a forma; texto e outros precisam de `object.rotate`.
- Efeito de sombra em grupo rotacionado gera imagem do tamanho da caixa rotacionada (maior que a original), a 300 ppi.

## Veredito visual
Qualidade de estúdio para colagem de bastidores; fita translúcida e polaroid convincentes. Textura de papel real (grão) não foi tentada, só faixas sutis.

## O que rasteriza
Sombras macias: smask a 300 ppi. Fotos: nativas. Fita, post-it, sombra dura, textos: vetor.
