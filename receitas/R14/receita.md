# R14. Colunas e quadros de texto

Status: FUNCIONA (colunas num quadro só; encadeamento entre quadros `text.thread.create` não testado)

## Sequência (R14/teste.py)
1. `text.create {x, y, text, font:"Source Sans 3", style:"Regular", size:15, color, area:{width:860, height:255, fit:"none"}}` (retorna {id}; texto longo com \n entre parágrafos).
2. `text.setStyle {ids, leading:22}`.
3. `select.set {ids:[t]}` + `text.setFormat {spaceAfter:8}` (espaço entre parágrafos; devolve {ids}).
4. `text.areaOptions {ids:[t], columns:3, gutter:28, inset:0, verticalAlign:"top"}` devolve as opções com `overflow` (booleano) e `fitScale`.
5. Checar `overflow:false` na resposta. É o critério de falha do plano.

## Resultado
Texto flui da coluna 1 para a 2 e a 3 sem perda, calha de 28 pt respeitada, espaçamento entre parágrafos aplicado. Com `height:215` a resposta trouxe `overflow:true` e as últimas linhas sumiram do PDF (provado: a última frase "uma feira de saúde..." desapareceu); com `height:255` saiu `overflow:false` e o texto inteiro apareceu. Ou seja, a detecção de estouro é confiável e deve ser checada em toda caixa.

## Defeitos e cuidados
- Colunas enchem uma de cada vez até a altura do quadro (sem balanceamento): ajuste `height` até as colunas ficarem parecidas; a 3ª sai mais curta (aceitável).
- Sem controle de viúva/órfã nem hifenização (limites conhecidos do plano): uma coluna começa com "todo o fim de semana" sem problema, mas pode surgir linha solta.
- Fonte Source Sans 3 embutida; nada rasteriza; PDF de 160 KB.
