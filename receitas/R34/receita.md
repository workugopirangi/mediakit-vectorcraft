# R34. Gradiente linear de marca em bloco e em fundo

Status: FUNCIONA

## Comandos que funcionaram
- Fundo e blocos: `shape.rectangle` + `select.set {ids}` + `paint.setFill {gradient:{kind:"linear", angle:90, stops:[{offset:0,color:"#14507A"},{offset:1,color:"#0F3550"}]}}` + `paint.setStroke {none:true}`.
- 3 stops com `midpoint` (ex.: `{offset:0.5,color:"#F08A4B",midpoint:0.3}`) funciona.
- Vetor explícito: `paint.setGradientGeom {ids:[id], start:[80,730], end:[1360,730], stroke:false}`.

## Veredito
Qualidade de estúdio. No PDF vira shading axial (`/ShadingType 2`), vetor puro: `pdfimages -list` não lista imagem nenhuma, arquivo da página de teste com 4 gradientes e textos = 18,6 KB. Ângulos 0, 45 e 90 respeitados. Conferido no pdftoppm e no sips (macOS): iguais.

## Defeitos e armadilhas
- Convenção do ângulo: com angle 90 o stop 0 fica na BASE e o último stop no topo (anti-horário, como Illustrator). Angle 0 vai da esquerda para a direita. Confirmado no render.
- `paint.setGradientGeom` sem `stroke:false` num objeto que tem traço none CRIOU um gradiente de traço branco para preto (borda visível). Sempre passar `stroke:false`.
- O sips renderiza as cores levemente mais dessaturadas que o pdftoppm (perfil de cor do macOS), não é defeito do PDF.
- Banding: gradiente escuro a escuro (#0B0B0C a #26262A) tem só ~27 níveis em 300 pt, limite de 8 bits, não do VectorCraft. Não apareceu faixa visível no zoom de 150 ppi nos gradientes claros.
- Nada rasteriza.
