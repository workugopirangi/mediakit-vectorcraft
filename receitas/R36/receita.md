# R36. Gradiente freeform (campos de cor orgânicos)

Status: FUNCIONA (com ressalva: vira imagem raster de baixa resolução no PDF)

## Comandos que funcionaram
```
shape.rectangle {x:0,y:0,width:1440,height:810}  + paint.setFill {color}   (fundo sólido primeiro)
select.set {ids:[id]}
paint.editGradient {ids:[id], stroke:false, kind:"freeform", mode:"points",
                    stops:[{offset:0,color:"#0F3550"},{offset:0.5,color:"#9FE3D0"},{offset:1,color:"#E9603A"}]}
   -> cria grade automática de 8 pontos coloridos ao longo dos stops
paint.freeform.addPoint {ids:[id], stroke:false, at:[200,150], color:"#E9603A", spread:0.3}   (-> {index})
paint.freeform.get {stroke:false}   (lista pontos, cor RGB 0..1, spread)
paint.editGradient {... mode:"lines"} gera campos em linhas (usei no card arredondado)
```
Não rodei `paint.freeform.addLine` (o modo `lines` do editGradient já mostrou o efeito).

## Medição do raster (pdfimages -list)
- Fundo página inteira 1440x810 pt: imagem 512x288 px = 26 ppi, 93 KB.
- Card 440x280 pt: imagem 512x326 px = 84 ppi, 15 KB.
- A imagem tem sempre ~512 px no lado maior, independente do tamanho do objeto e de `document.rasterEffectsSettings {resolution:300}` (testei com 300 ligado: não mudou). PDF da página: 128 KB.
- Imagem com `/Interpolate` (interp yes): o leitor suaviza. A 250 ppi no zoom e no sips (macOS) o campo de cor ficou liso, sem pixels, sem emenda, sem cruz. Texto por cima continua vetor (fontes embutidas).

## Veredito
Visual bonito e orgânico, adequado para fundo de capa. Para impressão de gráfica a 26 ppi só é seguro porque gradiente suave não tem detalhe; pontos com spread pequeno e transições bruscas ficariam borrados. Não use para forma com bordas nítidas dentro do campo.

## Defeitos e armadilhas
- OBRIGATÓRIO passar `stroke:false` em `paint.editGradient`, `paint.freeform.get` e `addPoint`. Sem isso, o gradiente freeform foi parar no TRAÇO (linha fina colorida na borda do retângulo) e o preenchimento ficou sólido. Foi assim que errei duas vezes.
- `paint.setFill {gradient:{kind:"freeform"}}` não funcionou como esperado: o comando seguinte `paint.freeform.get` disse "the paint is not a freeform gradient". Use `paint.editGradient`.
- `spread` é fração do meio lado maior: 0.3 já faz mancha chapada enorme (ficou "bolha"). Para aurora suave use 0 a 0.1.
- Cores fora da paleta aparecem fácil (usei roxo de propósito para testar; evitar em kit).
- Cada objeto freeform gera uma imagem: 10 cards = 10 imagens.
