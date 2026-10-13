# R56. Parede de logos de patrocinadores

Status: FUNCIONA (com ressalva de qualidade do material de origem e de logos detalhados)

## Material de teste
Não existem logos individuais no acervo, só o quadro patrocinadores-2026.png (939x1030). Recortei 15 logos com PIL (caixa + autocrop do alfa) em R56/logos/*.png; cada um tem só 80 a 270 px de largura. Isso é entrada preparada fora do VectorCraft.

## Comandos que funcionaram
- Colocar: `file.place {path, link:false}` e `select.set {ids}`.
- Caixa óptica: calculei por logo largura = raiz(14000 x proporção), altura = largura / proporção, limitada a 190 x 90 pt, e usei `object.setBounds {x:cx, y:cy, width, height}` (referência padrão = CENTRO, então x,y já é o centro da célula; não precisa de align).
- Versão BRANCA (para fundo escuro): `effect.apply {effect:"adjust.levels", params:{outputBlack:255, outputWhite:255}}` no logo selecionado. Preserva o alfa e vira silhueta branca.
- Versão PRETA (para fundo claro): mesmo efeito com `outputBlack:0, outputWhite:0`.
- Alternativa que também deu silhueta branca: `edit.colors.adjustBalance {mode:"rgb", r:100, g:100, b:100, includeImages:true}`.
- `edit.colors.toGrayscale {includeImages:true}` só dá cinza (não serve para monocromo). `adjust.brightnessContrast` com 100/100 deixou parte da cor (não serve).
- Exportar normal. teste.pdf = branco sobre azul-mar; teste-preto.pdf = preto sobre creme.

## Prova
- 15 imagens + 15 smasks no PDF, sem reamostragem: continuam em 33 a 76 ppi nativos (`pdfimages -list`). O efeito de levels não rasterizou nem aumentou resolução.
- Grade 5x3 alinhada pelo centro de cada célula, peso óptico visualmente parecido.

## Defeitos (honestos)
1. Qualidade: os logos do quadro são de baixa resolução; a 1440 x 810 ficam com 33 a 76 ppi. Em tela cheia aparecem serrilhados/moles; em impressão é inaceitável. Pedir logo vetorial (SVG/PDF) ao patrocinador é obrigatório para o kit final. `file.place` aceita SVG/PDF (não testado aqui).
2. Silhueta monocromática destrói logos com detalhe interno: o cachorro (dogs), a asa FENIX GYM, o selo TACHÃO e o GELO do PORTO viram manchas brancas. Só funciona bem para logos de traço/texto (DIBOA, SPAZIO, ARC, ZANDO, UU'HULL, BHAVA). Para logos de selo colorido, usar versão enviada pelo patrocinador em negativo, ou mostrar em cor sobre cartão claro.
3. Logos de traço fino (POUSO ABARÉ, UU'HULL) ficam finos demais em tamanho pequeno.
4. Não testei `object.align`/`object.distribute` (usei coordenada calculada, que é determinística e dispensa os dois).
5. Não testei `recolor.apply` nos logos.

## Veredito visual
Grade e peso óptico: bom. Resultado final: NÃO é qualidade de estúdio por causa da resolução de origem e dos silhuetados; o método (caixa óptica + levels) é correto e repetível.

## O que rasteriza
Nada além das próprias imagens (nativas). Levels não gerou raster novo.
