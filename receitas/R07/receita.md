# R07. Recorte (cutout) com contorno de adesivo e sombra dura

Status: FUNCIONA

## Sequência (R07/teste.py)
1. `file.place {path:"real-atleta-recorte.png", link:false}` + `object.setBounds {x,y,width,height,reference:0}` (cópia A, só para a silhueta).
2. `imageTrace.make {id:A, params:{mode:"blackAndWhite", threshold:254, ignoreWhite:true, noise:20}}` (o trace lê o ALFA: tudo que não é transparente vira preto; com threshold 128 só saíam as partes escuras do atleta, 60 caminhos). Devolve {id, paths, anchors}.
3. `imageTrace.expand {id}` devolve {ids} (descarta a imagem de origem, fica só o vetor).
4. `select.set {ids}` + `object.pathfinder.unite {}` devolve {ids} (silhueta única) e `object.path.simplify {tolerance:1.5}`.
5. Duas vezes: `select.set {ids:[sil]}` + `object.path.offsetPath {offset:12, joins:"round"}` (copias novas acima do original). Copia 1 vira o adesivo (fill branco), copia 2 vira a sombra (fill preto + `object.move {dx:16, dy:16}`).
6. `edit.clear` na silhueta original, colocar de novo a foto PNG (cópia B) com os mesmos bounds e `object.arrange.bringToFront {}`.
Sempre com `paint.setStroke {none:true}`.

## Aparência
Contorno branco uniforme de 12 pt ao redor de atleta e bola (a bola ganhou seu próprio contorno, ilha separada), sombra dura deslocada sólida, sem pontas nem picos mesmo a 200 dpi. Sensação de adesivo/estúdio. Qualidade de estúdio.

## Defeitos e cuidados
- Contorno branco some na camisa branca (inerente ao estilo).
- Fiapos de cabelo muito finos podem ficar fora da silhueta se `noise` for alto; com noise 20 saiu bom.
- No PDF o PNG vai como imagem RGB 173 ppi + soft mask (alfa preservado); o contorno e a sombra são vetor puro. Nada rasterizado pelo VectorCraft. PDF cerca de 1,3 MB.
- A cópia A usada pelo trace tem que ter os mesmos bounds da cópia B, senão o contorno desalinha.
