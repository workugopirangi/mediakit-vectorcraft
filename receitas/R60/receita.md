# R60. Páginas na dimensão final (1440 x 810) sem escalar

Status: FUNCIONA

## Comandos que funcionaram
- `file.new {width:1440, height:810, units:"Points"}` (1 prancheta).
- Mais pranchetas do mesmo tamanho: `artboard.new {x:1540, y:0, width:1440, height:810, name:"Pagina 2"}` (x = largura + 100 de vão; sem x ele coloca à direita da última).
- Desenhar em coordenadas globais: a página N começa em x = N x 1540; todo `shape.rectangle`/`text.create` soma esse deslocamento.
- Alinhar/reorganizar: `artboard.rearrange {layout:"row", spacing:100}` retornou `{artboards:3, columns:3, rows:1}`. Sem `moveArtwork:true` a arte NÃO acompanha a prancheta; como o vão já era 100 nada se mexeu, mas ao usar com espaçamento diferente é preciso passar `moveArtwork:true` (não testado).
- Exportar tudo: `document.exportPdf {path, preserveEditing:false}` gera uma página por prancheta. `pdfinfo`: 3 páginas, todas 1440 x 810 pts.

## Traço e escala (medido com document.inspect, retângulo com traço de 10 pt escalado em 150%)
| Chamada | strokeWidth depois |
|---|---|
| `object.scale {sx:150, strokes:false}` | 10 |
| `object.scale {sx:150, strokes:true}` | 15 |
| `object.scale {sx:150}` (preferência padrão) | 10 |
| `object.setBounds {width:300, height:150, reference:0}` | 10 |
Conclusão: com a preferência padrão atual o traço NÃO escala; para escalar é preciso `strokes:true`. Não vi a preferência alterada por script. A suspeita do plano (`object.scale` mexe em traços) não se confirmou com o padrão; passe `strokes:false` explícito para não depender da preferência.

## Prova
- Texto 28 pt e 120 pt e traço de 4 pt saem nos tamanhos pedidos (conferi no preview das 3 páginas); fontes embutidas; PDF de 13 KB.

## Não testado
- `artboard.setProps {scaleArt:true}` (redimensionar prancheta com a arte).
- Texto em área (`typeAreas`) ao escalar.

## Veredito
Fluxo "criar já em 1440 x 810" funciona e elimina o escalonamento 1920 x 1080 para 75%.

## O que rasteriza
Nada.
