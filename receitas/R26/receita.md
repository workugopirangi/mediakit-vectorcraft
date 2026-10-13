# R26. Mirror repeat (simetria, borda espelhada)

Status: FUNCIONA (com um cuidado de traço no eixo)

## Sequência que funcionou (R26/teste.py)
1. Desenhar só a METADE esquerda do ornamento até o eixo x=720: dois `path.create` (curvas Bezier) com traço dourado, uma `shape.star` e uma `shape.ellipse`.
2. Nos caminhos que TOCAM o eixo: `stroke.set {cap:"round", join:"round"}` (ver defeito abaixo).
3. `select.set {ids:[todos os objetos da metade]}` e `object.repeat.mirror {angle:90, offset:0}` devolve `{id}`. `angle:90` = eixo vertical; `offset:0` põe o eixo exatamente sobre a coordenada x do centro dos objetos selecionados... na prática, o eixo caiu em x=720 porque os caminhos terminam nele.

## Prova do eixo (medida)
Render a 144 ppi da faixa do ornamento (x de 400 a 1040 pt); comparar a imagem com ela mesma espelhada: diferença média 0,0001 de 255, ZERO pixels acima de 60. Espelho exato.

## Defeito achado e corrigido
Com `cap:"butt"` (padrão), os dois traços que se encontram no eixo em ângulo deixam um entalhe em V na ponta, visível a 400 ppi (foto z-1.png antes da correção). Com `cap:"round"` o encontro fecha liso. Para meio de ornamento em ponta, sempre usar cap redondo ou deixar o caminho cruzar o eixo e aparar.

## Veredito visual
Estúdio depois do cap redondo. A 100 % não se vê o entalhe, só em zoom.

## Armadilhas
- O repeat vivo mantém a metade editável; para entregar, `object.repeat.expand`.
- `offset` é a distância do eixo ao objeto: não testei valores diferentes de 0 (eixo deslocado).
