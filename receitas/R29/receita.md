# R29. Halftone vetorial em foto (pontos)

Status: FUNCIONA

## Sequência que funcionou (R29/teste.py)
1. `file.place {path, link:false}` + `object.setBounds {x,y,width,height,reference:0}` (foto 935x1280 em caixa 420x575 pt).
2. `select.set {ids:[foto]}`
3. `object.vectorHalftone {shape:"circle", frequency:12|20|30, angle:45, mode:"mono", color:"#D4A64A", clip:true, invert:true}` devolve `{id, dots}`.
4. Exportar normalmente.

## Descoberta importante: `invert`
O padrão (`invert:false`) faz o ponto crescer com a ESCURIDÃO da foto (lógica de impressão sobre papel branco). Sobre fundo escuro isso sai em NEGATIVO (céu some, árvore e sombra acendem). Em fundo escuro usar `invert:true`; em fundo claro, `invert:false`. Primeira versão sem invert saiu negativa, a segunda (invert:true) lê como foto positiva.

## Provas medidas
- Pontos: 12 lpi = 7.026 pontos, 20 lpi = 19.190, 30 lpi = 42.628. (frequency em linhas por polegada: 42 mil pontos em 420x575 pt confere com passo de 2,4 pt.)
- Tempo do comando: 0,12 s, 0,21 s e 0,33 s. Render do PDF com ~69 mil pontos a 50 ppi: 1,2 s.
- Tamanho do PDF: 5,17 MB com os três painéis (69 mil pontos, cerca de 75 bytes por ponto). Meta do plano era abaixo de 20 MB: ok. Um painel de 30 lpi sozinho pesa ~3 MB.
- `pdfimages -list`: nenhuma imagem no PDF (a foto some, só ficam os pontos); `/BM` ausente (sem blend). Fontes: Helvetica Neue Bold.
- Zoom 300 ppi: círculos nítidos, tamanhos variam suave de ponto minúsculo a ponto que se funde, nenhum artefato, recorte limpo na borda da foto.

## Veredito visual
Estúdio. Look de impresso verdadeiro; 20 lpi é o melhor equilíbrio de leitura (rostos reconhecíveis); 12 lpi é gráfico e grosso (bom para fundo); 30 lpi mais fotográfico, 3 MB por painel.

## Defeitos e armadilhas
- Foto de baixo contraste (céu estourado) vira massa sólida nos realces: preparar a foto (contraste/levels) antes, ou usar uma foto com mais variação.
- Cada painel é UMA cor; para duas cores, ver R30 (CMYK).
- 30 lpi e acima em página inteira (1440x810) passam de 10 MB: limitar a área ou a frequência.
