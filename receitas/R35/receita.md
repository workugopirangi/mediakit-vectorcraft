# R35. Gradiente radial como holofote

Status: FUNCIONA

## Comandos que funcionaram
- Holofote com transparência: `shape.ellipse` + `paint.setFill {gradient:{kind:"radial", stops:[{offset:0,color:"#D4A64A",opacity:0.85},{offset:1,color:"#D4A64A",opacity:0}]}}` + `paint.setStroke {none:true}` + `transparency.set {ids:[id], blend:"Screen"}`.
- Elipse via `aspect:45` (porcentagem altura/largura) num retângulo, 3 stops com opacity (0.55, 0.15, 0).
- Foco deslocado: `paint.setGradientGeom {ids:[id], start:[350,660], end:[610,660], focal:[200,620], stroke:false}`.

## Veredito
Qualidade de estúdio. Centro claro, borda totalmente transparente, SEM anel cinza (mantenha a mesma cor nos stops e varie só a opacity; testei também branco opaco para preto com opacity 0 e não houve anel). Idêntico no pdftoppm e no sips (macOS).
No PDF: `/ShadingType 3` (radial) com `/SMask` para a opacidade e `/BM /Screen`, tudo vetor. Única imagem da página é a foto (jpeg 935x1280 em 580x795 pt = 116 ppi, é limite da foto, não do gradiente).

## Defeitos e armadilhas
- Screen em dourado sobre foto clara dá efeito sutil. Para holofote forte use opacity 1 no stop 0 e raio maior que o sujeito.
- Gradiente radial num retângulo respeita o retângulo: se o último stop não chegar a transparente dentro do retângulo, aparece borda reta (vi isso no bloco coral, erro meu). Use elipse ou garanta raio menor que a metade do menor lado.
- Sem `start/end`, o gradiente é ajustado aos limites de cada objeto. Com `start/end`, eles são coordenadas do documento.
- `setGradientGeom` precisa de `stroke:false` (ver R34).
- Nada rasteriza.
