# R21. Selo circular com texto em volta (carimbo)

Status: FUNCIONA (com um desvio do plano: o texto de baixo NÃO usa `flip`)

## Sequência que funcionou (R21/teste.py)
1. Fundo: foto (`file.place` + máscara) + retângulo azul-mar a 45 %.
2. Anéis: `shape.ellipse` r=185 (fill azul-mar, traço dourado 4 pt), r=172 (traço 1,2 pt), r=108 (traço 1,2 pt). Pintar com `select.set` + `paint.setFill`/`paint.setStroke`.
3. Texto de cima: caminho circular em SVG com ponto de partida às 9 horas e sentido horário:
   `path.create {d:"M863,405 A137,137 0 1 1 1137,405 A137,137 0 1 1 863,405 Z"}`
   `text.createInPath {path, mode:"onPath", text:"EDIÇÃO 2027 · OFICIAL", size:30, font:"Helvetica Neue", style:"Condensed Black", color}`
4. Texto de baixo: caminho circular de raio maior (158) em sentido ANTI-HORÁRIO (flag de varredura 0): `A158,158 0 1 0 ...`. O texto fica em pé na parte de baixo, com as letras voltadas para dentro do selo.
5. Centralizar cada texto: medir a largura (texto temporário + `document.inspect` bounds.width, mais `n_letras * spacing`), e `type.pathOptions {start: 0.25 - (largura/2)/(2*pi*r), spacing:3, alignToPath:"baseline"}`. O 0,25 é o meio de cima (e o de baixo, no caminho anti-horário que também parte das 9 h).
6. Estrela central: `shape.star {cx,cy,radius1:70,radius2:30,points:5}` pintada de ouro.
7. Girar o selo todo: `select.set` nos 6 ids e `object.rotate {angle:-12}` (gira texto em caminho junto, sem problema).

## Veredito visual
Estúdio. Zoom a 170 ppi: texto nítido, vetorial, fechamento do círculo sem emenda, espaçamento regular, texto de baixo legível (não de cabeça para baixo), anéis concêntricos limpos. A estrela é shape (não glifo), então não depende de fonte (ver R19).

## Armadilhas
- `type.pathOptions {flip:true}` lê de volta `flip:false` sempre. Em linha reta o render mostra o texto de cabeça para baixo e alinhado pelo fim do caminho (funciona, mas é outra coisa). Em círculo fechado não tive efeito visível. NÃO usar flip no selo; usar caminho anti-horário.
- Texto de cima tem a base no caminho e cresce para fora; o de baixo, com caminho anti-horário, cresce para dentro. Por isso o raio do de baixo (158) é maior que o do de cima (137): os dois ocupam a mesma faixa (137 a 160).
- Centralização é calculada, não automática. Erro de largura = texto torto no eixo.
- Usar "·" (ponto médio) e não "★" no texto: estrela em Helvetica Neue Condensed Black cai em fonte reserva (R19).

## O que rasteriza
Só a foto de fundo (JPEG). Selo, texto e anéis são vetor.
