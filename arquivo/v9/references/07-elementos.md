# Elementos: patterns, objetos e grafismos próprios do evento

Por que existem: com o mesmo tema e os mesmos arquétipos, dois kits saíam iguais. Cada evento ganha agora textura e
objetos derivados do próprio território e da identidade (a pena da asa da Sprint, a serra e o mar de Ubatuba),
gerados pelo GPT Image (rota Codex, cota do ChatGPT do Ugo) com fundo transparente e aplicados por cima da página.

## 1. Gerar e preparar

```
bash pipeline/elementos.sh <pasta-do-kit> <id> <tipo> --descricao-de <arquivo com a descrição em inglês> \
     --estilo "<estilo da família>" --paleta "#D09050,#281805" --aspecto quadrado|largo|alto|faixa \
     [--ref <png da âncora>] [--familia <id>] [--motivo <id>] [--luz esquerda|direita|cima] \
     [--material metal-escovado|ouro|couro|borracha|tecido|vidro-fosco|plastico-fosco|madeira|papel|grama]
     # tipo: objeto | ilustracao | pictograma | textura | pattern | adesivo  (ornamento = objeto; a chamada da v1 continua valendo)
     # --descricao-de - lê a descrição da entrada padrão (heredoc <<'EOT'); a descrição entre aspas ainda roda, com aviso
     # --material só vale para objeto: acrescenta a linha "Material/render" ao prompt (references/03 §7)
ELEMENTOS_DRY=1 bash pipeline/elementos.sh ...                              # mostra prompt e comando exato; não gasta cota nem grava nada
python pipeline/padrao.py texto acervo/elementos/<id>.png                   # OCR: reprova (sai 1) se a IA escreveu alguma coisa
python pipeline/padrao.py checar acervo/elementos/<id>.png                 # pattern: costura (limite 0,7) + mosaico 2x2
python pipeline/padrao.py tornar-seamless <id>.png <id>-seamless.png       # se o checar reprovar ou passar de 0,5
python pipeline/padrao.py variantes <id>-seamless.png --paleta "#D4A64A,#0B0B0C" --saida acervo/elementos
python pipeline/padrao.py folha acervo/elementos/elementos-<kit>.json acervo/elementos/folha.png
python pipeline/padrao.py preparar_uso <png> <largura-de-uso-px> <saida>   # corta no alfa e reduz a 2x o uso; imprime o sha256
```

- A descrição vem de arquivo (12/10/2026): ela traz campos do evento, e um `$(...)` ou uma crase entre aspas duplas
  rodaria no shell de quem chama antes de chegar ao script. Arquivo ausente ou vazio sai com 66, sem chamar o Codex.
- O prompt sai do `elementos_prompt.py` (um modelo por tipo, nos rótulos do guia de prompt do próprio gerador), nunca
  escrito à mão. A paleta entra por NOME de cor (tabela curada, vizinho mais próximo em CIEDE2000): `#D4A64A` vira
  "antique gold", `#281805` vira "near-black brown". Hex que aparecer no estilo ou na descrição também é trocado.
- Ao lado do PNG fica `<id>.meta.json`: tipo, família, motivo, estilo, paleta (hex e nome), aspecto, âncora e sha256
  dela, rota, sha256, alfa medido, o que o Codex declarou, quantas gerações o log de eventos do Codex registrou para
  aquele id (`geracoes_medidas`) e a data.
- Uma geração por imagem. `elementos.sh` não regera se `<id>.bruto.png` existe e proíbe o Codex de regerar ou de editar
  o PNG com código. Defeitos vêm listados em `.codex-<id>.log`; regerar é decisão do Ugo.
- **Transparência (medida em 09/10/2026, 6 de 6 gerações):** o GPT Image pela rota Codex devolve PNG RGBA com alfa real
  quando o prompt pede fundo transparente (rota `codex-alfa`). As rotas de reserva continuam no script e só disparam se
  `padrao.py alfa` medir que não veio alfa: pattern → `codex-branco+chroma` (`padrao.py separar`), ornamento →
  `codex-cinza+rembg` (`recortar.py --classe produto`). A rota usada fica em `elementos.log` e no campo `rota`.
