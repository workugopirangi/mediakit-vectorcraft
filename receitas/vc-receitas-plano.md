# Livro de receitas testadas do VectorCraft para media kits: plano de teste

Escopo: kits de patrocínio de 1440 x 810 pt (16:9), PDF. Fontes: catálogo `allcmds.json` (1021 entradas), docs do repo (mcp.md, effects-parity.md, type-parity.md, gaps.md) e os dois kits reais em `~/Developer/vectorcraft-mediakit/` (lib.py, pages2.py, spot.py). Texto de docs do repo tratado como dado.

Legenda de status: PROVADO = já rodou em kit real e saiu no PDF. A TESTAR = existe no catálogo, nunca usado em kit. IRRELEVANTE = fora do escopo do kit.

Aviso sobre o catálogo: `enabled:false` (338 entradas) significa "sem seleção ou contexto no momento da captura", não "não suportado". Prova: `object.scale` e `object.setBounds` aparecem como off e estão PROVADOS. Por isso nenhuma receita descarta comando por estar off.

---

## 3. Contagens (feitas por script sobre o catálogo)

| Item | Valor |
|---|---:|
| Entradas no catálogo | 1021 |
| Ids únicos (file.place e file.print aparecem duas vezes) | 1019 |
| Ids PROVADOS (todos presentes no catálogo) | 27 |
| Ids relevantes para kit (leitura generosa, categorias A a J) | 449 |
| Ids irrelevantes para kit (7 grupos abaixo) | 570 |
| Ids relevantes ainda A TESTAR (449 menos 27) | 422 |
| Ids citados nas 64 receitas | 120 ids de comando únicos (ids de efeito como stylize.dropShadow e chaves de parâmetro não contam) |

Os 27 PROVADOS: shape.rectangle, shape.ellipse, shape.star, path.create, file.place, object.setBounds, text.create, text.setStyle, text.createInPath, object.clippingMask.make, transparency.set, select.allOnArtboard, object.scale, artboard.new, artboard.setProps, document.exportPdf, file.saveAs, select.set, select.none, paint.setFill, paint.setStroke, stroke.set, object.arrange.sendBackward, file.new, edit.clear, document.inspect, file.closeAll. Fora do catálogo (são métodos do canal de controle, não comandos): ui.dialog.set e ui.dialog.confirm, também provados.

## 1. Categorias relevantes e comandos que importam

Formato: `id` {parâmetros-chave}. PROVADO ou A TESTAR.

### A. Formas e traço base (13 ids relevantes)
- PROVADO: `shape.rectangle` {x,y,width,height,radius}, `shape.ellipse` {x,y,width,height}, `shape.star` {cx,cy,radius1,radius2,points,rotation}, `path.create` {d | anchors[{x,y,in,out}], closed}.
- A TESTAR: `shape.polygon` {cx,cy,radius,sides,rotation}, `shape.spiral` {cx,cy,radius,decay,segments}, `shape.arc`, `shape.line`, `shape.flare`, `shape.rectangularGrid` {rows,columns,rowSkew,columnSkew,frame,fill}, `shape.polarGrid` {concentric,radial,compound}, `path.freehand`, `path.blob` {points,size,merge}.
- Gotcha conhecido: forma nova nasce com traço preto de 1 pt. Sempre chamar `paint.setStroke {none:true}`.

### B. Cor, gradientes, swatches, spot (66 ids)
- PROVADO: `paint.setFill` / `paint.setStroke` com `color` hex.
- A TESTAR: `paint.setFill {gradient:{kind:linear|radial|freeform, stops[{offset,color,opacity,midpoint}], angle|start,end, aspect, focal}}`, `paint.editGradient`, `paint.setGradientGeom`, `paint.freeform.addPoint {at,color,spread,line}`, `paint.freeform.get`, `swatch.new {name,color,mode}`, `swatch.setSpot {name}`, `paint.setFill {swatch,tint}` (cor global religada), `recolor.apply {map[{from,to}], method, includeImages, includePatterns}`, `color.convert`, `swatch.library.get`, `edit.colors.toGrayscale|toCMYK|invert|saturate|adjustBalance`, `file.documentColorMode`.

### C. Malha, envelope e distorção (21 ids)
- A TESTAR: `object.mesh.create {rows,cols,appearance,highlight}`, `object.mesh.setPointColor {id,index,color}`, `object.mesh.movePoint`, `object.envelope.makeWithWarp {style:arc|arch|bulge|flag|wave|fish|rise|squeeze|twist, bend, h, v}`, `object.envelope.makeWithMesh {rows,cols}`, `object.envelope.makeWithTopObject`, `object.envelope.expand`, `object.envelope.setMeshPoint`, `object.distort {corners[4]}`, `object.puppetWarp`, `object.liquify`.
- Risco conhecido: mesh sai com emendas e cruzes no PDF (auditoria anterior).

### D. Tipografia (84 ids)
- PROVADO: `text.create` (ponto e área), `text.setStyle` {font,style,size,leading,tracking,justify,fill,features,start,end em byte}, `text.createInPath {mode:onPath|area}`.
- A TESTAR: `text.setRangeStyle` {kerning,baselineShift,hScale,vScale,rotation,fill,stroke,strokeWidth,features,smallCaps,position}, `text.setFormat` {leftIndent,spaceBefore,spaceAfter}, `text.areaOptions` {rows,columns,gutter,inset,firstBaseline,verticalAlign,fit:autoHeight|shrinkText}, `text.thread.create`, `text.tabs.set` {stops[{position,align,leader,alignOn}]}, `type.pathOptions` {start,end,flip,effect,alignToPath,spacing}, `type.createOutlines`, `type.convertToAreaType`, `object.textWrap.make`, `text.fonts` (lê `missingGlyphs` e `status`), `text.fontList`, `charStyle.*` e `paraStyle.*` (new, apply, redefine), `type.changeCase`, `type.smartPunctuation`.
- Gotchas: glifo ausente cai em Inter sem aviso (estrela em Helvetica Neue). Fontes variáveis: só instâncias nomeadas como estilo, sem eixos (type-parity.md). Hifenização e Optical Margin: ausentes.

