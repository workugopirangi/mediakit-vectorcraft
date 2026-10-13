# R66. Pessoa saindo do quadro

Status: FUNCIONA

## Receita
1. Fundo de cor: `shape.rectangle` amarelo 1440x810.
2. Quadro com foto: `file.place` da foto, `shape.rectangle` do tamanho do quadro (330,250,780x480), `select.set {ids:[foto, retangulo]}`, `object.clippingMask.make`. Escurecer com retângulo preto `transparency.set {opacity:35}` e borda: retângulo sem preenchimento `paint.setStroke {color:"#0B0B0C"}` + `stroke.set {weight:8}`.
3. Pessoa: `file.place {path:"real-atleta-recorte.png"}` e `object.setBounds {x:560, y:110, width:640, height:800, reference:0}`. Ela é maior que o quadro (cabeça em y=125, borda de cima do quadro em y=250).
4. Sombra na pessoa ANTES de recortar: `effect.apply {effect:"stylize.dropShadow", params:{blur:18, x:-10, y:8, opacity:55, color:"#000000", mode:"multiply"}}`.
5. Máscara em forma de L/T: dois retângulos pretos, A = o quadro (330,250,780,480) e B = a faixa inteira acima da borda de cima (0,0,1440,250); `select.set {ids:[A,B]}` e `object.pathfinder.unite {}` (retorna `{ids:[N]}`); depois `select.set {ids:[pessoa, N]}` e `object.clippingMask.make {}`. Resultado: a pessoa aparece inteira acima da borda e só dentro do quadro abaixo dela, então a cabeça "vaza" e as pernas ficam contidas.
6. Texto por último. Export normal.

## Prova
- teste.pdf 2,1 MB: foto do quadro JPEG 176 ppi nativo; pessoa PNG com smask a 162 ppi; sombra 2992x3659 a 300 ppi. Fontes embutidas.
- Zoom a 100 ppi: a cabeça cobre a borda preta do quadro com recorte limpo; abaixo da borda de baixo nada vaza.

## Defeitos e gotchas (honestos)
1. Primeira tentativa: sombra aplicada ao grupo já recortado. Resultado ruim: a sombra rasterizou 6325x3367 px (a caixa do grupo inclui a faixa gigante B) e ficou um borrão amarelado do pé abaixo da borda do quadro. Corrigido aplicando a sombra à imagem ANTES do `clippingMask.make`; a máscara então corta a sombra também.
2. Consequência: abaixo da borda de baixo o recorte (e a sombra) é cortado; acima da borda de cima a sombra cai no amarelo (lido como sombra na parede). Se quiser a sombra completa sobre o amarelo, precisaria de uma segunda cópia: não testei.
3. Para vazar também pela lateral é preciso acrescentar outro retângulo à união (ex.: faixa à direita do quadro); só testei o vazamento por cima.
4. A foto do quadro tem gente em primeiro plano (cena de premiação) que compete com o atleta recortado. Em produção usar foto de fundo mais limpa ou bloco de cor.
5. A franja clara do recorte (ver R65) também aparece aqui, contra fundo escuro.

## Veredito visual
Efeito de estúdio, bem convincente com o recorte fornecido. A máscara vetorial (união de retângulos) é exata e leve; o custo está só na sombra raster.

## O que rasteriza
Sombra da pessoa: 300 ppi. Foto e recorte: nativos. Máscara, borda, texto: vetor.
