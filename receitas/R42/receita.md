# R42. Pathfinder para blocos geométricos

Status: PARCIAL (booleanas funcionam; crop com foto falha; fendas finas entre peças vizinhas)

## Comandos que funcionaram
```
select.set {ids:[a,b,c]}  (ordem de pintura, de trás para frente)
object.pathfinder.divide {}      -> {ids:[grupo]}   (divide devolve UM grupo com as fatias)
object.ungroup {}                (as fatias passam a ser objetos soltos; os ids são os mesmos dos filhos do grupo, não nascem ids novos)
object.pathfinder.minusFront {} | intersect {} | exclude {}   -> {ids}
```
Testado: divide de 2 círculos + retângulo (7 fatias), divide de 8 paralelogramos adjacentes (8 fatias), minusFront (quadrado menos círculo), intersect (lente), exclude.

## Veredito
- Booleanas corretas e vetoriais, geometria exata, sem fatias duplicadas, fills mantidos. Para pintar fatias por cor: depois de `divide` fazer `object.ungroup` e achar os ids pelo `document.inspect {depth:6}` (filhos kind "Path"); pintar o grupo inteiro pinta todas igual (foi o erro do meu 1º teste: tudo coral com fios).
- FENDAS: em fatias vizinhas de cores diferentes sobre fundo preto aparece fio fino escuro na emenda (antialiasing, conflation artifact) em pdftoppm (muito sutil, a 300 ppi só a linha branca/creme ficou visível) e em sips (macOS, fio visível ampliando 4x em todas as emendas). Em tela de 100% quase não se vê; em fundo escuro com fatias claras é perceptível. Mitigação (não testada): duplicar o bloco unido atrás das fatias com a cor média, ou sobrepor 0,25 pt de traço da mesma cor.
- `object.pathfinder.crop` com foto + losango: ERRO "Crop produced an empty result" (crop não aceita imagem raster como alvo). Para foto em losango use `object.clippingMask.make` (provado em kits anteriores).

## Gotchas
- Ids retornados por `divide` são do grupo, não das fatias.
- Divide dos paralelogramos adjacentes sem recolorir (todos coral) mostrou as emendas como linhas finas, ou seja, as fatias não são fundidas.
- Nenhuma imagem criada (só a foto de teste, 287 ppi).
