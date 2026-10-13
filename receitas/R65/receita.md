# R65. Texto atrás da pessoa

Status: FUNCIONA

## Receita (a ordem de empilhamento é o truque; nenhum comando especial)
1. `file.place {path: foto de fundo, link:false}` e `object.setBounds {x:0, y:0, width:1440, reference:0, proportional:true}` (foto de fundo, camada de baixo).
2. `shape.rectangle` preto 1440x810 com `transparency.set {opacity:45}` para escurecer o fundo e o amarelo pesar.
3. `text.create {x:50, y:600, text:"COPA AME", font:"Helvetica Neue", style:"Condensed Black", size:300, color:"#F5D80A"}` + `text.setStyle {tracking:-5}`. O título gigante é texto vivo e fica ABAIXO da pessoa só por ter sido criado antes.
4. `file.place {path: real-atleta-recorte.png}` + `object.setBounds {x:640, y:30, width:640, height:800, reference:0}` (1440x1800 com alfa, razão 0,8 igual à do arquivo, sem distorção). Criado por último, fica por cima do título e por baixo do que vier depois.
5. Contato de sombra: `select.set {ids:[atleta]}` e `effect.apply {effect:"stylize.dropShadow", params:{blur:22, x:-14, y:6, opacity:55, color:"#000000", mode:"multiply"}}`. A sombra da pessoa cai sobre as letras e cola o recorte no fundo.
6. Textos finais por último. Export normal.
Conferência da ordem: `document.inspect` lista de cima para baixo (texto, atleta, título, foto). Para reordenar depois: `object.arrange.sendBackward/bringForward`.

## Prova
- teste.pdf 2,2 MB: fundo JPEG 96 ppi (1920 px em 1440 pt, limite do arquivo-fonte), atleta PNG com smask a 162 ppi (1440x1800 em 640x800), sombra 3075x3742 a 300 ppi. Fontes Condensed Black e Bold embutidas; o título continua texto selecionável.
- Preview: a pessoa cobre o meio do "M" e o "A" fica íntegro; leitura "COPA AME" preservada.

## Defeitos e gotchas
1. Tamanho do título: a 400 pt o "AME" saiu da página (cortado). 300 pt coube em 1440 com tracking -5. Medir sempre a largura antes (document.inspect dá bounds).
2. Posição da pessoa decide a legibilidade: com ela no meio do título (x=520) escondeu o "A" e o texto virou "COPA A ME". Deslocar a pessoa até cobrir só parte de uma letra grande (a barra do "M") resolveu.
3. O recorte do acervo tem leve franja clara no cabelo e no braço (visível em zoom de 110 ppi, não a 50 ppi); com o fundo escuro isso aparece como contorno. Aceitável em tela; para capa de impressão pedir recorte mais limpo ou erodir o alfa 1 px antes.
4. A sombra raster em imagem de 640x800 pt gera imagem de 3075x3742 px a 300 ppi (rasteriza também a área em volta). Custa cerca de 0,5 MB por pessoa.
5. O atleta fica a 162 ppi; para tela é nítido, para gráfica fraco.
6. Não usei o goleiro (real-goleiro-recorte.png, 1265x1265), mas o método é idêntico.

## Veredito visual
Qualidade de estúdio em tela. O efeito de profundidade é convincente com a sombra de contato; sem ela o recorte parece colado.

## O que rasteriza
Só a sombra da pessoa (300 ppi). Título e textos: vetor. Foto e recorte: nativos.