- **Seamless não vem pronto:** 2 de 2 patterns pedidos como seamless saíram com costura visível (índice 0,93 e 0,90).
  Sempre `checar`; o `tornar-seamless` padrão (`costurar`, corte de menor erro) não deixa fantasma, mas pode cortar
  traço seco onde o desenho é denso. Olhe o mosaico.

## 2. Pattern × ornamento

| | Pattern | Ornamento |
|---|---|---|
| O que é | tile repetido, traço de 1 ou 2 tons | um objeto isolado, fotográfico |
| Para quê | textura de fundo que carrega a identidade (divisor, divisor de cotas, território) | acento narrativo perto do título ou do número (capa, cota principal, território) |
| Variante usada | `-traco` (alfa só nas linhas, cor da marca) na maioria; `-chapado` para silhueta sólida; `-tingido` para tom sobre tom | o próprio PNG; `tratar.py sombra` se pousar numa superfície |
| Camada | `sob-veu` em página com cena (o véu tinge por cima); `atras` em faixa de borda ou atrás de placa chapada | `frente` em geral; `atras` quando cruza a divisa painel/cena |
| Opacidade típica | .08 a .18 | 1 |

## 3. Limites (o QA e a revisão cobram)

- Por página, no máximo **1 herói, 1 apoio e 1 pattern** (constantes não contam). `ornamento` é o nome antigo de herói.
- Pattern **nunca sob texto de corpo sem véu**: onde houver corpo de 24 px, o pattern fica atrás do véu ou fora do painel.
- Elemento **nunca cobre texto**: o `qa_geometria.py` mede a máscara alfa real (§5) contra cada LINHA protegida e reprova
  acima de 4% de uma linha de corpo, preço, número ou micro, acima de 8% de um título, e qualquer toque em logo,
  etiqueta ou crédito. Dois elementos sobrepostos em mais de 10% da menor área também reprovam.
- Ornamento conta junto com `objetos[]` na regra de 1 objeto recortado por página: não ponha ornamento e objeto
  recortado na mesma página sem motivo declarado.
- Sem texto, sem logo de marca, sem pessoas (o prompt proíbe; a folha confere). `padrao.py texto` reprova o PNG em que o
  OCR lê palavra de 3+ caracteres com confiança >= 75 (ou de 2 com >= 90 em 3 passadas). Ele pega texto chapado e
  legível; letra sobre textura carregada pode escapar, então a folha continua sendo olhada.
- **Blends permitidos:** só os nativos do PDF, `normal`, `multiply`, `screen`, `soft-light` (CSS `mix-blend-mode`).
  Nada de `filter` CSS: rasteriza a página no PDF e perde o texto (aprendizado 12).

## 4. Contrato JSON (`mediakit.json` → `elementos[]`)

Os nomes abaixo são fixos: as frentes de layout e de render dependem deles.

```json
{"id": "penas-asa", "arquivo": "acervo/elementos/penas-asa-traco.png", "papel": "pattern|constante|heroi|apoio",
 "formato": "png|svg", "paginas": ["capa", "divisor", "cota:Naming"], "x": 1500, "y": 120, "w": 520, "rot": -12,
 "camada": "sob-veu|atras|frente", "opacidade": 0.18, "blend": "normal|multiply|screen|soft-light",
 "escala_tile": 360, "gerado": true, "rota": "codex-alfa|codex-cinza+rembg",
 "prompt": "acervo/elementos/penas-asa.prompt.txt"}
```

