# R54. Botões, etiquetas e cantos arredondados

Status: FUNCIONA

## Comandos que funcionaram (todos vetor, sem raster)
- Pílula: `shape.rectangle {x,y,width,height,radius: height/2}`; depois `paint.setFill`, `paint.setStroke {none:true}` (ou cor + `stroke.set {weight}`).
- Cartão com raio fixo: `shape.rectangle {radius:36}`; raio é igual nos 4 cantos.
- Raio só em alguns cantos: `object.setLiveShape {ids:[id], radius:48, corners:[0,2]}` (0 topo-esquerdo, 1 topo-direito, 2 baixo-direito, 3 baixo-esquerdo). Para o raio entrar o retângulo precisa ter nascido com `radius` pequeno (usei 1); em retângulo sem raio nenhum não testei.
- Cantos chanfrados e "ingresso" (côncavos): `object.setLiveShape {radius:40, kind:"chamfer"}` e `kind:"invertedRound"`.
- Efeito vivo: `effect.apply {effect:"stylize.roundCorners", params:{radius:30}}` em retângulo reto; sai como vetor, canto limpo. Preferir `shape.rectangle radius`, que é geometria real e editável; o efeito deixa o retângulo reto por baixo.
- Ajuste posterior: `object.setLiveShape {radius:100}` em retângulo com traço de 8 pt manteve o traço contínuo, sem corte.

## Prova
- teste.pdf, 14 KB, sem imagens, fontes embutidas (HelveticaNeue CondensedBlack e Bold). Conferi cantos em zoom de 120 ppi: raio uniforme e traço inteiro.

## Gotchas
- `object.setLiveShape` retorna null (sucesso sem payload).
- Texto não centraliza sozinho na pílula: calcular baseline manualmente (y + h/2 + ~size*0.35). Usei +8 para corpo 22 e ficou centrado óptico.
- Pílula só com traço (vazada): `paint.setFill {none:true}` e stroke 2 pt; ok.
- Raio de pílula = metade da altura; se passar disso o motor limita sozinho.

## Veredito visual
Qualidade de estúdio. Raio consistente, bordas nítidas, sem artefato.

## O que rasteriza
Nada.