### E. Imagem, máscaras, recorte, trace, halftone (34 ids)
- PROVADO: `file.place`, `object.setBounds {reference:0}`, `object.clippingMask.make`, `transparency.set {opacity}`.
- A TESTAR: `transparency.set {blend}` (Multiply, Screen, Overlay), `transparency.makeOpacityMask {clip,invert}`, `transparency.setOpacityMask`, `object.maskImage`, `object.cropImage {rect|trim}`, `imageTrace.make {preset, params{mode:blackAndWhite|grayscale|color|logo, palette, colors, threshold, paths, corners, noise, ignoreWhite}}`, `imageTrace.expand`, `imageTrace.presets`, `object.vectorHalftone {shape,frequency,angle,mode:mono|cmyk,color,invert,clip,keepOriginal}`, `object.createObjectMosaic {columns,rows,spacingX,spacingY,gray}`, `object.rasterize {ppi,background}`.

### F. Efeitos e aparência (47 ids)
- A TESTAR: `effect.apply {effect:id, params, item, target}` com ids de `effect.list`: `stylize.dropShadow|feather|innerGlow|outerGlow|roundCorners|scribble`, `artistic.filmGrain`, `texture.grain|craquelure|mosaicTiles|stainedGlass`, `blur.gaussian|radial`, `pixelate.colorHalftone|crystallize|mezzotint|pointillize`, `distort.roughen|tweak|zigZag|twist|puckerBloat|diffuseGlow|oceanRipple`, `warp.*` (15), `brushStrokes.*` (8). Também `effect.setParams`, `effect.expandAppearance`, `document.rasterEffectsSettings {resolution:300, background}`, `appearance.addFill|addStroke|setItem|moveItem`, `graphicStyle.new|apply|redefine`.
- Gotchas conhecidos: sombra e grão rasterizam a 72 ppi se `resolution` não for 300. Efeito depois de fill em padrão, gradiente radial ou freeform só exporta no lugar certo desde #1536 (corrigido segundo o repo, validar).
- 3D (Extrude & Bevel, Inflate, Rotate, Revolve): existe como efeito inicial (cerca de 25% de paridade), ids a descobrir em `effect.list`.

### G. Booleanas, offset, blend, traço, expandir (61 ids)
- A TESTAR: `object.pathfinder.unite|minusFront|intersect|exclude|divide|trim|merge|crop|outline|minusBack`, `object.path.offsetPath {offset, joins:round|miter|bevel}`, `object.path.outlineStroke`, `object.path.simplify`, `object.path.addAnchorPoints`, `object.path.splitIntoGrid`, `object.blend.make {steps|distance|smooth, orientation:page|path}`, `object.blend.options`, `object.blend.replaceSpine`, `object.blend.expand`, `object.compoundPath.make`, `stroke.set {weight,cap,join,dash,dashOffset,align,arrowheads,profile}`, `stroke.setAdvanced {brush,arrowScale}`, `stroke.widthPoint.set`, `stroke.widthProfile.set`, `brush.new {type:art|scatter|pattern|calligraphic|bristle}`, `brush.apply`, `object.expand`, `object.expandBrush`, `object.shape.convertToShape`, `object.arrange.*`.
- PROVADO: `stroke.set {weight}`, `object.arrange.sendBackward`.

### H. Repetição, padrões, símbolos (28 ids)
- A TESTAR: `object.pattern.make {name,tileType:grid|brickByRow|brickByColumn|hexByColumn|hexByRow,brickOffset,width,height}`, `pattern.options {tileType,hSpacing,vSpacing,overlap,copies}`, `object.pattern.done`, `pattern.transform {matrix}`, `pattern.list`, `object.repeat.radial {instances,radius}`, `object.repeat.grid {rows,cols,hSpacing,vSpacing}`, `object.repeat.mirror {angle,offset}`, `object.repeat.options`, `object.repeat.expand`, `symbol.new`, `symbol.place {name,x,y}`, `symbol.spray {points,radius,density}`, `symbol.breakLink`.

### I. Gráficos de dados (5 ids)
- A TESTAR: `graph.create {type:column|stackedColumn|bar|stackedBar|line|area|scatter|pie|radar, x,y,width,height, series, categories, rows, csv}`, `graph.setData`, `graph.setType`, `graph.design`, `graph.marker`.
- Alternativa a comparar: barras desenhadas com `shape.rectangle` por Python (o que os kits fizeram, PROVADO).

### J. Páginas, camadas, alinhamento, transformação, PDF (90 ids)
- PROVADO: `file.new`, `artboard.new`, `artboard.setProps`, `select.allOnArtboard`, `object.scale`, `object.setBounds`, `document.exportPdf`, `file.saveAs`, `file.closeAll`, `document.inspect`, `select.set`, `select.none`, `edit.clear`.
- A TESTAR: `document.exportPdf {standard:pdfX4|pdfX1a|pdfX3, compatibility, compression{color,gray}, marks, bleed, createLayers, range, flattenerPreset, preserveEditing, thumbnails}`, `document.pdfSettings` (mostra o que difere do preset, sem gravar), `document.pdfInfo`, `document.setup`, `object.align {to:artboard|selection|key}`, `object.distribute`, `object.distributeSpacing`, `object.group`, `object.transform {matrix, copy}`, `object.transformEach`, `object.createTrimMarks`, `layer.new|setProps|setCurrent|collectInNew`, `artboard.rearrange|duplicate|reorder`, `links.embed`.