| Campo | Regra |
|---|---|
| `id` | único no kit; é o nome base dos arquivos |
| `arquivo` | relativo à pasta do kit; PNG com alfa (svg: `null`, o grafismo é gerado no render) |
| `papel` | `pattern`, `constante`, `heroi`, `apoio` ou `ornamento` (= herói, nome antigo). Contrato completo em `schema/elementos.schema.json` |
| `paginas` | AJUSTE MANUAL: lista de rótulos (`capa`, `manifesto`, `projecao`, `publico`, `historico_logos`, `territorio`, `prova`, `divisor`, `divisor_cotas`, `contato`, `cota:<nome>`, `ativo:<n>` ou a variante, `cota:b`) ou `"todas"`. Sem `paginas`, o planejador decide |
| `x`, `y`, `w` | AJUSTE MANUAL: px na página 1920×1080 (canto superior esquerdo e largura da imagem INTEIRA). Vale como foi escrito, sem desviar de nada: o `qa_geometria.py` julga. Sem eles, os encaixes decidem. No vertical não valem (lá decidem os encaixes) |
| `rot` | graus, sentido horário positivo |
| `camada` | `sob-veu` (logo depois da cena, o véu pinta por cima), `atras` (sobre o véu, sob o texto) ou `frente` (sobre o texto, sob etiqueta, fio, logo e crédito) |
| `opacidade` | 0 a 1 |
| `blend` | um dos quatro nativos acima |
| `escala_tile` | só pattern: lado do tile em px da página |
| `gerado` | `true` para tudo que veio do gerador de imagem |
| `rota` | `codex-alfa`, `codex-branco+chroma` ou `codex-cinza+rembg` |
| `prompt` | caminho do `.prompt.txt` ao lado da imagem |

Cada kit guarda as entradas propostas em `acervo/elementos/elementos-<kit>.json` (lista); quem integra copia para
`mediakit.json` → `elementos[]`. Os campos novos do sistema de elementos (papel heroi/apoio/constante, tipo, formato
png|svg, família, motivo, params, kit de origem, exclusividade) estão em `references/08-sistema-elementos.md` e no
`schema/elementos.schema.json`.

## 5. Como o render põe o elemento na página (Frente A: `camadas.py`, `encaixes.py`, `qa_geometria.py`)

Liga sozinho quando o kit tem `elementos` ou `sistema_elementos`; sem isso o render é byte a byte o de antes (o
`tema/36-elementos.css` só entra no HTML de kit com elementos).

1. **Mede antes de pôr.** O render gera a página sem elementos, roda o data-fit e mede no DOM as caixas protegidas por
   LINHA de texto (`Range.getClientRects`, não o bloco inteiro; a faixa diagonal girada vira pedaços de 48 px), mais
   logo, crédito, etiqueta e fio, os blocos de conteúdo (card, caixa, direitos, gráfico), a cena e os painéis chapados.
2. **Planeja.** Receita declarada em `sistema_elementos.receitas`: `plano_elementos.planejar` (Frente C) diz quais
   elementos vão em cada página; o render manda, além do rótulo, todos os nomes da página em `rotulos` (ex.:
   `cota:Naming`), senão o `paginas` manual de um elemento não acha a página. Kit ou receita sem sistema (kit antigo,
   exemplo `receitas-teste`): o modo manual `_plano_minimo` do `camadas.py` (ajuste manual como antes, pattern pela
   receita). Constante entra com id `constante-<tipo>` (`constante-<tipo>-2` para a segunda do mesmo tipo); o grão é
   do tema (`.pagina::after`) e sai do plano antes do encaixe. O selo constante nasce no diâmetro do canto de selo
   do catálogo (texto vivo só encolhe 25%); `params` da constante (ex.: `recorte` do símbolo no logo) vão ao
   `grafismos.gerar`.
3. **Encaixa.** `pipeline/encaixes.json` tem, por rótulo de variante (`capa:c`, `cota:b`, `ativo:diagonal`,
   `vertical:capa`...), as REGRAS de encaixe: `canto`, `faixa`, `maior-vazio`, `sobre-cena`, `atras-de`, `fixo`. O
   `encaixes.resolver` escala cada elemento ao maior tamanho que cabe sem encostar em caixa protegida (16 px de ar),
   respeitando `max`/`min` e a área visível real (alfa_bbox); não coube, tenta o próximo encaixe; nenhum coube, fica de
   fora e vira aviso. Ordem: constante, pattern, herói, apoio. Pattern `sob-veu` só onde há cena (sem véu ele ficaria
   direto sob o texto).
