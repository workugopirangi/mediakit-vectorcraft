# R52. Brilho (outer glow) e feather

Status: PARCIAL (glow funciona; feather funciona em forma, mas ESTRAGA foto; use máscara de opacidade para foto)

## Comandos que funcionaram
- `document.rasterEffectsSettings {resolution:300}`.
- Glow em texto vivo (continua texto selecionável, fonte embutida): `select.set {ids:[texto]}` e `effect.apply {effect:"stylize.outerGlow", params:{blur:22, color:"#F5D80A", mode:"screen", opacity:85}}`.
- Glow em forma (pílula com traço): mesmo comando; sai sem corte nas bordas.
- Feather em FORMA lisa: `effect.apply {effect:"stylize.feather", params:{radius:25}}`; borda suave correta, miolo sólido.
- Borda suave em FOTO (plano B que funciona): colocar a imagem, desenhar um retângulo por cima, `paint.setFill {gradient:{kind:"radial", stops:[{offset:0,color:"#FFFFFF"},{offset:0.55,color:"#FFFFFF"},{offset:1,color:"#000000"}]}}`, `select.set {ids:[imagem, retangulo]}`, `transparency.makeOpacityMask {}`. A foto fica nítida e some nas bordas; é máscara vetorial, a foto não rasteriza de novo (259 ppi nativos).
- Fade de cor por cima (foto "entrando" no bloco de cor): retângulo + `paint.setFill {gradient}` e depois `paint.editGradient {ids:[id], stops:[{offset:0,color:..., opacity:1.0},{offset:1,color:..., opacity:0.0}]}`. Opacidade em fração 0 a 1.

## Prova
- teste.pdf: 995 KB. pdfimages: cada glow/feather vira par imagem + smask a 300 ppi (texto 2967x1625, pílula 1817x609, feather 3351x517). Foto mascarada fica JPEG 2880x1621 (259 ppi) sem recompressão.
- Fonte HelveticaNeue CondensedBlack e Bold embutidas.

## Defeitos e gotchas (honestos)
1. `stylize.feather` aplicado direto em IMAGEM desfoca a imagem INTEIRA (mesmo com raio 4 já amolece), não só a borda. Testado: imagem solta, imagem dentro de clip group, raios 4, 20, 45. Reprovado para foto. Em Illustrator o feather só dissolve a borda; aqui não.
2. Feather ou glow em objeto grande rasteriza o objeto e o halo inteiro: uma foto 740 pt gerou imagem 3100x1753 a 300 ppi. Foto que sai da prancheta rasteriza a parte fora da prancheta também (testei com foto alta: imagem 2850x6152, PDF de 4,8 MB). Sempre recortar ou posicionar dentro da página antes de aplicar efeito.
3. Há um fio escuro finíssimo no contorno das letras com glow quando se dá zoom de 150 ppi (artefato da borda do soft mask do glow). Invisível em 50 ppi, perceptível em zoom de impressão. Não consegui eliminar; aceitar em tela, conferir em gráfica.
4. Em `paint.setFill {gradient}` a opacidade dos stops não pegou (saiu tinta chapada); funcionou com `paint.editGradient` depois. Ordem: setFill, depois editGradient.
5. Resolução do raster é a do documento NO EXPORT (ver R51).

## Veredito visual
Glow de texto e de forma: qualidade de estúdio em tela. Feather de foto: não usar. Máscara radial de foto: estúdio.

## O que rasteriza e a que ppi
Glow e feather: sempre raster, na resolução do documento (300 testado). Máscara de opacidade com gradiente e fade de gradiente: vetor (shading), a foto fica nativa.
