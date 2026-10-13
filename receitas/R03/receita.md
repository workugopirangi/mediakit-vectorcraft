# R03. Foto dentro de letras gigantes

Status: FUNCIONA

## Sequência (R03/teste.py)
1. `text.create {x, y(baseline), text:"SPRINT", font:"Helvetica Neue", style:"Condensed Black", size:440, color:"#FFFFFF"}` + `text.setStyle {ids, tracking:-10}`.
2. `file.place {path, link:false}` + `object.setBounds {..., reference:0}` cobrindo toda a palavra.
3. `select.set {ids:[texto]}` + `object.arrange.bringToFront {}` (o texto tem que ser o topo).
4. `select.set {ids:[foto, texto]}` + `object.clippingMask.make {}`. Aceita texto direto, não precisa de `type.createOutlines`.

## Aparência
Curvas dos glifos limpas, sem serrilhado visível a 50 ppi; foto aparece só dentro das letras. Qualidade de estúdio.

## Defeitos e cuidados
- Escolha foto clara/colorida: partes escuras da foto somem em fundo preto (o "N" e o "T" perdem o contorno no teste). Use fundo contrastante com a foto.
- Em 440 pt "SPRINT" ocupa cerca de 1330 pt de largura; com 520 pt estoura a página. Meça antes.
- No PDF a fonte do texto mascarado não aparece em `pdffonts` (a máscara vira caminho vetorial): texto não editável no PDF, mas sem risco de fonte faltando.
- Foto a 84 ppi efetivos porque o c-arena tem 1672 px esticado em 1440 pt; nada foi rasterizado pelo VectorCraft.
