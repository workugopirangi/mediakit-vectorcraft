# R39. Envelope por malha, distorção livre e perspectiva

Status: FUNCIONA (com cuidado de uso)

## Comandos que funcionaram
```
object.distort {ids:[id], corners:[[TLx,TLy],[TRx,TRy],[BRx,BRy],[BLx,BLy]]}   # texto e imagem
object.envelope.makeWithMesh {ids:[id], rows:3, cols:4} -> {id: envId}
document.inspect {depth:3}  -> achar bounds do envId (x,y,width,height)
object.envelope.setMeshPoint {id:envId, index:rw*(cols+1)+cl, x, y}   # em coordenadas do documento
```
Índice dos pontos: ordem por linha, (cols+1) pontos por linha (confirmado: mexer no índice 1*5+2 deslocou o ponto interno esperado).

## Veredito
- `object.distort` em título "COPA AME" (Condensed Black, texto vivo antes): trapézio limpo, curvas lisas, sem dobras. Bom para título deitado/perspectiva.
- `object.distort` em foto: funciona, borda reta limpa. A imagem continua sendo o JPEG original (1936x1081 px, 326 x 277 ppi efetivos na página, 190 KB), sem reamostrar.
- Envelope por malha 3x4 em "2026" com 5 pontos movidos: deformação orgânica suave, vetor, sem dobras com deslocamentos de ~15 a 40 pt em corpo 170. Qualidade de estúdio para distorção leve.
- Fontes: o texto distorcido virou contorno (pdffonts só lista fontes dos textos não deformados).

## Defeitos e armadilhas
- Meu primeiro teste moveu pontos para coordenadas absolutas longe do texto e o glifo explodiu (cruzes, fatias): nada a ver com defeito, mas deslocamento grande (maior que a altura de uma letra) dá dobras. Calcule os pontos a partir do bounds do envelope.
- Não existe comando de leitura de bounds (`object.getBounds` não existe); use `document.inspect`.
- `setMeshPoint` e `distort` retornam vazio/ids sem confirmar posição: conferir no PNG.
- A perspectiva é projetiva só em `object.distort`; o envelope de malha é local, não projetivo.