### Grupos IRRELEVANTES para kit (570 ids, uma linha cada)
1. UI, janelas, painéis, atalhos, ferramentas, preferências, ajuda, plugins, scripts (ui.*, window.*, view.*, shortcuts.*, toolbar.*, tool.*, prefs.*, help.*, app.*, guide.*, plugin.*, command, script, docInfo): 212 ids. Nota: `ui.*Dialog` são caixas do app, não servem a script. A QA usa `document.exportPdf` mais render do PDF, não `ui.screenshot`.
2. Perspectiva (perspective.*): 25 ids.
3. Fatias, web, CSS e exports de tela, Office, SVG e PNG (slice, object.slice.*, webExport.*, css.*, document.exportForWeb, file.saveForWeb*, exportForScreens, exportForOffice, file.export.svg e png, attributes.openUrl): 38 ids. Exceção de QA: `file.export.png` serve para miniatura de conferência.
4. Impressão, pré-impressão, CAD e formatos legados (print.*, flattener.*, pdf.preset.*, file.print, document.exportDxf, exportEps, dxfInfo, file.package, overprint, color.plates, color.gamutCheck, object.flattenTransparency): 33 ids. O PDF/X sai pelo `document.exportPdf`, que está em J.
5. Dados e variáveis (dataset.*, variable.*): 19 ids.
6. Edição fina de pontos, seleção avançada, Live Paint, Shaper, Shape Builder, Magic Wand, Eyedropper, facas e cortadores (path.* exceto create, freehand e blob; select.* exceto set, none, all, add, allOnArtboard; livePaint.*, shaper.*, shapeBuilder.*, magicWand.*, eyedropper.*): 112 ids.
7. Administração de arquivo e documento (file.openRecent1 a 30, recuperação, clipboard.*, edit.cut, copy, paste, undo, redo, preferences, library.* de bibliotecas de nuvem, links.* de relink e pacote, assets.*, document.open, serialize, json, node, rulerOrigin, isolamento, lock e hide): 131 ids.

---

## 2. As 64 receitas, em ordem de impacto visual

Convenção de teste (vale para todas): uma artboard 1440 x 810 por receita, `file.new` já em 1440x810 (não escalar do 1920 x 1080), exportar com `document.exportPdf`, rasterizar a página com `pdftoppm -r 144` e inspecionar a imagem; abrir o PDF em pelo menos Preview e um segundo leitor (Chrome ou pdf.js), porque as falhas de mesh e transparência dependem do leitor. Critério extra para toda receita: nenhum traço preto de 1 pt indesejado, nenhuma fonte substituída em silêncio, tamanho do PDF anotado.

### Bloco 1: foto, cor e recorte (impacto máximo)

**R01. Duotone de foto**
- Objetivo visual: foto de atleta em dois tons da marca (preto e amarelo), assinatura de kit de estúdio. Uso: capa e páginas de cenário.
- Comandos: `file.place`, `object.setBounds`, `edit.colors.toGrayscale`, `edit.colors.adjustBalance` ou `edit.colors.saturate`, `shape.rectangle`, `paint.setFill`, `transparency.set {blend:"Multiply"|"Screen"|"Lighten"}`, `object.group`, `object.clippingMask.make`. Variante B: `recolor.apply {includeImages:true, map}`.
- Critério: sombras da foto na cor escura da marca, altas luzes na cor clara, sem banding visível; mesma aparência no segundo leitor; foto nítida (150 ppi efetivos ou mais).
- Risco: modos de mesclagem no PDF dependem do leitor; `toGrayscale` pode alterar a imagem linkada em vez de uma cópia. Plano B: dois retângulos coloridos (Multiply e Screen) sobre a foto cinza.

**R02. Foto em máscara de forma livre (círculo, losango, blob)**
- Objetivo visual: fotos fora do retângulo, em formas orgânicas. Uso: grade de fotos de edições anteriores.
- Comandos: `shape.ellipse|polygon|star`, `path.create {d}`, `file.place`, `object.setBounds`, `object.clippingMask.make` (base PROVADA com retângulo).
- Critério: borda do recorte limpa em zoom 400%, sem fio de foto fora da máscara, máscara com compound path (furo) respeitada.
- Risco: máscara composta com furo e even-odd (doc diz que funciona, não testado em PDF).

**R03. Foto dentro de letras gigantes**
- Objetivo visual: palavra "BRASIL" ou nome do evento com a foto preenchendo as letras. Uso: capa.
- Comandos: `text.create {size 400 ou mais, Helvetica Neue Condensed Black}`, `file.place`, `object.clippingMask.make` (o texto usado como máscara perde a cor), `type.createOutlines` como plano B.
- Critério: foto visível só dentro dos glifos, curvas sem serrilhado, texto editável (ou contorno de propósito).
- Risco: máscara de texto pode virar contorno no PDF; checar embutimento de fonte.

**R04. Tipografia gigante sangrando da página**
- Objetivo visual: título maior que a página, cortado nas bordas, ocupando 70% da área. Uso: abertura de seção.
- Comandos: `text.create`, `text.setStyle {size, tracking negativo, leading}`, `object.setBounds`, retângulo do tamanho da artboard (`shape.rectangle` mais `object.clippingMask.make`).
- Critério: PDF mostra só a área da artboard, letra cortada limpa na borda, sem texto vazando para a página vizinha (artboards usam GAP de 2000 pt).
- Risco: objeto fora da artboard pode aparecer em leitores que usam a bounding box total; testar `cropTo` e a máscara.

**R05. Foto com fade por opacity mask (degradê para a cor do fundo)**
- Objetivo visual: foto "derretendo" no bloco de cor, base de composição editorial. Uso: capa, páginas de cota.
- Comandos: `file.place`, `shape.rectangle` mais `paint.setFill {gradient linear preto para branco}`, `transparency.makeOpacityMask {clip, invert}`.
- Critério: transição suave sem degraus, nenhuma borda dura.
- Risco: vira soft mask no PDF; PDF/X-1a e X-3 achatam isso (ver R57).

