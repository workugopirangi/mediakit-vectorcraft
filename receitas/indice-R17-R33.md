| ID | Receita | Status | Veredito |
|---|---|---|---|
| R17 | Texto em mix-blend sobre foto | FUNCIONA | Blend nativo no PDF (/BM Overlay, Multiply, SoftLight), poppler e cairo iguais; legibilidade depende da foto. |
| R18 | Texto em contornos como trava de segurança | FUNCIONA | pdffonts vazio, 0,9 % de pixels diferentes (só borda); perde edição, só na cópia final. |
| R19 | Auditoria de glifos ausentes | FUNCIONA | text.fonts só conta por fonte; com laço de sondas acha texto e caractere, e a estrela vira shape.star. |
| R20 | Texto em caminho livre | FUNCIONA | Arco, onda de 3 segmentos e S apertado sem sobreposição de letras; texto segue editável e embutido. |
| R21 | Selo circular com texto em volta | FUNCIONA | Texto de baixo exige caminho anti-horário (flip não funciona em círculo); centralização calculada; zoom limpo e vetorial. |
| R22 | Selo dentado e sunburst | FUNCIONA | star de 24 pontas + roundCorners + offsetPath dão medalha limpa e vetorial; anel interno com segunda star fica feio. |
| R23 | Padrão a partir de motivo IA | PARCIAL | pattern.make com PNG e repeat.grid dão fundo de estúdio, mas o PDF expande em imagens (zero PatternType) e há emenda de 1 px em 800 dpi no tile contínuo; encolher o PNG antes (2,5 MB para 362 KB). |
| R24 | Repetição de vetor puro (grade) | FUNCIONA | repeat.grid + gridType brickByRow + expand: 1.500 instâncias sem duplicata, 27 KB e 0,02 s de export. |
| R25 | Radial repeat | FUNCIONA | 24 raios com simetria exata de 15 graus medida por rotação de imagem; exige center e radius explícitos (radius 0 não desenha). |
| R26 | Mirror repeat | FUNCIONA | Espelho exato (0 pixels de diferença); traços que encontram o eixo precisam de cap redondo, senão fica um entalhe em V em zoom. |
| R27 | Símbolos e confete | PARCIAL | symbol.spray põe 1 instância por ponto (radius e density não espalham, scale fixo); confete natural exige symbol.place + object.rotate/scale por instância. |
| R28 | Espiral, grade polar, malha retangular | FUNCIONA | Geometria exata (rows/columns contam divisórias); traço abaixo de 0,5 pt é preso em 1 pixel por poppler, cairo e CoreGraphics, usar 0,5 pt ou mais. |
| R29 | Halftone vetorial em foto | FUNCIONA | Pontos nítidos e 100 % vetor (7 mil a 42 mil pontos, 5 MB em três painéis); em fundo escuro é obrigatório invert:true. |
| R30 | Halftone CMYK colorido | FUNCIONA | 4 telas com Multiply nativo, rosetas corretas e iguais em poppler e cairo; fundo branco obrigatório e ~12 MB por página cheia (teto de pontos recusa 18 lpi). |
| R31 | Halftone raster por efeito | FUNCIONA | Só presta com rasterEffectsSettings 300 e maxRadius ~2,6 (padrão sai 72 ppi e dots de 8 pt); em doc RGB vira neon aditivo, em CMYK parece tinta; ~4 a 5,6 MB por painel, sem vantagem de peso sobre o vetorial. |
| R32 | Image Trace (foto posterizada e logo) | PARCIAL | Logo AME sai limpo em Color 2 cores (37 caminhos, 5,6 mil âncoras, cor aproximada); Flat Logo é recusado/inútil; foto posterizada sai em degraus com 33 a 41 mil âncoras e paleta fora da marca. |
| R33 | Mosaico de quadrados | FUNCIONA | 40x53 tiles em 0,03 s, cor média correta (erro médio 4/255), grade exata, sem fio entre tiles com espaço 0, 272 KB. |
