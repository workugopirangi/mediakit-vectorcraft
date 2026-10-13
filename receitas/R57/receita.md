# R57. Exportação PDF/X-4 (gráfica)

Status: FUNCIONA na estrutura (conferida com pypdf); conformidade formal NÃO verificada (sem veraPDF, sem Ghostscript)

## Comandos que funcionaram
```
file.new {width:1440, height:810, units:"Points", colorMode:"cmyk", bleed:8.5}
document.rasterEffectsSettings {resolution:300}
# arte com sangria: fundo -8.5,-8.5 1457x827; foto sangrando a 728.5 de largura
paint.setFill {color:{c:0,m:8,y:96,k:0}}        # cor CMYK direta
swatch.new {name:"Dourado Sprint", color:{c:20,m:40,y:80,k:0}, spot:true}
document.exportPdf {path, standard:"pdfX4", preserveEditing:false,
  bleed:{top:8.5,bottom:8.5,left:8.5,right:8.5},
  marks:{trim:true, registration:true, colorBars:false, pageInfo:false, weight:0.25, offset:12},
  output:{conversion:"destination", outputIntent:"VectorCraft Generic CMYK (SWOP-like)",
          outputCondition:"Generic CMYK (SWOP-like)", trapped:false}}
```
Retorno: 1,78 MB, `warnings: []`. `document.pdfInfo {path}` devolve as caixas.

## O que conferi (pypdf 6.13 + pdfinfo + pdffonts + pdfimages)
- PDF 1.6. `/OutputIntents` com `/S /GTS_PDFX`, `/DestOutputProfile` ICC embutido (158 KB, espaço CMYK, classe prtr, N=4).
- `/GTS_PDFXVersion (PDF/X-4)` no Info e no XMP (`pdfxid:GTS_PDFXVersion`); `/Trapped /False`.
- Caixas: TrimBox 1440x810 (30.25..1470.25 x 30.25..840.25), BleedBox = Trim + 8.5 em cada lado, MediaBox/CropBox 1500.5 x 870.5 (inclui a área das marcas). Corretas.
- Fontes embutidas e subsetadas (HelveticaNeue CondensedBlack e Bold), sem fonte faltando.
- Transparência mantida (X-4): grupos `/S /Transparency`, `/ca` e `/CA` em ExtGState, soft mask (sombra), sem achatamento.
- Cores: só ICCBased (CMYK) e Separation; a foto saiu `icc 4 componentes` JPEG (convertida de RGB para CMYK, 190 ppi); sombra 300 ppi; tinta direta "Dourado Sprint" como `/Separation` com alternativa CMYK [0.2 0.4 0.8 0]; marcas em `/Separation /All` (registro).
- Marcas de corte e alvos de registro aparecem no preview, fora da sangria.

## NÃO verificado (honesto)
- veraPDF e Ghostscript não existem nesta máquina, então não há validação formal de conformidade PDF/X-4. Conferi só os itens estruturais acima.
- Não varri os content streams à procura de operadores `rg`/`g` (RGB/cinza de dispositivo) fora dos espaços declarados; nos recursos não apareceu DeviceRGB.
- O perfil de saída é o "VectorCraft Generic CMYK (SWOP-like)", genérico. Não há FOGRA39/FOGRA51/SWOP certificado nas opções (`edit.colorSettings` lista só 6 perfis). Para gráfica real é preciso o perfil que a gráfica pede (carregar e conferir se o motor aceita perfil externo: não testado).
- Título do PDF saiu "Untitled-2" (dar `name` no `file.new`).
- Preto 100K (CMYK 0,0,0,100) é preto "puro", mas poppler o mostra cinza escuro (#35 31 32) por causa do ICC; é normal, não é defeito.

## Gotchas
- Escolher `standard:"pdfX4"` já desliga `preserveEditing` (senão recusa).
- A MediaBox cresce com `marks.offset` + sangria; a página vira 1500 x 870, não 1440 x 810. O TrimBox é que vale.
- Sombra e foto em fundo transparente exigem X-4; X-1a/X-3 achatam (não testado aqui).

## Veredito
Bom o bastante para mandar a um prepress experiente testar com Preflight; ainda não posso afirmar "passa em PDF/X-4" sem validador.

## O que rasteriza
Sombra: 300 ppi (smask). Foto: JPEG CMYK em ~190 ppi, sem reamostrar. Resto vetor.
