# R17. Texto em mix-blend sobre foto

Status: FUNCIONA

## Sequência que funcionou
1. `file.new {width:1440,height:810,units:"Points"}`
2. foto: `file.place {path, link:false}` + `object.setBounds {reference:0}` + retângulo + `object.clippingMask.make` (corte "cover")
3. `text.create {x,y(baseline),text,font:"Helvetica Neue",style:"Condensed Black",size:260,color:"#F3E3B5"}`
4. `transparency.set {ids:[texto], blend:"Overlay"}` (ou `"Multiply"`, `"SoftLight"`; aceita `opacity` junto)
5. `document.exportPdf {path, preserveEditing:false}`

## Veredito visual
Nível de estúdio com ressalva de uso. O PDF grava o blend nativo (`/BM /Overlay`, `/Multiply`, `/SoftLight` confirmados no arquivo), sem rasterizar o texto. Poppler (pdftoppm) e Cairo (pdftocairo) renderizam igual a olho nu (diferença média 3/255, só reamostragem da foto).

## Defeitos e armadilhas
- Legibilidade depende da foto: Multiply some em área escura (camisa preta), Overlay com creme só aparece em área clara. Usar sobre foto com zona clara, ou com tarja de cor por baixo.
- Os títulos mantêm fonte embutida (pdffonts: HelveticaNeue-CondensedBlack e Bold, emb=yes).
- Preto no Multiply é preto; o "efeito" só aparece em cor média.

## O que rasteriza
Só a foto (JPEG, 47 ppi efetivo no 1440 pt; fonte f1.jpg 935x1280, é limite do acervo). Texto e blend ficam vetoriais.