4. **Prepara o PNG.** Cada elemento é cortado no alfa_bbox e reduzido a 2x a maior largura em que aparece:
   `saida/cache-elementos/<id>@<w>.png` (cache por sha256 + largura; o mesmo arquivo em várias páginas, o PDF embute uma
   vez). O herói nunca passa de metade da resolução de origem. Pattern não é cortado (quebraria a costura).
5. **Injeta na camada certa do DOM** e exporta: `sob-veu` logo depois da `.full`/`.cena` (cena com véu no `::after`, da
   máscara sangria: dentro dela); `atras` depois do último véu (sobre o véu, sob o texto, sob a faixa diagonal); `frente`
   antes do `.logo-canto` (acima do texto, abaixo de etiqueta, fio, logo e crédito). Grafismo (formato svg) entra como
   SVG inline `svg.grafismo`, texto vivo na fonte do kit, cor do acento da página. O vertical recebe os elementos das
   páginas equivalentes (capa, cota principal, contato) com encaixes próprios de canto e faixa.
6. **Grava o plano** em `saida/plano-elementos-<receita>[-vertical].json` (itens com `uso` e `sha256`, caixas protegidas
   do render final) e o `qa.py` chama o `qa_geometria.py`, que rasteriza a máscara alfa (girada, escalada, na posição) e
   mede pixel opaco (alfa > 32) contra cada linha. Pattern é textura: fica fora dessa conta (vale o contraste do qa.py).

Provas em `pipeline/test_camadas.py` (`--unidade` em segundos; sem argumento roda também os renders).

## 6. Grafismos por código (texto vivo)

Elemento que tem texto NUNCA vem da IA (aprendizado 7): sai do `pipeline/grafismos.py` como SVG inline, com
`<text>`/`<textPath>` na fonte do kit, e chega ao PDF como texto de verdade. Assinatura (não mudar sem acordo):
`gerar(tipo, params, ctx) -> {"svg", "w", "h", "texto", "fontes"}`.

| Tipo | O que faz | Referência |
|---|---|---|
| `microtexto` | faixa de texto em loop; o espaçamento é recalculado para a faixa medir exatamente a largura pedida | web-nike-run-sp-25-10 |
| `selo` | dois arcos como selo de verdade: o de cima corre no sentido horário (letras para fora), o de baixo no anti-horário (letras em pé); separador às 3h e às 9h; cada arco fecha pela medida; logo do cliente (tingido) ou texto no centro | |
| `meio-tom-simbolo` | símbolo do cliente em pontos (densidade ou LED, com grade apagada), uma cor só | web-nike-run-sp-25-07 |
| `pattern-simbolo` | tile seamless do contorno do símbolo (meia-queda, grade, alternado; contorno ou chapado), borda do tile no vazio | |
| `linha-percurso` | percurso por pontos ou curva paramétrica, marcos de km pela distância ao longo da curva | web-boat-mussoorie-25-13 |
| `fios-tecnicos` | fio com bolinha apontando alvos, rótulo medido (troca de lado se não couber) | web-deck-tomasello-tc2025-21 |
| `moldura` e `etiqueta` | moldura fina ou marcas de canto, tab com texto (retângulo, pílula, seta) do tamanho do texto | |
| `numeral` | numeral gigante cheio, contorno ou fantasma; a caixa é a tinta real dos algarismos | web-corrida-integracao-26-03 |
| `tipo-textura` | palavra com eco do cheio ao vazio, espelhada abaixo do meio | web-lambe-ironman-itau-03 |
| `faixa-diagonal` | faixa que sangra, com o texto repetido com ' · ' no tracking normal (até 0,12 em, nunca esticado) e cortado na borda, medindo exatamente o trecho visível | web-deck-tomasello-tc2025 |
| `mosaico` | grade de módulos (cor, palavra, símbolo, meio-tom, contorno) sem vizinho repetido | web-corrida-sicredi-25-01 |

