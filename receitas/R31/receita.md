# R31. Halftone raster por efeito (pixelate.colorHalftone)

Status: FUNCIONA (com três pegadinhas que mudam o resultado: ppi, maxRadius e modo de cor do documento)

## Sequência que funcionou (R31/teste.py)
1. `document.rasterEffectsSettings {resolution:300}` ANTES de aplicar o efeito.
2. `file.place` + `object.setBounds {reference:0}` da foto (420x575 pt).
3. `select.set {ids:[foto]}` e `effect.apply {effect:"pixelate.colorHalftone", params:{maxRadius:2.6}}` (efeito vivo, a foto continua editável; devolve `{ids,index,item}`).
4. `document.exportPdf` normal. Painéis lado a lado: efeito, `object.vectorHalftone` CMYK 20 lpi (R29/R30) e original.
Variante CMYK: `file.new {..., colorMode:"cmyk", rasterEffectsPpi:300}` e `params:{maxRadius:2.6, channel1:15, channel2:75, channel3:0, channel4:45}` (pasta `cmyk/`).

## Pegadinhas (medidas)
1. PPI: o padrão do documento é 72 ppi (`document.rasterEffectsSettings {}` lê `resolution:72`). Sem o passo 1 o PDF traz a imagem do efeito em 424x579 px (72 ppi, 435 KB), dots crus e pixelados. Com 300 ppi: 1767x2413 px (300 ppi).
2. `maxRadius` padrão = 8 pt: dots enormes, foto irreconhecível (primeira tentativa, vide texto no teste). Para equivaler a ~20 lpi, `maxRadius` ~2,6 pt (célula de 3,6 pt).
3. Modo de cor: em documento RGB o efeito faz telas R, G e B ADITIVAS (pontos vermelhos, verdes, azuis, ciano, magenta sobre fundo preto): look de luz, não de tinta. Em documento CMYK (`colorMode:"cmyk"`) sai a quadricromia com ciano, magenta, amarelo e preto, parecida com o vetorial do R29/R30 (zoom a 400 ppi, comparação em `R31/cmyk/z-1.png`). Mesmo assim o PDF embute a imagem como RGB, não CMYK.

## Peso (medido), painel de 420x575 pt a 300 ppi
- Efeito, documento RGB: imagem de 3,98 MB (flate sem perda). Efeito em documento CMYK: 5,64 MB.
- Vetorial CMYK 20 lpi (69.048 pontos): cerca de 5,9 MB.
- PDF total do teste: 10,4 MB (efeito 4 MB + vetorial ~6 MB + foto original 297 KB).
Ou seja, não é mais leve que o vetorial nessa escala, e perde nitidez em zoom.

## Comparação com R29/R30
A olho nu a 100 % (preview a 50 ppi): parecido, o vetorial é mais nítido e com cores mais fiéis; o efeito RGB é mais "neon". A 400 ppi o efeito é raster de 300 ppi (bordas suaves, sem pontos perfeitos); o vetorial permanece perfeito em qualquer zoom.

## Veredito visual
Aceitável a 100 % com 300 ppi e maxRadius ajustado; em RGB o look é diferente do impresso. Para entrega a gráfica ou zoom, preferir R29/R30 (vetor). Vantagem do efeito: continua vivo e editável (trocar maxRadius depois), e funciona em qualquer objeto, não só imagem.

## O que rasteriza
O efeito inteiro vira UMA imagem (RGBA) na resolução configurada, mais um smask de 8,7 KB. Nada de vetor nos pontos.
