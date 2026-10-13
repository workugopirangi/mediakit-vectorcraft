# R11. Hierarquia tipográfica com estilos nomeados

Status: FUNCIONA (descoberta importante: parágrafo e caractere são estilos separados)

## Sequência (R11/teste.py)
1. Criar um texto de amostra com a aparência desejada (`text.create` + `text.setStyle {tracking, leading}`), `select.set {ids:[t]}`.
2. `paraStyle.new {name:"KIT Corpo", id:t}` E `charStyle.new {name:"KIT Corpo", id:t}`. Apagar a amostra (`edit.clear`).
   - `paraStyle` guarda SÓ atributos de parágrafo (justify, recuos, space_before/after, hyphenate). Fonte, corpo, entrelinha, tracking e cor ficam no `charStyle` (confirmado em `charStyle.list`: font_family, font_style, size, leading, tracking, fill...). Com apenas paraStyle o texto saiu em Source Sans 12 pt (primeira tentativa falhou assim).
3. Texto novo: `text.create {x,y,text,size:12, area?:{width,height,fit:"autoHeight"}}` e depois `paraStyle.apply {name, ids:[t]}` + `charStyle.apply {name, ids:[t]}` (devolve {count:1}).
4. Mudar a hierarquia inteira: `charStyle.setAttrs {name:"KIT Titulo", attrs:{...atributos de charStyle.list com size:60, leading:64, fill:{type:"solid", color:{model:"rgb", r,g,b}}}}`.

## Prova de que "trocar o estilo muda todas as ocorrências"
`charStyle.list` mostrou uses: Display 1, Titulo 2, Corpo 2, Legenda 1. Depois do `setAttrs` em KIT Titulo, os dois títulos mudaram juntos de branco 44 pt para amarelo 60 pt (R11/antes-1.png contra R11/preview-1.png). Corpo e legenda ficaram intactos.

## Aparência
Quatro níveis (Condensed Black 190, Bold 44, Medium 19, Bold 11 caixa-alta com tracking 220) claros, leading sem colisão de ascendentes, nenhum aviso de fonte. Qualidade de estúdio.

## Cuidados
- Texto de amostra "x" criado em (0,0) precisa ser apagado.
- `charStyle.setAttrs` exige o objeto de atributos completo (ler de `charStyle.list`, mudar chaves e devolver).
- pdffonts: 3 fontes Helvetica Neue embutidas (CondensedBlack, Bold, Medium); sem fallback. PDF de 25 KB. Nada rasteriza.
