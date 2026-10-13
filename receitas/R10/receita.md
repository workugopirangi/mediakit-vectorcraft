# R10. Borda irregular (papel rasgado / recorte à mão)

Status: FUNCIONA (com ressalva de estilo: borda ondulada orgânica, não fibra de papel rasgado)

## Sequência (R10/teste.py)
Para cada foto, três retângulos com o efeito de aspereza, o do meio é a máscara:
1. Sombra: `shape.rectangle` maior (+22/+18) preto, `effect.apply {effect:"distort.roughen", params:{size:3, relative:false, detail:7, points:"smooth", seed:S+50}}`, `transparency.set {opacity:22}`, `object.move {dx:10, dy:12}`.
2. Papel branco: retângulo maior (+16/+14), roughen `{size:6, detail:9, points:"smooth", seed:S+20}`.
3. Máscara: retângulo do tamanho da foto, roughen `{size:4, detail:7, points:"smooth", seed:S}`, depois `select.set {ids:[m]}` + `object.expand {object:true}` (o efeito vivo vira caminho real).
4. `file.place {link:false}` + `object.setBounds`, `object.arrange.bringToFront` na máscara, `select.set {ids:[foto, m]}` + `object.clippingMask.make {}`.
`distort.roughen` é vetor (catálogo diz `raster:false`), por isso nada rasteriza. Seeds diferentes dão bordas diferentes em cada cartão.

## Aparência
Primeira tentativa com `points:"corner"` (size 7, detail 18): bordas em dentes de serra pretos e brancos, aspecto de selo postal, feio e carregado. Descartei. A versão final com `points:"smooth"` dá bordas onduladas e orgânicas, tipo recorte à mão/polaroid; limpa a 150 dpi. Não parece papel rasgado com fibra (isso exigiria textura), mas é adequado para depoimentos e bastidores.

## Defeitos e cuidados
- A borda da foto em si fica quase reta (aspereza 4 pt); quem dá a impressão de rasgo é a borda do papel branco atrás.
- Foto precisa cobrir a máscara inteira (errei uma altura na 1ª rodada e apareceu faixa de papel).
- `object.expand` funcionou e deixou caminho limpo; PDF com 3 JPEGs originais (173 a 184 ppi), 0,9 MB.
