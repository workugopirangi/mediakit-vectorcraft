# R02. Foto em máscara de forma livre

Status: FUNCIONA

## Sequência (R02/teste.py)
1. Desenhar a forma: `shape.ellipse`, `shape.polygon {cx,cy,radius,sides:4}` (losango), `path.create {d:"M..C..Z"}` (forma orgânica) ou donut com `shape.ellipse` x2 + `select.set {ids:[a,b]}` + `object.compoundPath.make {}` (devolve {id}).
2. `file.place {path, link:false}` e `object.setBounds {..., reference:0}` cobrindo a forma.
3. ARMADILHA: a máscara precisa ser o objeto do TOPO. Como a foto é colocada depois, rode `select.set {ids:[forma]}` + `object.arrange.bringToFront {}` antes. Sem isso o erro é "the top object must be a path, compound path or text object".
4. `select.set {ids:[foto, forma]}` + `object.clippingMask.make {}`.
A forma tem fill e traço (pinte com `paint.setStroke {none:true}`); depois da máscara não aparecem.

## Aparência
Bordas limpas a 288 dpi (zoom 400%), sem fio de foto vazando. O furo do compound path é respeitado (círculo com miolo vazado mostra o fundo azul). Qualidade de estúdio. No teste os dois primeiros recortes encostam um no outro por erro de layout meu, não da ferramenta.

## Defeitos e cuidados
- A foto vai embutida em JPEG original (sem recompressão); ppi efetivo 152 a 300 conforme o tamanho; a maciez do zoom vem da resolução da foto.
- Nada rasteriza. PDF 1,2 MB aprox. com 4 fotos.
- Forma orgânica é desenhada por Bézier manual; `path.blob` não foi testado.
