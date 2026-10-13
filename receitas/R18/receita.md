# R18. Texto em contornos como trava de segurança

Status: FUNCIONA

## Sequência que funcionou
1. Montar a página com `text.create` (4 fontes: Helvetica Neue Condensed Black, Avenir Next Demi Bold, Didot Bold, Futura Medium; acentos e uma estrela).
2. (opcional) `text.fonts {selectionOnly:false}` para ver `missingGlyphs`.
3. `select.set {ids:[todos os textos]}` e `type.createOutlines {}` (devolve `{ids}` de grupos, um por texto).
4. `document.exportPdf {path, preserveEditing:false}`.

## Prova
- `pdffonts` do PDF final: ZERO fontes (lista vazia). Antes dos contornos: 5 fontes, entre elas `Inter-Regular`, que entrou sozinha por causa da estrela que o Didot não tem.
- Depois do `createOutlines`, `text.fonts` devolve `[]` (nenhum texto vivo).
- Comparação pixel a pixel a 200 ppi, antes x depois: 0,9 % dos pixels diferem, só em borda de letra (suavização; o poppler aplica hinting em texto vivo e não em curva). Mesma posição, mesmo desenho. A estrela (glifo da Inter) vira curva e fica idêntica ao que se via.

## Veredito visual
Estúdio. Letras idênticas, acentos preservados (ç ã õ é ü), kerning mantido.

## Armadilhas
- Perde edição: fazer só na cópia final (o texto vira grupos de compound paths, um por glifo).
- Contorna também o glifo substituto: se a estrela caiu em Inter, o contorno é de Inter (visualmente ok, mas não é a estrela da marca; ver R19).
- Texto cheio de glifos aumenta o PDF (aqui o PDF ficou com 408 KB, dos quais 364 KB são a foto).
