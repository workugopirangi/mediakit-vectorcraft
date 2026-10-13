# R53. Extrusão 3D em título

Status: PARCIAL (funciona e sai em vetor, mas só com receita específica e a cor da face muda)

## Comandos que funcionaram
1. `text.create` e `select.set {ids:[texto]}`.
2. `type.createOutlines {}` (texto vira grupo de traçados compostos, um por letra).
3. `object.ungroup {}` (retorna null, mas deixa as letras selecionadas) e em seguida `object.pathfinder.unite {}` sem `select.set` no meio. Retorna `{ids:[N]}`, um único traçado composto com todas as letras.
4. `select.set {ids:[N]}` e `effect.apply {effect:"threeD.extrude", params:{depth:30, rotationX:-6, rotationY:-12, rotationZ:0, perspective:0, shade:true, ambient:45, lightIntensity:70}}`.
5. Exportar normal. Não precisa de `object.expand`.

## Provar
- teste.pdf tem 14 KB, nenhuma imagem (`pdfimages -list` vazio): a extrusão sai como vetor puro, sem rasterizar. O texto vira contorno, então `pdffonts` fica vazio (perde seleção e busca do texto).

## Defeitos e gotchas
1. `effect.apply threeD.extrude` direto em texto falha: "requires a path or compound path". Tem que outlinar primeiro.
2. Em grupo (resultado do outline) com `target:"contents"` aplica, mas cada letra recebe a sua própria rotação 3D e a palavra desmonta (dígitos "2027" ficaram desalinhados). Por isso unir as letras antes (passo 3).
3. Com `shade:true` a face frontal é escurecida pela luz: coral #E9603A saiu marrom-avermelhado (~#C05030). A cor de marca NÃO se preserva. Branco saiu cinza. Ajustar `ambient` mais alto ajuda um pouco, não resolve.
4. Com `shade:false` não há contraste entre face e lateral (tudo na mesma cor), então a lateral vira mancha. Texto preto sem sombreamento fica uma massa.
5. Sem rotação (0,0,0) a extrusão fica atrás da face e não aparece.
6. Rotações fortes (rotationY 25 e rotationX -15, depth 70) deram artefato visível (dobra tipo "papel enrolado" dentro do "0") e deformação das letras. Só valem rotações leves e depth baixo.
7. Paleta: face não aceita cor própria separada da lateral; a lateral é a mesma cor escurecida.

## Veredito visual
Com rotação leve e depth 30 o resultado é aceitável para um título de capa em estilo "bloco", mas a cor da face muda. Não é qualidade de estúdio sem retoque. Recomendo para um título isolado, não como padrão. Plano B para cor exata de marca: empilhar cópias do contorno deslocadas (`object.transform {copy:true}`) em tom mais escuro e a face na cor exata por cima, 100% vetor.

## O que rasteriza
Nada. Extrusão vetorial.
