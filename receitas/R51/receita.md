# R51. Sombra projetada em 300 ppi e sombra dura vetorial

Status: FUNCIONA

## Comandos que funcionaram
- `document.rasterEffectsSettings {resolution:300}` (ou `"high"`).
- Sombra macia: `select.set {ids:[cartao]}` e `effect.apply {effect:"stylize.dropShadow", params:{blur:24, x:0, y:16, opacity:45, color:"#0F3550", mode:"multiply"}}`.
- Sombra dura vetorial: criar ANTES do cartão um `shape.rectangle` preto com x+14, y+14 (a ordem de empilhamento coloca o cartão por cima). Vetor puro, borda nítida, zero raster.
- Exportar: `document.exportPdf {path, preserveEditing:false}`.

## Prova
- teste.pdf (300 ppi): 674 KB. `pdfimages -list` mostra a sombra como imagem 2034x2034 e 1751x1751 a 300 ppi, com soft mask (smask), um par por cartão.
- teste-72.pdf (mesma página, resolução 72): 573 KB, sombras em 488x488 e 420x420 a 72 ppi.
- Fontes embutidas (HelveticaNeue CondensedBlack, Medium, Bold, subset). Texto continua vetorial.

## Veredito visual
Qualidade de estúdio para a sombra dura (vetor). A sombra macia é correta e sem serrilhado a 300 ppi; a 72 ppi, por ser blur, o olho quase não nota, mas em zoom de gráfica a borda fica mole. Recomendo usar 300.

## Gotchas
- A resolução de raster é lida NA EXPORTAÇÃO (configuração do documento), não na hora do `effect.apply`. Não dá para ter um objeto a 72 e outro a 300 no mesmo PDF alternando a configuração entre os `effect.apply`: o teste mostrou que os dois saem na resolução vigente no export.
- O efeito é aplicado ao objeto inteiro: cada cartão com sombra gera 2 imagens (cor + smask). Dezenas de cartões inflam o arquivo pouco (25 a 50 KB cada, pois são quase lisos).
- Sombra no `multiply` sobre fundo escuro some. Em fundo escuro use sombra dura, ou opacity alto.
- Elementos filhos que não são o objeto com efeito (cabeçalho colorido do cartão) ficam por cima e não projetam sombra própria. Se o cabeçalho for retangular e o cartão tiver cantos arredondados, o cabeçalho "fura" o canto (defeito de desenho, resolver com máscara).
- A foto de acervo (tratado/c-arena.jpg, 1672 px) cobre 1440 pt a só 84 ppi. É limite do arquivo-fonte, não do VectorCraft.

## O que rasteriza e a que ppi
Só a sombra macia (stylize.dropShadow), na resolução configurada (72/150/300). Sombra dura, formas e texto: vetor.
