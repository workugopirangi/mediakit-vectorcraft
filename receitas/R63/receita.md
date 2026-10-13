# R63. Cor de marca em RGB para tela e CMYK para impressão

Status: PARCIAL (os comandos funcionam; o número de deltaE que o motor devolve NÃO bate com a diferença medida no PDF, e o preto da AME vira preto rico perigoso)

## Comandos que funcionaram
- `color.convert {color:"#F5D80A", to:"cmyk", intent?}` devolve `{values:[c,m,y,k] (0..1), hex, lab, outOfGamut, deltaE}`.
- `color.convert {color:{c:4,m:10,y:96,k:0}, to:"rgb"}` volta (testado: dá #ffdc03).
- `swatch.new {name, color:"#F5D80A", mode:"cmyk"}` cria o swatch já convertido; `paint.setFill {swatch}` aplica.
- `file.documentColorMode {mode:"cmyk", convert:true}` converte o documento inteiro (2 objetos: `changed:2`); repetir com `grays:"black"` não mudou nada porque as cores já estavam convertidas.

## Resultado (perfil: "VectorCraft Generic CMYK (SWOP-like)", intenção relativa)
| Cor | RGB | CMYK (%) | outOfGamut | deltaE do motor | dE76 medido no PDF* |
|---|---|---|---|---|---|
| AME amarelo | #F5D80A | 8,3 / 9,3 / 93,7 / 0 | não | 0,0 | 6,1 |
| AME preto | #0B0B0C | 56,8 / 50,6 / 49,0 / 95 | SIM | 4,1 | 2,7 |
| Sprint ouro | #D4A64A | 14,7 / 29,1 / 73,4 / 5,2 | não | 0,0 | 2,9 |
| Sprint creme | #F3E3B5 | 6,7 / 7,4 / 30,4 / 0 | não | 0,0 | 5,2 |
| Sprint mar | #0F3550 | 91,6 / 62,6 / 34,6 / 40,5 | SIM | 2,2 | 3,6 |
| Sprint menta | #9FE3D0 | 40,2 / 0 / 30,7 / 0 | SIM | 6,6 | 10,2 |
| Sprint coral | #E9603A | 2,7 / 70,5 / 75,1 / 0 | não | 0,0 | 6,3 |
*Medido por mim: renderizei o PDF (poppler, 50 ppi) com a cor RGB à esquerda e o swatch CMYK à direita e comparei os pixels em CIE76 (aproximação com sRGB/D65; serve como ordem de grandeza, não como medição colorimétrica).

## Achados (adversariais)
1. O deltaE do motor é ~0 para toda cor "dentro da gama", mas a conferência real de ida e volta mostrou mudança visível: o amarelo da AME saiu (233,217,24) no lugar de (245,216,10), dE76 ~6. A conversão de documento (`documentColorMode`) também deu #F5D81D (blue 0x0A para 0x1D). Ou seja, o dE "0" do motor mede outra coisa (provavelmente o aperto de gama, não o ciclo completo). Não confiar nele como aceite do critério "dE abaixo de 6".
2. `intent` muda MUITO o amarelo e o deltaE não acusa: relativa dá Y 93,7%; perceptual dá Y 60,9%; saturation 63,7%; absoluta M 4,9% Y 90,2% K 0. O deltaE reportado é o mesmo (8,9e-5) nas quatro. O padrão (relativa) é o que preserva o amarelo vivo; não usar perceptual para cor de marca.
3. Preto da AME (#0B0B0C) vira um CMYK "preto rico" 57/51/49/95 = cobertura total de tinta de 251% (soma dos quatro canais: 0,568+0,506+0,490+0,95), abaixo do teto comum de 300%, mas texto fino em quatro tintas desregistra na impressora. Para texto e filetes usar K=100 (C0 M0 Y0 K100) ou um preto rico definido por swatch, nunca a conversão automática.
4. Menta do Sprint (#9FE3D0) fica fora da gama e dE76 ~10: será visivelmente mais apagada no impresso. Mar (#0F3550) fora da gama mas perto (dE 2,2 a 3,6). Aviso de fora de gama (`outOfGamut:true`) existe e funciona como sinal.
5. O perfil é genérico "SWOP-like"; não há FOGRA nem perfil da gráfica. O dE contra o perfil real da gráfica pode ser outro. Não testei carregar perfil externo.

## Veredito
Dá para converter, gerar swatches CMYK e saber quais cores saem da gama. Não dá para aprovar cor de marca só pelo `deltaE` devolvido; fechar com prova de impressão ou medição com o perfil da gráfica. Recomendação: definir à mão o CMYK da marca (AME amarelo: algo como C4 M10 Y96 K0, a confirmar com a gráfica), guardar como swatch global spot ou CMYK fixo.

## O que rasteriza
Nada.
