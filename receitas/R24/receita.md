# R24. Padrão por repetição de vetor puro (live repeat grid)

Status: FUNCIONA

## Sequência que funcionou (R24/teste.py)
1. Montar o ícone com `shape.ellipse` (só traço), `shape.polygon {sides:5}` e `path.create` (5 raios), pintar e agrupar: `select.set {ids}` + `object.group {}` (devolve `{id}` ou `{ids}`).
2. `select.set {ids:[grupo]}` e `object.repeat.grid {rows:6, cols:13, hSpacing:50, vSpacing:24}` devolve `{id}` do repeat vivo (o grupo original vira a instância de canto).
3. `object.repeat.options {gridType:"brickByRow", flipRows:true}` (valores aceitos: grid, brick, hex, brickByRow; `hexagonal`, `staggered`, `offset` dão erro).
4. `select.set {ids:[repeat]}` e `object.repeat.expand {}` devolve `{ids}` do grupo de instâncias.

## Provas
- Visual: grade regular, linhas alternadas deslocadas (tijolo). Com ícone simétrico o `flipRows` não é visível; para provar espelhamento seria preciso um ícone assimétrico (não testado).
- Expansão sem duplicata: teste de carga com elipse 30x50 = 1.500 instâncias deu 3.002 nós (1.500 grupos + 1.500 caminhos + camada e grupo), nenhum nó a mais. O objeto original não fica por baixo.
- Peso e tempo (medidos): 1.500 instâncias, repeat + expand em < 0,01 s, exportPdf em 0,02 s, PDF de 27 KB. A grade de 78 ícones da página de teste deu PDF de 295 KB, quase tudo a foto de fundo.
- `pdffonts`: só Helvetica Neue (títulos). Ícones são vetor.

## Veredito visual
Estúdio para rodapé e fundo técnico. A página de teste usa uma foto de patrocinadores bem agitada atrás do título (escolha ruim minha); o ícone bola-vetor sozinho está limpo.

## Armadilhas
- O risco do plano ("milhares de instâncias pesam") NÃO se confirmou nesta escala (1.500). Não testei 10 mil.
- A grade nasce a partir do canto do original: planejar a posição do objeto base, não a da grade.
- Um retângulo opaco sobre a grade esconde parte dela, mas o texto por cima precisa de fundo (usei preto) para ter contraste.
