# R33. Mosaico de quadrados a partir de uma foto

Status: FUNCIONA

## Sequência que funcionou (R33/teste.py)
1. `file.place {path, link:false}` + `object.setBounds {reference:0}` da foto (f10.jpg, 959x1280) em 520 x 694 pt.
2. `select.set {ids:[foto]}`
3. `object.createObjectMosaic {columns:40, rows:53, spacingX:2, spacingY:2, width:520, height:694}` devolve `{id, tiles:2120}` em 0,03 s. A foto é substituída por um grupo de retângulos; manter `rows` proporcional à foto (53 = 40 x 1280/959) para o quadrado sair quadrado.

## Provas medidas (R33, script de conferência)
- 2.120 tiles = 40 x 53, passo de 13,0 pt em x e 13,1 pt em y; cada tile tem 11 x 11,095 pt (13 menos os 2 pt de espaço). Grade alinhada, ocupa de x=61 a 579 e y=111 a 803 (margem de 1 pt, que é meio espaçamento).
- Cor: comparei o preenchimento de cada tile com a média da região correspondente da foto (calculada em Python): erro máximo por canal, média 4,2 de 255, percentil 95 14,5, máximo 31. A diferença vem do meu arredondamento das fronteiras da região e do corte de 1 pt, não de cor errada; as cores batem.
- Emenda: com `spacingX:0, spacingY:0` sobre fundo magenta, zoom de 200 ppi: nenhum fio magenta entre os quadrados (sem costura de antialiasing). Dá para usar mosaico sem espaço.
- PDF: 272 KB com o mosaico (2.120 retângulos) mais a foto original de comparação ao lado. Tudo vetor, nenhuma rasterização do mosaico.

## Veredito visual
Estúdio como ornamento (divisória, página de dados). Com 40 colunas a foto ainda é reconhecível (três corredoras, árvore), com espaço de 2 pt vira "azulejo". Sem espaço, vira pixel-art. O tom médio fica um pouco mais lavado que o original (média de cada quadrado).

## Armadilhas
- A linha de rodapé do mosaico pode ficar cortada em 1 pt se `rows` não for múltiplo exato da altura (inofensivo).
- `gray:true` e `deleteRaster:true` existem e não foram testados; o padrão já remove a foto (o objeto original sai de cena).