**R06. Foto com sobreposição de cor em bloco**
- Objetivo visual: foto com camada de cor semitransparente e texto por cima, legibilidade garantida. Uso: cartões de benefício.
- Comandos: `shape.rectangle`, `paint.setFill`, `transparency.set {opacity, blend}`, `object.arrange.sendBackward`.
- Critério: contraste do texto 4.5:1 ou mais sobre a foto; cor lida igual nos dois leitores.
- Risco: baixo (base PROVADA); só confirmar blend em leitor externo.

**R07. Foto recortada (cutout) com contorno e sombra dura**
- Objetivo visual: atleta recortado sobre bloco de cor com contorno branco estilo adesivo. Uso: capa, depoimento.
- Comandos: `file.place` (PNG com alfa), `imageTrace.make {mode:"blackAndWhite"}` para silhueta, `object.path.offsetPath {offset, joins:"round"}`, `object.pathfinder.unite`, `paint.setFill`.
- Critério: contorno uniforme de 8 pt ao redor da silhueta, sem pontas, sombra dura deslocada (vetor).
- Risco: trace de silhueta de foto real é irregular; usar limiar alto e `object.path.simplify`.

**R08. Textura de papel e ruído sobre blocos de cor**
- Objetivo visual: tirar o aspecto chapado digital. Uso: fundo de todas as páginas.
- Comandos: `effect.apply {effect:"texture.grain"|"artistic.filmGrain"}`, `document.rasterEffectsSettings {resolution:300}`, `transparency.set`.
- Critério: grão fino visível em 100%, sem aspecto pixelado (72 ppi é o defeito conhecido); PDF abaixo de 15 MB por página de fundo cheio.
- Risco: alto: rasteriza em 72 ppi sem a configuração; PDF pesa. Plano B: grão como PNG gerado fora e posicionado com `file.place` em Multiply.

**R09. Foto desfocada de fundo (profundidade)**
- Objetivo visual: foto de arena desfocada atrás de texto nítido. Uso: páginas de números.
- Comandos: `effect.apply {effect:"blur.gaussian"}`, `document.rasterEffectsSettings`, `transparency.set`.
- Critério: blur sem borda transparente escura nas pontas da imagem, resolução suficiente.
- Risco: bordas da imagem desvanecem (halo); cobrir com máscara menor que a foto.

**R10. Borda irregular tipo papel rasgado**
- Objetivo visual: foto com borda rasgada ou recortada à mão. Uso: depoimentos, bastidores.
- Comandos: `path.create`, `effect.apply {effect:"distort.roughen"}` ou `distort.tweak`, `object.expand`, `object.clippingMask.make`.
- Critério: borda orgânica sem repetição óbvia, máscara expandida e leve.
- Risco: `object.expand` de efeito ao vivo; checar se vira path limpo.

### Bloco 2: tipografia de estúdio

**R11. Hierarquia tipográfica completa (display, título, corpo, legenda)**
- Objetivo visual: 4 níveis consistentes com tracking e leading ajustados. Uso: todas as páginas.
- Comandos: `text.setStyle {tracking, leading}`, `charStyle.new|apply`, `paraStyle.new|apply`.
- Critério: estilos aplicados por nome; trocar o estilo muda todas as ocorrências; leading sem colisão de ascendentes.
- Risco: baixo; estilos nunca usados em kit.

**R12. Recursos OpenType (numerais tabulares, ligaduras, small caps, alternativos)**
- Objetivo visual: números de métricas alinhados (tnum), versaletes em rótulos. Uso: audiência e preço.
- Comandos: `text.setStyle {features:["tnum","smcp","ss01"]}`, `text.setRangeStyle {smallCaps}`.
- Critério: números de largura igual em colunas, glifos alternativos trocados de verdade.
- Risco: Helvetica Neue pode não ter `tnum`; testar também uma fonte com OpenType rico.

**R13. Fonte variável (instâncias nomeadas)**
- Objetivo visual: peso intermediário preciso. Uso: títulos.
- Comandos: `text.fontList`, `text.setStyle {font, style:<instância>}`.
- Critério: instâncias disponíveis aplicam-se e saem no PDF com o peso certo.
- Risco: conhecido: eixos livres NÃO existem (só instâncias nomeadas). Registrar como limite, não testar eixos.

**R14. Colunas e quadros de texto**
- Objetivo visual: bloco de texto em 2 ou 3 colunas com calha. Uso: páginas "sobre o evento".
- Comandos: `text.create {area:{width,height,fit}}`, `text.areaOptions {columns, gutter, inset, verticalAlign}`, `text.thread.create`.
- Critério: texto flui entre colunas sem linha órfã; `overflow` vazio na resposta.
- Risco: `text.create` devolve `overflow` quando não cabe: tratar como falha da receita.

**R15. Tabela de cotas com tabulação e líder pontilhado**
- Objetivo visual: lista "Item ........ R$" alinhada. Uso: página de investimento.
- Comandos: `text.create`, `text.tabs.set {stops[{position, align:"right", leader:". "}]}`.
- Critério: valores alinhados à direita (ou decimal) na mesma coluna; líder desenhado.
- Risco: o doc admite "leader drawing not verified".

**R16. Texto com contorno, vazado e preenchimento em gradiente**
- Objetivo visual: letras grandes só com contorno, ou preenchidas com degradê. Uso: números de destaque.
- Comandos: `text.setRangeStyle {fill:"none", stroke, strokeWidth}`, `paint.setFill {gradient}` com texto selecionado.
- Critério: contorno sem pontas de miter estouradas (join round), gradiente cobre o bloco todo.
- Risco: gradiente em texto fica no "espaço do texto"; conferir deslocamento.

**R17. Texto em mix-blend sobre foto**
- Objetivo visual: título que "entra" na foto. Uso: capa.
- Comandos: `text.create`, `transparency.set {blend:"Multiply"|"Overlay", opacity}`.
- Critério: legibilidade preservada, aparência igual nos dois leitores.
- Risco: igual ao R01.