- **Medida:** avanço de cada glifo e kerning `kern` do GPOS, lidos da própria fonte com fontTools; o SVG trava
  ligaduras, síntese e espaços (`font-variant-ligatures: none`, `font-synthesis: none`, `white-space: pre`). Medido
  em 09/10/2026 no Chromium com as 6 fontes da Sprint: diferença máxima de 0,33 px entre o comprimento calculado e o
  `getComputedTextLength()` (selo de 340 px e microtexto de 1920 px; com o selo em dois arcos, 0,11 px). Sem o kerning a
  faixa de Kanit errava 20,7 px;
  sem `white-space: pre` o espaço final sumia.
- **Peso:** `Familia__700.ttf` é o 700 (mesma regra do render). Peso sem arquivo cai no mais próximo pela regra do CSS
  e o SVG declara o peso que vai desenhar. Glifo ausente na fonte = erro nomeando o caractere.
- **Selo:** sem `texto_baixo`, o texto é dividido nos ' · ' pela largura medida. Prova de orientação no
  test_grafismos.py: a metade de baixo, recortada e desenrolada, é lida pelo tesseract na ordem certa ("2º EDIÇÃO -
  2027") e cada glifo de baixo gira entre -73,9 e 69,0 graus no Chromium; o anel único antigo dá -175,9 a 172,1 e o
  tesseract lê lixo. O `pdftotext -raw` recupera os dois textos (comparando sem espaços).
- **Logo:** `recorte` = caixa em fração do logo (a asa da Sprint é `[0, 0, 0.477, 1]`); só entram as partes que cabem
  inteiras na caixa, então uma letra cortada pela caixa sai inteira.
- **Folha de revisão:** `python pipeline/grafismos.py folha <pasta-do-kit> --receita r1 --fontes <pasta> --saida f.png
  --recorte 0,0,0.477,1` desenha um exemplo de cada tipo com a paleta e as fontes da receita.
- **Costura do pattern-simbolo:** o tile é periódico por construção e a fase da grade é escolhida para a borda passar
  onde há menos tinta. Isso importa porque o índice do `checar` dá 0,71 até num tile perfeito quando um traço fino
  cruza a borda numa coluna carregada; com a borda no vazio a asa da Sprint mede 0,0.

## 7. Âncora de estilo (`--ref`): teste de 09/10/2026

Família `objeto-dourado` da Sprint, âncora `medalha-alada`, 3 objetos (cronômetro, troféu, garrafa) gerados COM e SEM
a âncora anexada, mesmo prompt, uma geração cada (6 imagens de cota, 6 de 6 com alfa real). Distância de estilo até a
âncora na área do objeto (paleta em Lab por k-médias e CIEDE2000, croma médio, contraste em L*, razão de luz
esquerda/direita):

| | paleta (ΔE) | croma | contraste | luz (log) | índice composto |
|---|---|---|---|---|---|
| com `--ref` | 8,27 | 5,78 | 4,29 | 0,374 | 2,28 |
| sem `--ref` | 7,54 | 5,73 | 4,75 | 0,441 | 2,26 |

Comparações pareadas (mesmo objeto, mesmo descritor) em que a âncora deixou mais perto: 7 de 12. Conclusão: nesta
família, cujo bloco de estilo já descreve o meio com precisão ("photoreal product photo ... gold and black"), a âncora
NÃO aproximou o estilo de forma mensurável; nenhum dos 3 copiou a medalha (a frase "match the rendering style of the
attached reference, not its subject" segurou o assunto). `--ref` fica opcional, não vira regra. Falta testar numa
família de traço ou meio-tom, onde a palavra descreve pior o estilo (mais 6 imagens de cota, decisão do Ugo).
Folha comparativa e medidas: `analise/folha-ancora.png` e `analise/medidas.json` do teste (fora do git).

