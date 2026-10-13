# R45. Mapa coroplético (27 estados)

Status: FUNCIONA

## Fonte e método
- Malha IBGE (pública): `https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson&intrarregiao=UF&qualidade=intermediaria` (27 features, `codarea` = código IBGE da UF, 251 KB). Nomes e siglas: `https://servicodados.ibge.gov.br/api/v1/localidades/estados` (o /api/v3/ dessa rota não existe, deu vazio).
- Arquivos baixados em `receitas/_s34/geo/`.
- Python projeta lon/lat com escala x = cos(-14 graus) (equiretangular, boa para o Brasil) e monta um `d` por estado (todos os anéis de todos os polígonos num único `path.create`).
```
path.create {d:"M x y L x y ... Z M ... Z"}    # um por UF, 27 chamadas, 0,26 s no total
paint.setFill {color}  paint.setStroke {color: cor do fundo}  stroke.set {weight:0.6, join:"round"}
text.create {...}      # siglas e legenda
```

## Veredito
Qualidade de estúdio: litoral detalhado, ilhas e exclaves (DF, Fernando de Noronha ausente na malha "intermediaria"), 27 UFs distinguíveis com 5 classes de cor. Vetor puro: PDF de 142 KB, 0 imagens, texto com fonte embutida.

## Defeitos e armadilhas
- FRESTAS: com `stroke:none` (mapa da direita, fundo preto) as fronteiras entre estados aparecem como fio escuro de antialiasing em sips/macOS (bem visível ampliado 4x, mesmo entre estados da mesma cor) e como fio vermelho muito tênue em pdftoppm a 400 ppi. Com traço de 0,6 pt na cor do fundo as fronteiras ficam intencionais e limpas. Regra: sempre traço fino na cor do fundo (ou cor do estado vizinho mais clara), ou colocar uma silhueta unida (pathfinder.unite) abaixo.
- Os valores usados são ILUSTRATIVOS (sorteio com semente 3, SP=100): não há número real por estado nos dados fornecidos. Não publicar sem dados reais.
- Rótulos de sigla precisam de cor condicional por contraste (preto sobre ouro/menta, branco sobre mar/coral); centroide simples sai fora de estados côncavos (RJ/GO), então para rótulo final usar ponto manual.
- Malha "intermediaria" simplifica o litoral; para impressão grande usar `qualidade=maxima` (não testei, arquivo maior).