**R18. Texto em contornos como trava de segurança**
- Objetivo visual: PDF independe de fonte instalada e resolve glifos ausentes. Uso: versão final enviada ao cliente.
- Comandos: `type.createOutlines`, `text.fonts` (conferir `missingGlyphs` antes).
- Critério: zero fontes no PDF (conferir com `pdffonts`), aparência idêntica antes e depois.
- Risco: perde edição; fazer só na cópia final.

**R19. Auditoria de glifos ausentes**
- Objetivo visual: nunca mais uma estrela virar Inter sem aviso. Uso: etapa fixa antes do export.
- Comandos: `text.fonts {selectionOnly:false}` (lê `missingGlyphs`, `status`).
- Critério: relatório lista todo texto com glifo ausente; a estrela substituída por `shape.star`.
- Risco: baixo.

**R20. Texto em caminho livre (curva, onda, arco)**
- Objetivo visual: slogan acompanhando uma curva. Uso: capa, rodapé de seção.
- Comandos: `path.create`, `text.createInPath {mode:"onPath", at}`, `type.pathOptions {start,end,flip,effect,alignToPath,spacing}`.
- Critério: letras seguem a curva sem sobrepor, início e fim certos.
- Risco: base PROVADA só em elipse; curvas em S podem pinçar letras.

### Bloco 3: ornamentos, selos e padrões

**R21. Selo circular com texto em volta (carimbo)**
- Objetivo visual: selo "EDIÇÃO 2026 / OFICIAL" com texto em círculo, anel duplo, estrela central. Uso: capa, cotas.
- Comandos: `shape.ellipse` (2 anéis), `text.createInPath {mode:"onPath"}`, segundo texto invertido com `type.pathOptions {flip:true}`, `shape.star`, `stroke.set {dash}`.
- Critério: texto superior e inferior legíveis, espaçamento igual, círculo fecha sem sobra; selo girado 12 graus.
- Risco: base de texto em elipse PROVADA; texto na parte de baixo (flip) e fechamento dos 360 graus não.

**R22. Selo dentado e sunburst**
- Objetivo visual: medalha com bordas serrilhadas. Uso: destaque de cota Ouro.
- Comandos: `shape.star {points:24, radius2 próximo de radius1}`, `shape.polygon`, `effect.apply {effect:"stylize.roundCorners"}`, `object.path.offsetPath`.
- Critério: dentes regulares, cantos levemente arredondados, anel interno concêntrico.
- Risco: baixo.

