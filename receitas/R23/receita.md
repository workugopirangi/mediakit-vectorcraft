# R23. Padrão a partir de motivo desenhado por IA (pattern swatch)

Status: PARCIAL (funciona e fica bonito, mas o PDF NÃO sai com padrão de ladrilho vetorial e há emenda de fio de cabelo em zoom extremo)

Arquivos: `teste.py` (3 painéis lado a lado: A pattern.make tijolo, B repeat.grid manual, C tile seamless), `teste_pagina.py` (página AME real, amarelo com bolas hex, sai em `pagina.pdf` e `pagina-preview.png`), `teste_trace.py` (variante vetorizada, em `v/`).

## Caminho A: object.pattern.make com o PNG (o melhor custo/benefício)
1. (recomendado) encolher o motivo antes: PNG de 1254 px para ~300 ppi do tamanho final (bola de 110 pt: 460 px). Sem isso o PDF tem 2,5 MB; com isso 362 KB.
2. `file.place {path, link:false}`, `object.setBounds {reference:0, width, height}`
3. `select.set {ids:[img]}` e `object.pattern.make {tileType:"brickByRow"|"hexByRow"|"grid", name, width:170, height:170}` (o ladrilho é maior que o motivo: sobra margem, não há emenda)
4. `object.pattern.done {}`
5. `edit.clear {ids:[img]}`: o PNG original CONTINUA na página depois do pattern.make e aparece empilhado no canto. Apagar sempre.
6. `shape.rectangle` do tamanho da área, `paint.setFill {none:true}` não serve: pintar com `select.set` + `paint.setFill {swatch:"<nome>"}`. O fill em padrão é transparente: pôr um retângulo de cor SOB ele (ou o fundo da página).
7. Opcional: `transparency.set {ids:[rect], opacity:38}` no retângulo com padrão (funcionou, deu o tom sobre tom amarelo da página AME).

## Caminho B: repetição manual de instâncias (plano B)
`file.place` e `object.setBounds` do motivo, `object.repeat.grid {rows:8, cols:6, hSpacing:30, vSpacing:0}`, `object.repeat.options {gridType:"brick"}` (aceita brick, hex, grid, brickByRow; "hexagonal", "staggered" e "offset" dão erro), `object.repeat.expand {}` (devolve um grupo), e `object.clippingMask.make` com um retângulo para cortar na caixa. Funciona, nível estúdio, brick por coluna (colunas ímpares descem). Resultado visual igual ao A.

## Caminho C: tile seamless desenhado por IA (ondas-serra-traco.png, 1254 px, fios dourados com alfa)
`object.pattern.make {tileType:"grid", width:300, height:300}`. O PNG de origem fecha: medi a diferença entre coluna esquerda e direita (média 3,2/255, menor que entre colunas vizinhas internas, 5,9) e linhas topo/base (0,0). Sem aviso de emenda a 100 %.

## O que o PDF contém (medido)
- `/PatternType` aparece 0 vezes: o VectorCraft EXPANDE o padrão na exportação, não grava ladrilho vetorial (nem de imagem). São repetições do mesmo objeto de imagem (um só XObject, reaproveitado ~70 vezes) recortadas. O arquivo não explode, mas não é "tiling pattern".
- Resolução efetiva é a do PNG espremido: 645 a 821 ppi no original (desperdício), 301 ppi depois de encolher. Nada vira 72 ppi.
- Rasteriza: o motivo (é PNG, só pode ser raster). Fundo, texto e retângulos são vetor.

## Emenda do ladrilho (honesto)
Zoom 800 dpi (poppler E cairo, dois leitores) no encontro de ladrilhos do Caminho C: aparecem risquinhos de 1 a 2 px onde cada fio cruza a borda (linha levemente mais fina no corte) e uma linha de fundo quase imperceptível no cairo. A 100 % e a 400 dpi: invisível. O critério "invisível em 800 %" NÃO passou totalmente. Motivos com margem (A, bolas, cronômetro) não têm emenda, pois não tocam a borda do ladrilho: para kit, prefira motivo com margem, não tile contínuo.

## Variante vetorizada (v/teste_trace.py)
`imageTrace.makeAndExpand {id, params:{mode:"color", palette:"limited", colors:2, ignoreWhite:true, paths:90, corners:50, noise:2, method:"abutting"}}` (0,3 s, 23 caminhos, 5.373 âncoras) e depois `pattern.make` sobre o resultado. Vira vetor puro, mas: (a) PDF vai a 1,87 MB para a página inteira (~72 mil curvas), (b) o traço sai mais grosso que o original, (c) degraus de 1 px na borda do ladrilho (pior que o raster). Modo "logo" é recusado para esse motivo ("isn't a flat-colour logo"). Veredito: não compensa para tile contínuo; só para motivo simples.

## Veredito visual
Caminhos A e B: estúdio (zoom a 100 % e 200 %, bolas, cronômetros e ondas nítidos, brick e hex corretos, alinhados à origem da página). Caminho C e variante vetorizada: bom a olho nu, com emenda só em zoom extremo.

## Armadilhas
- O original fica na página depois de `pattern.make`.
- Sem fundo sob o fill em padrão a página fica branca.
- `hexByRow` com ladrilho 170 pt: espaçamento vertical é menor que o horizontal, ajustar `height` para a densidade.
- `pattern.options {sizeTileToArt, hSpacing, vSpacing, copies}` existe e não foi necessário.
