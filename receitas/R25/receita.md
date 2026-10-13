# R25. Radial repeat (rosa dos ventos, mandala, raios)

Status: FUNCIONA

## Sequência que funcionou (R25/teste.py)
1. Raio: `shape.rectangle {x:cx-3, y:cy-380, width:6, height:240}` pintado (sem traço), posicionado com a PONTA EXTERNA a 380 pt do centro.
2. `select.set {ids:[raio]}` e `object.repeat.radial {instances:24, radius:380}` devolve `{id}`.
3. `object.repeat.options {center:[cx,cy], instances:24, radius:380}` (devolve null, é normal).
4. (opcional) `object.repeat.expand {}` para virar grupo editável.
5. Leque parcial: `object.repeat.options {startAngle:-90, endAngle:90, instances:13}` (testado: 13 raios em 180 graus, passo de 15 graus, leque limpo).

## Semântica do `radius` (descoberta)
`radius` é a distância do CENTRO até a borda de cima do objeto original (o objeto fica de fora do círculo). Sem `radius`/`center`, o padrão põe o centro uns 408 pt abaixo do topo do objeto e o resultado sai fora de lugar. Com `radius: 0` (minha primeira tentativa) NÃO aparece raio nenhum no PDF. Sempre passar `center` e `radius`.

## Prova de ângulo e fechamento (medida)
Render a 144 ppi, recorte circular excluindo o miolo (tem texto): girar a imagem em torno do centro e comparar.
- 15, 30, 45 graus: diferença média 0,11 a 0,12 de 255, zero pixels acima de 80.
- 7,5 e 12 graus (ângulos errados): diferença média 6,1, 40 mil pixels acima de 80.
Conclusão: simetria exata de 360/24 = 15 graus, sem lacuna no fechamento.

## Veredito visual
Estúdio. Raios nítidos e uniformes, vetor puro (PDF de 848 KB só por causa da foto do painel). Fontes: Helvetica Neue Condensed Black embutida.

## Armadilhas
- Os raios vazam da caixa: pôr a foto/painel por cima, ou recortar com `object.clippingMask.make`.
- `reverseOverlap` não testado (raios não se sobrepõem aqui).