**R23. Padrão a partir de motivo desenhado por IA (pattern swatch)**
- Objetivo visual: textura de marca feita de um motivo repetido (bola, luva ou estrela desenhada por IA). Uso: fundo de seções, capas.
- Comandos: `file.place` (PNG do motivo), `imageTrace.make {mode:"logo"|"color", palette:"limited", colors:3}`, `imageTrace.expand`, `object.pattern.make {tileType:"brickByRow", width, height}`, `object.pattern.done`, `paint.setFill {swatch}`; ajustes por `pattern.options` e `pattern.transform`.
- Critério: emendas do tile invisíveis em zoom 800%, tile alinhado às bordas da artboard, PDF com padrão como tiling vetorial (não imagem gigante).
- Risco: alto e de alto retorno; efeitos rasterizados sobre fill em padrão foram corrigidos (#1536), validar. Plano B: `object.repeat.grid` mais `object.repeat.expand`.

**R24. Padrão por repetição de vetor puro (live repeat grid)**
- Objetivo visual: grade de ícones esportivos. Uso: fundo de rodapé.
- Comandos: `object.repeat.grid {rows, cols, hSpacing, vSpacing}`, `object.repeat.options {gridType, flipRows}`, `object.repeat.expand`.
- Critério: grade regular, linhas alternadas espelhadas quando pedido, expandido sem sobreposição duplicada.
- Risco: milhares de instâncias pesam; medir tempo e tamanho.

**R25. Radial repeat (rosa dos ventos, mandala, raios)**
- Objetivo visual: raios saindo do centro (sunburst) ou rosa dos ventos de mapa. Uso: capa, fundo de logo.
- Comandos: `object.repeat.radial {instances:24, radius}`, `object.repeat.options {startAngle, endAngle, reverseOverlap}`.
- Critério: ângulos exatos (360/N), sem lacuna no fechamento.
- Risco: baixo.

**R26. Mirror repeat (simetria, borda espelhada)**
- Objetivo visual: ornamento simétrico, moldura. Uso: cabeçalhos.
- Comandos: `object.repeat.mirror {angle:90, offset}`.
- Critério: eixo exato, sem fio no meio.
- Risco: baixo.

**R27. Símbolos e confete (spray)**
- Objetivo visual: confete de estrelas e bolas espalhado, multidão estilizada. Uso: agradecimento, capa.
- Comandos: `symbol.new`, `symbol.spray {points, radius, density}`, `symbol.place`, `symbol.breakLink`.
- Critério: distribuição natural, rotação e escala variadas, sem pontos fora da artboard.
- Risco: instâncias de símbolo no PDF; medir tamanho.

**R28. Ornamentos geométricos: espiral, grade polar, malha retangular**
- Objetivo visual: fundos técnicos tipo blueprint, ondas concêntricas. Uso: páginas de dados.
- Comandos: `shape.spiral`, `shape.polarGrid {concentric, radial}`, `shape.rectangularGrid {rows, columns, rowSkew}`, `stroke.set`.
- Critério: linhas finas (0.5 pt) uniformes, sem moiré no PDF reduzido.
- Risco: traço fino pode sumir em leitores; definir espessura mínima.

**R29. Halftone vetorial em foto (pontos)**
- Objetivo visual: foto em retícula de pontos, look de impresso. Uso: capa, divisórias.
- Comandos: `file.place`, `object.vectorHalftone {shape:"circle", frequency:12 a 25, angle:45, mode:"mono", color, clip:true}`.
- Critério: pontos nítidos (vetor), contraste preservado, número de subpaths razoável (PDF abaixo de 20 MB).
- Risco: milhares de subpaths; compound path de dots já foi PROVADO, mas não neste volume.

**R30. Halftone CMYK colorido**
- Objetivo visual: foto em retícula de 4 cores com rosetas. Uso: divisória pop.
- Comandos: `object.vectorHalftone {mode:"cmyk", frequency, angle}`.
- Critério: ângulos de tela (cyan -30, magenta +30, amarelo -45 a partir do preto) visíveis; cores multiplicam sem lacunas brancas.
- Risco: o multiply entre telas depende de blend no PDF.

**R31. Halftone raster por efeito (pixelate.colorHalftone)**
- Objetivo visual: comparar com o vetorial: retícula como efeito ao vivo.
- Comandos: `effect.apply {effect:"pixelate.colorHalftone"}`, `document.rasterEffectsSettings {resolution:300}`.
- Critério: parecido com o R29 a olho nu; peso de arquivo medido.
- Risco: 72 ppi se esquecer a resolução.

**R32. Image Trace: foto posterizada e logo vetorizado**
- Objetivo visual: foto em 3 a 4 cores chapadas; logo de patrocinador PNG virando vetor limpo. Uso: capas, parede de logos.
- Comandos: `imageTrace.make {params{mode:"color", palette:"limited", colors:4, paths, corners, noise}}` e `{mode:"logo", logoColors}`, `imageTrace.expand`.
- Critério: poucos nós, curvas suaves, cantos vivos nos logos, sem manchas de ruído.
- Risco: médio; existe `docs/image-trace-quality.md`, ler antes.

**R33. Mosaico de quadrados a partir de uma foto**
- Objetivo visual: foto reduzida a quadrados coloridos, ornamento de dados. Uso: divisória.
- Comandos: `object.createObjectMosaic {columns:40, rows:22, spacingX:2, spacingY:2}`.
- Critério: cada quadrado com a cor média certa, grade alinhada.
- Risco: baixo.

### Bloco 4: gradientes e malhas

**R34. Gradiente linear de marca em bloco e em fundo**
- Objetivo visual: fundo com degradê sutil de duas cores, sem banding. Uso: todas as páginas.
- Comandos: `paint.setFill {gradient:{kind:"linear", stops, angle}}`, `paint.setGradientGeom`.
- Critério: sem faixas visíveis no PDF e em tela, ângulo respeitado.
- Risco: baixo; banding em tons escuros.

**R35. Gradiente radial como holofote**
- Objetivo visual: foco de luz atrás de atleta ou título. Uso: capas.
- Comandos: `paint.setFill {gradient:{kind:"radial", stops com opacity, aspect, focal}}`, `transparency.set {blend:"Screen"}`.
- Critério: centro claro, borda transparente (sem anel cinza), foco deslocado quando pedido.
- Risco: opacidade em stop de gradiente radial no PDF.

**R36. Gradiente freeform (campos de cor orgânicos)**
- Objetivo visual: fundo "aurora" com manchas de cor suaves. Uso: fundo de capa.
- Comandos: `paint.setFill {gradient:{kind:"freeform"}}`, `paint.freeform.addPoint {at, color, spread}`, `paint.freeform.addLine`, `paint.freeform.get`.
- Critério: transições suaves, sem emendas, nitidez em zoom.
- Risco: o doc diz que exporta como imagem do campo de cor (raster). Medir ppi efetivo e peso.

**R37. Malha de gradiente (mesh)**
- Objetivo visual: sombreado orgânico de 4x4 pontos em ornamentos. Uso: formas ilustrativas.
- Comandos: `object.mesh.create {rows, cols, appearance}`, `object.mesh.setPointColor {id,index,color}`, `object.mesh.movePoint`, `object.mesh.expand`.
- Critério: sem emendas nem cruzes em 3 leitores; plano B decidido (R36 ou raster) se falhar.
- Risco: conhecido: emendas e cruzes no PDF (auditoria). A receita existe para medir e fixar a regra "não usar mesh" ou "usar malha 2x2".

### Bloco 5: deformação, blend, offset, pathfinder

**R38. Envelope warp em tipografia (arco, bandeira, onda, inchaço)**
- Objetivo visual: título curvado para dar movimento. Uso: títulos de seção.
- Comandos: `object.envelope.makeWithWarp {style:"arc"|"flag"|"wave"|"bulge", bend, h, v}`, `object.envelope.expand`, `object.envelope.release`.
- Critério: letras deformadas suavemente, nitidez vetorial, expandido vira curvas limpas.
- Risco: médio; texto vira contorno.

**R39. Envelope por malha, distorção livre e perspectiva**
- Objetivo visual: título deitado em perspectiva. Uso: capa dinâmica.
- Comandos: `object.envelope.makeWithMesh {rows, cols}`, `object.envelope.setMeshPoint`, `object.distort {corners[4]}`.
- Critério: perspectiva consistente, sem dobras nas letras.
- Risco: médio.

**R40. Blend entre formas (ondas, linhas de velocidade, concêntricos)**
- Objetivo visual: 20 passos entre dois círculos ou curvas dando textura de movimento. Uso: capas, fundos.
- Comandos: `object.blend.make {steps:20|distance, orientation:"page"|"path"}`, `object.blend.options`, `object.blend.replaceSpine`, `object.blend.expand`.
- Critério: passos regulares, cor interpolada suave, spine curva respeitada.
- Risco: médio.

**R41. Offset path e efeito adesivo (sticker)**
- Objetivo visual: contorno externo uniforme em volta de texto ou logo. Uso: capa, selos.
- Comandos: `type.createOutlines`, `object.pathfinder.unite`, `object.path.offsetPath {offset:10, joins:"round"}`.
- Critério: contorno uniforme sem pontas e sem buracos indesejados; furos do "O" tratados.
- Risco: médio; união de glifos pode deixar furos.

**R42. Pathfinder para blocos geométricos**
- Objetivo visual: composições com cortes (divide, minus front, intersect), losangos de fotos. Uso: layouts de grade.
- Comandos: `object.pathfinder.divide|minusFront|intersect|exclude|crop`, `object.compoundPath.make`.
- Critério: resultado sem fatias duplicadas, fills mantidos, sem micro-fendas entre peças vizinhas.
- Risco: médio; fendas (seams) em peças adjacentes.

**R43. Marca-texto (highlighter) e sublinhado irregular**
- Objetivo visual: traço de marca-texto sob palavras-chave. Uso: textos de benefício.
- Comandos: `path.create`, `effect.apply {effect:"stylize.scribble"|"distort.roughen"}`, `brush.new {type:"art"}`, `brush.apply`, `transparency.set {blend:"Multiply"}`.
- Critério: aspecto de pincel, sem pontas quadradas, Multiply sobre o texto.
- Risco: médio.

**R44. Largura variável (swoosh)**
- Objetivo visual: linha com afinamento nas pontas, sensação de velocidade. Uso: rotas, grifos.
- Comandos: `stroke.widthProfile.set {points}`, `stroke.widthPoint.set {t,left,right}`, `stroke.set {profile:"taperEnd"|"lens"}`.
- Critério: perfil preservado no PDF, curva sem degraus.
- Risco: médio.

### Bloco 6: dados, mapas e rotas

**R45. Mapa coroplético (estados com valores)**
- Objetivo visual: mapa do Brasil com estados coloridos por métrica. Uso: alcance geográfico do evento.
- Comandos: `path.create {d}` por estado (Python converte GeoJSON em d), `paint.setFill`, `stroke.set {weight:0.5, join:"round"}`, `text.create`.
- Critério: fronteiras coincidentes sem frestas, legenda lida, 27 estados distinguíveis.
- Risco: baixo (compound path com milhares de subpaths já foi PROVADO).

**R46. Mapa de pontos e de bolhas**
- Objetivo visual: dot map (PROVADO) mais bolhas proporcionais por cidade. Uso: origem do público.
- Comandos: `path.create` (dots), `shape.ellipse` por cidade, `transparency.set {opacity}`.
- Critério: bolhas sobrepostas legíveis, área proporcional ao valor.
- Risco: baixo.

**R47. Linhas de rota (circuito, turnê)**
- Objetivo visual: rota curva entre cidades com pontos e setas. Uso: calendário de etapas.
- Comandos: `path.create {anchors com in e out}`, `stroke.set {weight, cap:"round", dash:[0,12], arrowhead}`, `shape.ellipse` (marcadores), `text.createInPath {mode:"onPath"}` para nomes.
- Critério: pontilhado redondo contínuo, seta alinhada ao fim, marcadores no lugar certo.
- Risco: `dash [0,gap]` com cap round faz pontos (doc); seta em traço pontilhado pode falhar.

**R48. Gráfico nativo (graph.create) contra barras desenhadas**
- Objetivo visual: gráficos de colunas, barras e pizza editáveis. Uso: números de audiência.
- Comandos: `graph.create {type, x,y,width,height, series, categories, rows}`, `graph.design`, `graph.setData`; comparar com `shape.rectangle` por Python.
- Critério: rótulos legíveis, cores da marca aplicadas; comparação lado a lado decide o padrão a adotar.
- Risco: médio; o estilo do gráfico nativo pode ser "de planilha" e destoar do look de estúdio.

**R49. Donut e medidores (progress ring)**
- Objetivo visual: 78% em anel grosso. Uso: KPIs.
- Comandos: `shape.arc`, `shape.ellipse`, `stroke.set {weight, cap:"round", dash, align}`, `object.path.outlineStroke`.
- Critério: arco com ponta redonda, ângulo exato, texto central.
- Risco: baixo.

**R50. Cartões de KPI e numerais gigantes**
- Objetivo visual: "1,2 mi" gigante com rótulo pequeno e régua fina. Uso: página de números.
- Comandos: PROVADOS (`text.create`, `text.setStyle`, `shape.rectangle`) mais `text.setRangeStyle {baselineShift, position:"superscript"}` para a unidade.
- Critério: alinhamento ótico entre numeral e rótulo.
- Risco: baixo.

### Bloco 7: efeitos finos e acabamento

**R51. Sombra projetada em 300 ppi e sombra dura vetorial**
- Objetivo visual: profundidade em cartões e fotos. Uso: cartões de cota.
- Comandos: `effect.apply {effect:"stylize.dropShadow", params}`, `document.rasterEffectsSettings {resolution:300}`; alternativa: cópia deslocada com `object.transform {copy:true}` mais `paint.setFill`.
- Critério: sombra macia sem serrilhado, ou dura com borda limpa; comparar as duas e adotar a vetorial se a raster falhar.
- Risco: conhecido (72 ppi por padrão).

**R52. Brilho (outer glow) e feather**
- Objetivo visual: título com brilho neon, foto com borda suave. Uso: capas.
- Comandos: `effect.apply {effect:"stylize.outerGlow"|"stylize.feather"}`.
- Critério: halo sem corte nas bordas do objeto, resolução 300.
- Risco: médio.

**R53. Extrusão 3D em título**
- Objetivo visual: letras com profundidade. Uso: palavra de capa.
- Comandos: `effect.list` para achar o id do 3D, `effect.apply {effect:<id 3D>}`, `object.expand`.
- Critério: extrusão limpa, exporta no PDF.
- Risco: alto; recurso inicial (cerca de 25% de paridade); usar só se passar.

**R54. Botões, etiquetas e cantos arredondados**
- Objetivo visual: pílulas e cartões com cantos consistentes. Uso: cotas e labels.
- Comandos: `shape.rectangle {radius}`, `object.setLiveShape`, `effect.apply {effect:"stylize.roundCorners"}`.
- Critério: raio uniforme, traço sem cortes.
- Risco: baixo.

**R55. Estilos gráficos e cor global (rebrand por patrocinador)**
- Objetivo visual: trocar a paleta do kit inteiro para cada prospect em um comando. Uso: produção em série dos kits.
- Comandos: `swatch.new {name, color}`, `paint.setFill {swatch}`, `swatch.edit`, `recolor.apply {map, includeImages, includePatterns}`, `graphicStyle.new|apply|redefine`.
- Critério: mudar o swatch recolore todas as ocorrências, inclusive padrão e imagem quando pedido.
- Risco: médio; é onde o ganho de produtividade é maior.

**R56. Parede de logos de patrocinadores**
- Objetivo visual: grade uniforme de logos em peso visual igual, em branco ou preto. Uso: página de parceiros.
- Comandos: `file.place` x N, `object.setBounds {reference}` com caixa máxima, `object.align`, `object.distribute`, `edit.colors.toGrayscale` ou `edit.colors.invert`, `recolor.apply`.
- Critério: logos centrados, mesma área ótica, versão monocromática legível.
- Risco: médio; logo com fundo branco no PNG.

### Bloco 8: PDF e produção

**R57. Exportação PDF/X-4 (gráfica)**
- Objetivo visual: PDF para impressão com sangria e cores CMYK. Uso: versão impressa do kit.
- Comandos: `file.documentColorMode {mode:"cmyk"}`, `swatch.setSpot`, `document.exportPdf {standard:"pdfX4", marks, bleed, compression}`, `document.pdfSettings`, `document.pdfInfo`.
- Critério: perfil de saída embutido, TrimBox e BleedBox corretas, fontes embutidas, transparência mantida (X-4); X-1a e X-3 achatam transparência (checar mesh, opacity mask e grão).
- Risco: médio.

**R58. PDF leve para e-mail**
- Objetivo visual: kit abaixo de 10 MB sem perda visível. Uso: envio ao prospect.
- Comandos: `document.exportPdf {compression{color{downsample:"bicubic", ppi:150, abovePpi:225, compression:"jpeg", quality:"high"}}, preserveEditing:false, thumbnails:false, fastWebView:true}`.
- Critério: tamanho final anotado por página; foto sem artefato; texto vetorial intacto.
- Risco: `preserveEditing` vem ligado no preset padrão e embute o documento nativo (infla o PDF).

**R59. Camadas, nomes de objeto e organização**
- Objetivo visual: arquivo fonte limpo para outros editarem. Uso: biblioteca de templates.
- Comandos: `layer.new`, `layer.setProps`, `object.setProps {name}`, `layer.collectInNew`, `document.exportPdf {createLayers:true}`.
- Critério: camadas nomeadas, PDF com camadas opcionais.
- Risco: baixo.

**R60. Páginas na dimensão final (1440 x 810) sem escalar**
- Objetivo visual: eliminar o passo "criar em 1920 x 1080 e escalar". Uso: pipeline.
- Comandos: `file.new {width:1440, height:810}`, `artboard.new`, `artboard.setProps {scaleArt}`, `artboard.rearrange`.
- Critério: traço e tipografia nos tamanhos pretendidos (sem escalar traço), todas as páginas alinhadas.
- Risco: baixo; o `object.scale` atual mexe em traços (`strokes`): conferir.

**R61. Marcas de corte e sangria**
- Objetivo visual: versão para gráfica com crop marks.
- Comandos: `object.createTrimMarks {style:"roman", offset:9}` ou `document.exportPdf {marks, bleed}`.
- Critério: marcas fora da área de sangria, 0.25 pt.
- Risco: baixo.

**R62. Fita adesiva, etiquetas e papel rotacionados**
- Objetivo visual: elementos de collage (tape, polaroid, post-it) com leve rotação e sombra dura. Uso: páginas de bastidores.
- Comandos: `shape.rectangle`, `object.transform {matrix de rotação}`, `transparency.set {opacity:70}`, `effect.apply {effect:"stylize.dropShadow"}`.
- Critério: rotação limpa, sombra consistente, sem recorte do efeito.
- Risco: baixo.

**R63. Cor de marca em RGB para tela e CMYK para impressão**
- Objetivo visual: amarelo da marca igual em tela e impressão. Uso: validação de cor.
- Comandos: `color.convert {color, to:"cmyk"}`, `swatch.new {mode:"cmyk"}`, `object.convertDocumentColorMode`.
- Critério: delta E reportado abaixo de 6 no amarelo, aviso de fora de gama tratado.
- Risco: médio; amarelo e laranja saem da gama.

**R64. Teste de regressão do kit inteiro**
- Objetivo visual: rodar todas as receitas aprovadas como suíte e comparar PDFs por imagem a cada versão do VectorCraft. Uso: segurança contra regressão.
- Comandos: roteiro Python que chama as receitas, `document.exportPdf`, `pdftoppm`, diff de pixels.
- Critério: diferença abaixo de 0,5% por página em relação ao PDF aprovado.
- Risco: baixo, alto valor.

---

## Ordem de execução recomendada

1. Maior impacto e menor custo: R01, R03, R23, R29, R21, R51, R08, R34, R35, R57 e R58.
2. Risco conhecido, para decidir a regra de uso: R37 (mesh), R36 (freeform), R08 (grão), R53 (3D).
3. Ornamentos e dados: R40 a R49.
4. Fechar com R55 e R64 (produção em série e regressão).

Cada receita aprovada vira uma função em `lib.py` com nome, parâmetros e PNG de referência, e uma linha na tabela "aprovada / aprovada com ressalva / reprovada, plano B".
