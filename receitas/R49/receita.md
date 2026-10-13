# R49. Donut e medidores (progress ring)

Status: FUNCIONA

## Comandos que funcionaram (técnica recomendada)
Trilho: `shape.ellipse` (cx, cy, r) com `paint.setFill {none:true}` + `paint.setStroke {color:"#1d5578"}` + `stroke.set {weight:34}`.
Arco de progresso: `path.create {d:"M cx cy-r A r r 0 <large> 1 x2 y2"}` com x2 = cx + r sin(a), y2 = cy - r cos(a), a = 2 pi pct / 100, large = 1 se pct > 50; depois `paint.setStroke {color}` + `stroke.set {weight:34, cap:"round"}`. Começa no topo, sentido horário, ângulo exato (3 anéis testados: 52%, 53%, 42%).
Número central: `text.create` Helvetica Neue Condensed Black 64 pt, branco.

## Veredito
Qualidade de estúdio: anéis grossos com ponta redonda lisa, vetor puro (0 imagens). Zoom a 220 ppi sem falha.

## Defeitos e armadilhas
- CAP ROUND ALONGA O ARCO: a ponta redonda avança meia espessura (w/2) além do ponto final e antes do inicial, então 52% parece uns 60%. Para ser fiel ao número, encurtar o arco: usar ângulo efetivo menor, subtraindo w/(2r) rad em cada ponta (nos 3 anéis testados eu NÃO compensei, o erro visual é da ordem de 6 a 7 pontos percentuais com w=34 e r=130). Para anel exato use cap butt, ou compense.
- `object.path.outlineStroke` converte o arco em forma preenchida e funcionou ({ids}); útil para aplicar gradiente no anel ou pathfinder.
- Técnica B (elipse com `dash [c*pct, c]`): `stroke.set` aceitou e desenhou, mas o ponto de partida do dash numa elipse NÃO é o topo e o arco sai rotacionado (a legenda que escrevi no teste dizendo "arranca à direita (3h)" está errada: o arco ficou de 9h para 3h passando pelo topo). Como não há comando fácil de rotação do início, prefira a técnica do path com arco SVG.
- Legenda do teste C colidiu com o texto (layout meu).
