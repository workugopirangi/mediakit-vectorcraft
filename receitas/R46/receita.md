# R46. Mapa de pontos e de bolhas

Status: FUNCIONA

## Comandos que funcionaram
- Contorno de SP: `sp.json` (IBGE, MultiPolygon, 612 pontos) projetado com x = cos(-22,5 graus), `path.create {d}` com todos os anéis, `paint.setFill {color:"#17486a"}` + `paint.setStroke` + `stroke.set {weight:1}`.
- Mapa de pontos: Python cria grade de 7 pt, testa ponto-no-polígono (anéis internos como furos) e monta UM único `path.create` com 3.476 círculos (`M x y a r r 0 1 0 2r 0 a r r 0 1 0 -2r 0 Z`, r = 2,2). Um objeto só, não 3.476.
- Bolhas: `shape.ellipse` por cidade com raio = sqrt(valor) x 5,2 (ÁREA proporcional ao valor), `paint.setFill {color:"#E9603A"}`, `paint.setStroke {color:"#FFFFFF"}`, `stroke.set {weight:0.8}`, `transparency.set {ids:[id], opacity:70}`.

## Veredito
Qualidade de estúdio nas duas técnicas. Pontos perfeitos em zoom de 300 ppi (círculos redondos, espaçamento regular). Bolhas sobrepostas ficam legíveis por causa da opacidade 70 e do anel branco fino. Vetor puro: PDF 147 KB, 0 imagens, 1 objeto para 3.476 pontos.

## Defeitos e armadilhas
- Meu layout ficou imperfeito: a cauda oeste do mapa de pontos encosta no mapa de bolhas, e os rótulos "Ubatuba" e "São José dos Campos" saíram mal posicionados (o cálculo automático de lado do rótulo é grosseiro, cidades do litoral norte se amontoam). Para o kit final posicionar rótulos manualmente e usar linha de chamada.
- Valores das bolhas são ILUSTRATIVOS (não há dado real por cidade nos números fornecidos).
- Cidades próximas (SP, Guarulhos, Santos) sobrepõem muito com escala 5,2; reduzir a escala ou ordenar maior primeiro (maior atrás) para o menor não ficar escondido.
- Um path de milhares de subpaths exporta sem problema (consistente com o PROVADO do plano).
