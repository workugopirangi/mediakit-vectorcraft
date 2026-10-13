# R04. Tipografia gigante sangrando da página

Status: FUNCIONA

## Sequência (R04/teste.py)
1. Fundo `shape.rectangle` 1440x810 amarelo.
2. `text.create {x:-30, y:520, text:"CORRA\nSEM PARAR", font:"Helvetica Neue", style:"Condensed Black", size:560, color:K}` + `text.setStyle {ids, tracking:-20, leading:470}` (duas linhas num objeto só; x negativo faz sangrar à esquerda).
3. `select.set {ids:[fundo, texto, rotulo]}` + `object.group {}`.
4. Retângulo 1440x810 por cima (qualquer cor), `select.set {ids:[grupo, retangulo]}` + `object.clippingMask.make {}`.
5. Export normal: MediaBox 1440 x 810, CropBox igual.

## Aparência
Corte limpo nas bordas direita e inferior, sem vazamento. Leitura dura de estúdio (estilo Nike). Qualidade de estúdio.

## Defeitos e cuidados
- Tracking -20 em 560 pt encosta os dois R; ajuste caso a caso.
- Medido: em 560 pt "CORRA" mede mais de 1500 pt de largura (sangra à direita de propósito).
- Sem rasterização. PDF de 10 KB, fonte vira caminho dentro da máscara (não aparece em pdffonts).
- A máscara é necessária em kits com várias artboards (GAP de 2000 pt), onde o texto vazaria para a vizinha; não testei multi-artboard, só a página única.
