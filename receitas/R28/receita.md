# R28. Ornamentos geométricos: espiral, grade polar, malha retangular

Status: FUNCIONA (regra de uso: traço de 0,5 pt ou mais)

## Sequência que funcionou (R28/teste.py)
1. Fundo `shape.rectangle` azul-mar.
2. Malha fina: `shape.rectangularGrid {x:0,y:0,width:1440,height:810,rows:27,columns:48,frame:false}` e segunda malha maior `{rows:9,columns:16,frame:true}`; pintar com `select.set {ids:[grupo]}` + `paint.setFill {none:true}` + `paint.setStroke {color}` + `stroke.set {weight:0.5}` (o peso vale para todos os caminhos do grupo, conferido por `document.inspect`).
3. `shape.polarGrid {x:820,y:90,width:560,height:560,concentric:9,radial:24}` e a mesma pintura.
4. `shape.spiral {cx:280,cy:560,radius:190,decay:85,segments:12}`.
5. Painel de dados por cima (retângulo opaco + texto).

## Semântica medida
- `rows`/`columns` na malha retangular são o número de DIVISÓRIAS internas: `columns:48` em 1440 pt dá células de 1440/49 = 29,39 pt (medido no render: 29,3 pt, todas iguais). Para células de 30 pt use 47 divisórias.
- `shape.polarGrid {concentric:3, radial:24}` (inspecionado): 4 elipses (3 mais a externa) e 24 raios de 15 graus cada, sem duplicata.
- Espaçamento e peso uniformes a 150 ppi (todas as linhas com a mesma intensidade).

## Moiré e traço fino (medido em 3 leitores)
Teste com a mesma malha em 0,25, 0,5 e 1,0 pt:
- poppler (pdftoppm) e cairo (pdftocairo): os três pesos saem IDÊNTICOS em 50, 72 e 144 ppi (o leitor prende qualquer traço fino em 1 pixel de dispositivo). Não se distinguem.
- CoreGraphics (sips, mesmo motor do Preview) a 72 ppi: 0,25 e 0,5 pt IGUAIS (intensidade 54), 1,0 pt mais forte (72). O leitor da Apple também prende o traço fino.
Conclusão: 0,25 pt não existe na prática; 0,5 pt é o menor peso que vale e aparece com ~75 % da força de 1 pt em tela de 72 ppi. Para projeção ou celular, usar 0,75 a 1 pt e cor mais clara. No preview a 50 ppi da página de teste a malha mostra linhas de brilho irregular (amostragem de grade de 20 px); a 150 ppi some.

## Veredito visual
Estúdio a 100 % e 150 ppi: linhas finas e uniformes, polar e espiral limpos. A espiral a 0,5 pt em coral sobre azul-mar é quase invisível: dar mais peso ou luz.

## Armadilhas
- O texto sobre malha precisa de painel opaco (usei retângulo azul-mar com borda).
- Duas malhas sobrepostas de passos diferentes criam linhas quase coincidentes (parecem linha dupla). Alinhar os passos (múltiplos) para evitar.
- Tudo é vetor, PDF de 216 KB.
