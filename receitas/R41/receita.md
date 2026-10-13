# R41. Offset path e efeito adesivo (sticker)

Status: FUNCIONA (com defeito de fendas finas que exige ajuste do offset)

## Comandos que funcionaram
```
text.create {...}                      -> id
select.set {ids:[id]}
type.createOutlines {}                 -> {ids:[grupo]}
select.set {ids:[grupo]}
object.pathfinder.unite {}             -> {ids:[unido]}
select.set {ids:[unido]}
object.path.offsetPath {offset:14, joins:"round"}   -> {ids:[novo]}   (SEM param ids)
paint.setFill / paint.setStroke (cor do adesivo, contorno)  no objeto novo
select.set {ids:[unido]} + object.arrange.bringToFront {}   (o offset nasce ACIMA do original, tampa o texto)
```

## Veredito
Efeito adesivo de estúdio: contorno uniforme, cantos arredondados com `joins:"round"` e pontas vivas com `miter`, vetor puro (offset vira path, 0 imagens). "COPA AME" 170 pt com offset 22 round ficou limpo; "SPRINT 2027" com miter 10 pt também.

## Defeitos e armadilhas
- `object.path.offsetPath` NÃO aceita `ids`: opera na seleção atual (erro "unknown parameter ids"). Sempre `select.set` antes.
- O contorno novo fica por cima do original e esconde o texto; trazer o original para a frente com `object.arrange.bringToFront`.
- FENDAS: com offset 14 o vão da letra C ficou como uma fenda preta fina (o traço de 2 pt mostra a fresta), e entre letras próximas (P e A) a cunha também sobra. Com offset 22 a abertura do C fechou, mas a cunha embaixo do P/A ficou. Regra: offset deve ser maior que metade do menor vão; contornar fendas restantes unindo um retângulo de reforço (não testei) ou aumentar o tracking antes.
- Sem `unite` antes (caso do "500"), o offset foi aplicado ao grupo de glifos e cada letra ganhou seu próprio contorno, com sobreposição entre letras: sempre unir antes.
- IDs de glifo pulam muito (um texto de 8 letras consumiu ~30 ids), sem consequência.
