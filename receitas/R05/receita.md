# R05. Foto com fade por opacity mask

Status: FUNCIONA

## Sequência (R05/teste.py)
1. `file.place {link:false}` + `object.setBounds {reference:0}` da foto.
2. `shape.rectangle` da mesma área do fade, depois `select.set {ids:[ret]}` + `paint.setFill {gradient:{kind:"linear", angle:0, stops:[{offset:0,color:"#000000"},{offset:0.55,color:"#FFFFFF"},{offset:1,color:"#FFFFFF"}]}}` (preto = transparente, branco = opaco). O retângulo é criado depois da foto, então já fica no topo.
3. `select.set {ids:[foto, ret]}` + `transparency.makeOpacityMask {clip:true}` (o objeto do topo vira máscara; sem erro, devolve ids).
4. Fundo da marca (#0F3550) atrás; texto por cima.

## Aparência
Transição suave: amostrei pixels a 200 dpi na borda do fade e não há degrau (variação de 1 nível de cor). A foto "derrete" no azul sem emenda. Qualidade de estúdio.

## Defeitos e cuidados
- No PDF sai como soft mask (`/SMask`, 1 ocorrência), foto continua JPEG original a 84 ppi efetivos (1672 px em 1440 pt; limite da foto). Nada rasterizado pelo VectorCraft.
- Não testei em PDF/X-1a e X-3 (que achatam transparência); só no export padrão e no poppler.
- A foto estende além da página à direita (sangra); sem problema no PDF.
