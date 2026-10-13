# R48. Gráfico nativo (graph.create) contra barras desenhadas

Status: PARCIAL (nativo funciona e é recolorível, mas tem aparência de planilha; barras desenhadas vencem)

## Comandos que funcionaram (nativo)
```
graph.create {type:"column", x:60, y:130, width:600, height:520, series:["jan/2026","set/2026"],
              categories:["Instagram (mil)","TV AME (inscritos/10)"], rows:[[113.4,204.8],[243,518]]} -> {id}
graph.setType {id, columnWidth:80, clusterWidth:70, legend:true, ticks:4, axisMin:0}
graph.setData {id, csv:",jan,set\nInstagram,113400,204800\nTV,2430,5180"}   (sem csv, lê os dados atuais)
pizza: graph.create {type:"pie", series:["turistas","moradores"], rows:[[52,48]]}   (uma linha com a série = fatia; com categorias separadas saiu vazio)
```
Recolorir: `document.inspect {depth:6}` lista Paths com fill #000000 (1ª série) e #8c8c8c (2ª); `select.set {ids:[pathId]}` + `paint.setFill {color}` pinta a série mantendo o gráfico. Textos (kind "Type", ids maiores que o do gráfico): `select.set {ids}` + `paint.setFill {color:"#FFFFFF"}`.

## Veredito
- Funciona: colunas, barras e pizza vetoriais, editáveis (graph.setData), séries recoloridas com as cores da marca e rótulos em branco no fundo preto. PDF sem imagem.
- Mas o resultado visual é "de planilha": fonte padrão Source Sans 3 (aparece no pdffonts) com corpo pequeno (cerca de 12 pt), eixo com traço fino preto (sumia no fundo escuro até pintar), sem valores acima das colunas, colunas sem canto arredondado, legenda com quadradinhos minúsculos, pizza com padrão preto e cinza e legenda ilegível. Não destoa só em cor: falta hierarquia (número grande, destaque do crescimento).
- Barras desenhadas por Python (retângulos com radius 6, valores grandes em Bold 40, linha de base, rótulos Medium 24, delta "+80,6%" em Condensed Black) saem claramente superiores para o kit e são controle total.

## Padrão decidido
Usar barras desenhadas para os números de audiência do kit; reservar `graph.create` para quando alguém precisar editar os dados depois (gráfico de apoio, anexo), sempre recolorindo via inspect.

## Gotchas
- `paint.setFill` com o gráfico selecionado pinta tudo igual (as duas séries ficaram amarelas): pintar por série.
- `graph.setType` com `type:"bar"` troca para barras horizontais (testei, funciona), mas eixos e rótulos longos saem cortados fora da página (rótulo "(visualizações)" cortado à esquerda do gráfico).
- A pizza com `categories` separadas gerou círculos vazios; usar uma linha com 1 série por fatia.
- Rótulo de categoria longo estoura a área do gráfico.
- Cálculo conferido: 204.800 / 113.400 = +80,6% (usado no teste desenhado). TV AME 2.430 para 5.180 (+113,2%, não mostrado; no nativo plotei x10 só para caber na escala, o que é feio: nunca misturar escalas num gráfico só).
