# R61. Marcas de corte e sangria

Status: FUNCIONA pelo export (`document.exportPdf {marks, bleed}`); PARCIAL pelo objeto (`object.createTrimMarks` não sobrevive ao export sem ampliar a página)

## Comandos que funcionaram (caminho recomendado)
```
file.new {width:1440, height:810, units:"Points", bleed:8.5}
# arte de fundo cobrindo -8.5..1448.5 x -8.5..818.5
document.exportPdf {path, preserveEditing:false, bleed:{useDocument:true},
  marks:{trim:true, registration:true, colorBars:true, pageInfo:true, kind:"roman", weight:0.25, offset:12}}
```
Resultado (`pdfinfo -box`): MediaBox 1500.5 x 881.7; TrimBox 30.25,41.45 a 1470.25,851.45 (= 1440 x 810 exatos); BleedBox = Trim + 8.5 em cada lado. Marcas de corte romanas nos cantos, alvos de registro no meio dos lados, barra de cores CMYK/cinzas no topo e linha de informação (título, prancheta, data UTC) embaixo. Fonte da página embutida (HelveticaNeue CondensedBlack). Marcas ficam fora da sangria (offset 12 > 8.5) e com 0,25 pt.

## Caminho alternativo (marcas como objeto)
`object.createTrimMarks {style:"roman", offset:12, length:18, weight:0.25, allArtboards:true}` cria um grupo "Trim Marks" que vai de -30 a 1470 (1500 x 870). Funciona e é editável, MAS o export normal corta a página na prancheta (PDF 1440 x 810, todas as caixas iguais) e as marcas desaparecem. Para usar isso seria preciso ampliar a prancheta ou exportar com sangria que cubra as marcas. Não recomendo; usar `marks` do export.

## Gotchas
- A página exportada NÃO é 1440 x 810: o gráfico deve ler a TrimBox. Para conferência visual, o preview do poppler mostra a MediaBox inteira.
- Para o fundo realmente sangrar, a arte precisa existir fora da prancheta (-8.5). A foto que usei (c-portico) ficou 815 pt de altura e não cobriu a sangria de baixo; o retângulo de cor por baixo segurou. Em produção, dimensionar a foto com folga.
- No preview a 50 ppi as marcas de 0,25 pt quase somem; conferir a 300 ppi (aparecem nítidas, barra de cores com 8 amostras).
- Acentos do título (VERSÃO GRÁFICA) saem corretos; no preview de 50 ppi sobre foto o til some visualmente, é só resolução.
- Não testei `kind:"japanese"` no export nem `bleed` assimétrico.

## Veredito
Estúdio pelo caminho do export.

## O que rasteriza
Nada neste teste (foto JPEG nativa).
