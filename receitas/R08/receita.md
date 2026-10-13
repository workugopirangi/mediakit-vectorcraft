# R08. Textura de grão sobre blocos de cor

Status: PARCIAL (funciona e é bonito, mas pesa: 24 MB por página de fundo cheio a 300 ppi)

## Sequência (R08/teste.py; variável RES muda a resolução)
1. `document.rasterEffectsSettings {resolution:300}` ANTES de aplicar o efeito (padrão é 72 ppi: o grão sai a 72 ppi e fica borrado/pixelado; confirmei: 484x814 px, 72 ppi, 1,4 MB).
2. `shape.rectangle` do fundo + `paint.setStroke {none:true}`.
3. `select.set {ids:[ret]}` + `effect.apply {effect:"artistic.filmGrain", params:{grain:6, highlightArea:0, intensity:10}}` (grão monocromático, discreto). Alternativa `effect.apply {effect:"texture.grain", params:{intensity:40, contrast:50, grainType:"regular"}}`.
O retângulo continua sendo objeto vivo (efeito editável) no documento; só o PDF rasteriza.

## Aparência (PNG a 50 e 144 dpi)
- `artistic.filmGrain`: grão fino e neutro, parece papel/filme, qualidade de estúdio.
- `texture.grain`: ruído CROMÁTICO (pontos roxos e verdes sobre o azul) e mais pesado; parece ruído digital, não papel. Evitar em fundo de marca, ou baixar muito `intensity`.
- Sem emenda nem borda branca na junção entre blocos; a imagem efeito é um pouco maior que o retângulo (margem de 1 px), invisível.

## O que rasteriza e a quanto
Cada retângulo com efeito vira uma imagem RGB + soft mask no PDF, na resolução configurada, tamanho = área do objeto:
- 300 ppi: bloco 480x810 pt = 2017x3392 px = 6,3 MB (filmGrain) e 7,9 MB (texture.grain). Página cheia 1440x810 MEDIDA: 6017x3392 px, 23,1 MB de imagem, PDF de 24,3 MB.
- 150 ppi: bloco 480x810 = 4,1 e 2,1 MB, PDF de 6,4 MB para dois blocos (página cheia estimada, não medida, perto de 9 MB).
- 72 ppi: 0,96 MB por bloco, grão borrado.
Critério do plano (< 15 MB por fundo cheio) NÃO é atendido a 300 ppi.

## Recomendação
Para kit de e-mail/WhatsApp: `resolution:150` (grão ainda fino na tela). Para gráfica: 300 ppi só nas páginas que precisam, ou grão em PNG pequeno ladrilhado (Plano B do plano, não testado aqui). Aplicar o efeito em retângulo menor que a página reduz proporcionalmente.
