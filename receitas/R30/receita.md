# R30. Halftone CMYK colorido

Status: FUNCIONA (pesado: use na área que precisa, não na página inteira)

## Sequência que funcionou (R30/teste.py)
1. `file.place` + `object.setBounds {reference:0}` da foto (real-equipe-sub.jpg, 1600x1068) em caixa 620 x 413 pt, ao lado de uma cópia original para comparar.
2. `select.set {ids:[foto]}`
3. `object.vectorHalftone {shape:"circle", frequency:25, angle:45, mode:"cmyk", clip:true}` devolve `{id, dots}`. A foto sai de cena e entra um grupo.
4. Fundo BRANCO obrigatório (cada tela multiplica; sobre fundo escuro some).

## O que sai (inspeção do documento e do PDF)
- Grupo com 4 caminhos, um por tela, cada um com blend `Multiply`: K `#343334`, C `#00a5f1`, M `#eb0b88`, Y `#fff300`. O PDF grava `/BM /Multiply` (confirmado no arquivo).
- Pontos: 125.077 a 25 lpi em 620x413 pt. Comando 0,92 s.
- Peso: PDF de 11,8 MB (os 125 mil pontos mais uma foto original de 531 KB usada na comparação). Página inteira 1440x810 a 12 lpi: 130.545 pontos, comando 0,9 s, export 5,2 s, PDF de 11,9 MB. A 18 lpi na página inteira o comando RECUSA: "too many dots for this size: lower the frequency". Ou seja, existe um teto de pontos (entre ~130 mil e o que 18 lpi pede).
- Nenhuma imagem raster no halftone (só a cópia original ao lado).

## Rosetas
Zoom a 400 ppi: quatro telas visíveis, rosetas clássicas, sobreposições multiplicando (vermelho, verde e azul nos cruzamentos), sem lacuna branca anormal; o preto (K) é pesado e cobre bastante. Os ângulos de tela seguem a documentação do comando (preto no ângulo pedido, ciano a -30, magenta a +30 e amarelo a -45 a partir dele); NÃO medi os ângulos por transformada, só conferi o padrão de roseta a olho.

## Leitores (risco do plano: multiply no PDF)
poppler e cairo a 400 ppi: diferença média 3,6/255 (só suavização); o multiply é interpretado igual. Preview/Acrobat não testados.

## Veredito visual
Estúdio como efeito "pop"; a imagem fica um pouco mais escura e menos saturada que a foto (limite de quadricromia simulada em RGB). A 100 % no 1440x810 a foto continua reconhecível com os dots visíveis a olho nu a 25 lpi (granulado, é o efeito).

## Armadilhas
- Só em fundo branco ou claro.
- Peso: 12 MB por página cheia; 10 páginas assim passam de 100 MB. Usar em divisória única.
- Se a frequência pedir pontos demais o comando falha sozinho (bom: não trava).
