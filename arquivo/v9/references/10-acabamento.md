# Camada de acabamento

A camada de acabamento é o que dá personalidade ao kit depois da composição (references/09): eco do título, objeto que
cruza as letras, malha em perspectiva, sombra de contato, máscara na foto, grão. Este documento é o processo (da leitura
à revisão, etapas 3b, 4, 5, 6 e 9 da SKILL v9) e o contrato. Kit sem nenhum campo desta camada valida e renderiza
exatamente como antes (mk-2.0).

## Contrato do schema

Versão: `schema_version` aceita `mk-2.0` e `mk-2.1`. Todo campo abaixo é opcional. Onde mora: `schema/mediakit.schema.json`
(direção, formato, lettering) e `schema/elementos.schema.json` (página, elemento da composição, elemento do kit, âncora).
As regras que o schema não alcança estão em `pipeline/acabamento.py` (`validar`), com prova em `pipeline/test_acabamento.py`.
O kit fictício `exemplos/acabamento-prova/` usa todos os campos e é a definição de pronto da mecânica
(`pipeline/test_acabamento_prova.py`).

### Vocabulários

| Campo | Valores |
|---|---|
| família de recurso (`direcao_criativa.recursos[].familia`, `nao_usa[]`) | `ornamento-identidade`, `pattern-textura`, `sobreposicao-recorte`, `profundidade-3d`, `tratamento-imagem`, `tipografia-expressiva`, `acabamento-borda`, `composicao-hibrida` |
| intensidade (direção e página) | 0 nenhuma, 1 sutil, 2 presente, 3 marcante |
| rota do recurso | `codigo`, `imagem`, `hibrido` |
| papel do fio condutor por página | `contrapeso`, `selo`, `separador`, `estrutura`, `eco`, `textura`, `moldura` |
| material (`elementos[].material`) | `metal-escovado`, `ouro`, `couro`, `borracha`, `tecido`, `vidro-fosco`, `plastico-fosco`, `madeira`, `papel`, `grama` |
| papel novo | `acabamento` (em `elementos[].papel` e em `composicao.<página>.elementos[].papel`; `ornamento` continua sendo o nome antigo de herói) |
| `efeito.opacidade` | 1, 0.72, 0.46, 0.24, 0.12, 0.06 (degraus, nunca valor solto) |
| `efeito.blend` | `normal`, `multiply`, `screen`, `soft-light` |
| `efeito.mascara` | `nenhuma`, `diagonal`, `chanfro`, `circulo`, `arco-base`, `janela` |
| `efeito.sombra` | `nenhuma`, `contato`, `deslocada` |
| `efeito.reflexo` | `nenhum`, `piso` |
| `efeito.cruza` | `alvo`: `titulo` ou `numero`; `corte`: `linha_base`, `cap` ou `cy` |
| `efeito.esmaecer` | `direcao`: `dir`, `esq`, `cima` ou `baixo`; `passos`: 3 a 8; `minimo`: 0 a 0.46 |
| `acabamento.profundidade` (página) | `plana`, `camadas`, `volume` |
| `acabamento.grao` (página) | `nenhum`, `leve`, `padrao`, `forte` |
| `acabamento.luz` (página) | `nenhuma`, `esq`, `dir`, `topo` |
| âncora nova | `{relacao: "registro", alvo: "foto"}`: recorte da própria foto na caixa dela, sem eixo nem escala |

### Onde cada campo entra

- `direcao_criativa` (raiz): `consulta` (caminho do registro da consulta ao repertório, ex. `consulta-repertorio.json`),
  `recursos[]` (0 a 9; a lista vazia existe para o formato herdado, e o QA do kit mk-2.1 cobra pelo menos 4 famílias: `id`, `familia`, `referencia`, `principio` com 8 ou mais caracteres e `rota` obrigatórios; `motivo`
  e `nao_copiar` opcionais), `nao_usa[]`, `intensidade {padrao, teto}`, `fio_condutor {motivo, papeis: {rótulo: papel}}`,
  `repete_entre_paginas[]`.
- `formato_base` (raiz): `{id, versao ≥ 1, sha256}` do formato de que o kit partiu.
- `receitas[].fontes.lettering`: família da tipografia expressiva; vazio = a display.
- `composicao.<página>.acabamento`: `recursos[]`, `intensidade`, `profundidade`, `grao`, `luz`, `porque`.
- `composicao.<página>.elementos[]`: `recurso`, `motivo`, `efeito`, papel `acabamento`, âncora `registro`.
- `elementos[]`: `material`, papel `acabamento`.

Grafismos novos, já no `TIPOS` de `grafismos.py` e no enum do schema desde 13/10/2026 (enum e gerador andam juntos;
`test_grafismos.py` cobra): `hachura`, `malha` (com `perspectiva`), `aneis`, `pontos-radiais`, `cantoneira`,
`moldura-dupla`, `regua-borda`, `eco`, `texto-curva`, `ondas`, `curvas-nivel`, `fita`, `carimbo`, `numeral-eco`,
`meio-tom-foto` em `elemento.tipo`, e `regua-borda` também em `sistema_elementos.constantes[].tipo`. `campo` ganhou
`perspectiva`. Tipo fora do enum continua sendo erro da âncora daquela página (`grafismo <tipo> desconhecido`).
Catálogo de uso em `references/05-efeitos.md`.

### Precedência

1. `efeito` da composição vence `elementos[].opacidade` e `elementos[].blend`, que vencem o tema.
2. `acabamento` da página vence `direcao_criativa.intensidade.padrao`.
3. O que o kit declara vence o formato (`formato_base`).

### Regras de `acabamento.validar`

| Regra | Nível |
|---|---|
| mais de 2 elementos de papel `acabamento` numa página | FALHA |
| papel `acabamento` com função fora de `acabamento`, `identidade`, `profundidade`, `equilibrio` | FALHA |
| papel `acabamento` sem `motivo` (dele ou do elemento em `elementos[]`), ou com motivo fora de `sistema_elementos.motivos` | FALHA |
| `efeito.cruza` fora da camada `frente` | FALHA |
| `sombra: contato` ou `reflexo: piso` em elemento que não é PNG de rota de imagem de `elementos[]` | FALHA |
| `sombra: deslocada` fora de grafismo SVG | FALHA |
| página ou elemento usa recurso de família listada em `nao_usa` | FALHA |
| `fio_condutor.papeis` com menos de 3 páginas | FALHA |
| `intensidade.teto` abaixo de `intensidade.padrao` | FALHA |
| página ou elemento cita recurso fora de `direcao_criativa.recursos` | AVISO |
| `acabamento.intensidade` da página acima do teto | AVISO |
| `direcao_criativa.recursos` com menos de 4 famílias distintas | AVISO (vira FALHA na etapa do fluxo) |

Se o alvo do `cruza` (título ou número) existe na página, só o render sabe: alvo ausente vira erro da âncora no render,
como qualquer alvo da composição.

Canal: as FALHAS entram em `plano.composicao_erros` por `composicao.validar(comp, ids, kit=k)`, que o `camadas.py`
chama com o kit inteiro (todas as regras). Sem `kit` rodam só as que a composição decide sozinha (máximo por página,
função, motivo de grafismo declarado na página, cruza na frente, sombra e reflexo em grafismo). O `qa.py` chama
`acabamento.validar(k)` e leva ao relatório as FALHAS que ainda não estão no plano e todos os AVISOS (seção QA, abaixo).
Kit sem campo novo não passa por regra nenhuma.

## Famílias e leitura

Todo recurso tem UMA família (a mesma lista do repertório v2, `repertorio/estudo/RUBRICA-v2.md`). A família diz o que o
recurso faz na página; o sinal da terceira coluna separa recurso de enfeite.

| Família | O que é | Sinal de que é recurso e não enfeite |
|---|---|---|
| `ornamento-identidade` | ornamento, motivo de marca, selo, ícone tirados da identidade | dá para dizer de que parte da marca ou do esporte veio e que papel cumpre (contrapeso, selo, separador) |
| `pattern-textura` | pattern (repetição regular) e textura (matéria sem ladrilho visível) | origem nomeável e amplitude medida contra o fundo |
| `sobreposicao-recorte` | figura recortada, sobreposição, transparência, máscara | o ponto em que os planos se cruzam é medido e serve à leitura |
| `profundidade-3d` | objeto ou cena com volume, sombra, reflexo, perspectiva | planos contados; sombra e luz na mesma direção |
| `tratamento-imagem` | o que se fez na foto (P&B, duotone, tingida, cor seletiva, grão, véu de luz) | a mesma regra em toda a série, medida |
| `tipografia-expressiva` | o tipo como imagem (gigante, eco, atrás ou na frente da figura, em caminho) | razão de escala ou relação com a figura medida, e o texto continua legível |
| `acabamento-borda` | bordas e cantos, molduras, faixas, fios de borda | borda nomeada, com medida, presa a um bloco |
| `composicao-hibrida` | duas ou mais linguagens na mesma página (foto, vetor, render, interface, mapa) | a costura entre as linguagens é nomeada e se repete |

### Leitura (etapa 3b.1)

Antes de olhar o repertório, o kit é lido em 4 linhas, na seção `## Leitura` do `direcao-criativa.md` (sem ela, o
`consultar` lê a seção Leitura do `direcao-de-arte.md` ou as 4 primeiras linhas dele). Cada linha é um fato do evento, do
esporte, do lugar ou do público e termina numa consequência visual:

- Boa: "a final é à noite, sob refletor: a luz é dura e de cima, então o troféu ganha brilho especular e sombra curta."
- Boa: "o campo é de terra vermelha: a textura do chão entra nos dados, e não um grão genérico."
- Ruim: "evento vibrante e acolhedor" (adjetivo sem consequência; reescreva até virar decisão).

As linhas cobrem o que dá matéria ao kit: luz e hora, chão e lugar, objeto do esporte, gesto do público. A consulta tira
dali as palavras e o tom; leitura vaga dá consulta vaga.

### Tabela de inferência: a Copa AME v2 por família

A v2 (mk-2.0, 09/10/2026, o formato `sabado-de-campo`) não declarava recursos. Classificados por olho sobre a folha
`formatos/sabado-de-campo/prova/referencia.jpg` e a gramática do formato; a intensidade é estimada, não medida. Serve de
ponto de partida da v3 e de exemplo de como ler um kit pronto.

| Página | Elemento | Família | Int. | O que falta |
|---|---|---|---|---|
| p.01 capa | goleiro recortado da foto real, na frente da cena | sobreposicao-recorte | 2 | passar na frente do título (`registro`) |
| p.01 capa | faixa diagonal amarela com microtexto | acabamento-borda | 2 | |
| todas | listras 248x16 no topo; fio fino na base (assinatura `fio`) | acabamento-borda | 1 | o fio não progride entre as páginas (`injetar_fio` só desenha a linha) |
| todas | grão dos painéis | pattern-textura | 1 | |
| p.03, p.07 | numeral gigante (10.000, 10) | tipografia-expressiva | 1 | eco, figura na frente do número |
| p.09, p.11, p.12 | numeral fantasma do ativo (02, 04, 05) | tipografia-expressiva | 1 | |
| p.04 histórico | mascote recortado; backdrop num painel creme com colchetes | ornamento-identidade; acabamento-borda | 2; 1 | o painel creme chapado |
| p.05 território | mapa esquemático em anéis | composicao-hibrida | 1 | o mapa é fraco: falta o chão (terra) e o objeto (bandeirinha) |
| p.07 divisor | faixa de pattern dos objetos do jogo; meio-campo sangrando | pattern-textura; ornamento-identidade | 2; 1 | |
| p.08 ativo 1 | cena com "SEU LOGO AQUI" composto e o celular com a tabela | composicao-hibrida | 2 | |
| p.09, p.16 | apito e cartões do Codex | profundidade-3d | 2 | só sombra de contato: sem piso, sem reflexo; na p.16 o apito cai sobre as pernas |
| p.10, p.17 | bola de estúdio | profundidade-3d | 2 | |
| p.12, p.15 | troféu dourado; 5 estrelas ao lado do título | profundidade-3d; ornamento-identidade | 2; 1 | luz especular dirigida; as estrelas como objeto (motivo de momento) |
| p.11 ativo 4 | placar sobre o painel; máscara diagonal da foto | composicao-hibrida; acabamento-borda | 2 | |
| p.13 inventário | papel creme, fios divisórios | acabamento-borda | 0 | a lista crua |
| p.18 contato | goleiro sangrando de baixo | sobreposicao-recorte | 2 | |

Leitura da tabela: a v2 já usava 7 das 8 famílias sem nomear nenhuma; `tratamento-imagem` não existe (as cenas são
naturais, igualadas pelo bloco de estilo); a tipografia expressiva é só numeral grande; a profundidade para na sombra de
contato; nenhuma página passa de 2. O que falta à v3 não é mais efeito por página: é a família que a v2 não tinha, o fio
que atravessa e a intensidade 3 nos pontos certos.

## Consulta

Etapa 3b.2, obrigatória e gravada, depois da Leitura e antes de qualquer escolha:

```
python3 repertorio.py consultar <pasta-do-kit> [--historico <json>]
```

- Lê a Leitura, os tipos de página do kit (`paginas`; sem ela, as chaves de `composicao`; `ativo` vale `ativo_painel` e
  `ativo_topo`) e o `memoria-mediakit/historico-kits.json`.
- Para cada uma das 8 famílias, ordena os recursos do índice: página +3, tom +1, palavra da Leitura no efeito ou no nome
  +1; recurso usado num dos 3 últimos kits de OUTRO cliente perde 2. Os 3 primeiros de cada família vão para `ids`.
- Grava na pasta do kit `consulta-repertorio.json` (`kit`, `data`, `indice_sha256`, `indice_versao`, `leitura {fonte,
  linhas}`, `tipos_pagina`, `tons`, `historico {kits_comparados, recursos_recentes}`, `consultas[]` por família com a
  nota e as razões de cada recurso, `ids`, `folha`) e `mood/consulta-recursos.png` (os recortes anotados dos candidatos).
- A folha se lê com um Read. Para cada família: o candidato serve a este kit? por quê? `risco_pdf` diferente de
  `nenhum` pede estudo A/B; `uau` alto não é motivo sozinho.

Família que volta vazia (o repertório v2 ainda está crescendo, e muitas voltam) se busca à mão
(`repertorio.py buscar --entidade todos --dimensao <família> --pagina <tipo>`) ou a origem é um padrão de composição
(v1) ou uma página de referência; se nada servir, a família fica de fora e o `direcao-criativa.md` diz por quê.

O QA confere a consulta (seção QA): sem o arquivo, ou ilegível, o kit mk-2.1 reprova; gravada sobre outro índice, ou sem
o sha256, avisa. Repertório mudou depois da consulta: rode de novo e confira se a escolha continua de pé.

## Escolha

Etapa 3b.3. De 5 a 9 recursos, de pelo menos 4 famílias, em `direcao_criativa.recursos` (o contrato) e numa tabela do
`direcao-criativa.md` (id · família · de onde · princípio · páginas · por que serve a este kit). Cada recurso:

- `id`: o do recurso no repertório; quando a origem é um padrão ou uma página de referência, um nome do kit.
- `referencia`: de onde veio, como a consulta trouxe: id de recurso, id de padrão, id de referência ou `ref:página`
  (vale `ref#página` e `ref@página`). Fora do índice reprova: recurso sem origem é recurso inventado.
- `principio`: a relação, numa frase, com o motivo do cliente no lugar do objeto da referência ("o objeto do nível pousa
  na borda direita e o material diz o valor"). Nunca a forma.
- `rota`: `codigo`, `imagem` ou `hibrido` (seção Rota por recurso).
- `motivo`: um de `sistema_elementos.motivos`. Recurso sem motivo do cliente é efeito genérico (guia, seção H).
- `nao_copiar`: o que é da referência e fica lá (a fonte, o objeto, o ângulo, a cor, o número de repetições).

```json
{"id": "objeto-no-piso", "familia": "profundidade-3d", "referencia": "material-do-objeto-diz-o-nivel-da-cota",
 "principio": "o objeto pousa num piso com sombra de contato e reflexo curto", "rota": "imagem", "motivo": "medalha",
 "nao_copiar": "as gemas e as barras da referência; o fundo claro"}
```

Junto da lista: `nao_usa` (famílias proibidas neste kit), `intensidade {padrao, teto}`, o `fio_condutor` e os motivos de
momento (próxima seção). A escolha vai ao Ugo no mock (etapa 7), com a folha da consulta.

## Fios e motivos de momento

**Fio condutor** é o recurso que atravessa o kit e faz as páginas serem do mesmo projeto sem serem iguais. O kit tem 2:
o principal em `fio_condutor {motivo, papeis: {rótulo: papel}}`, em pelo menos 3 páginas; o segundo em
`repete_entre_paginas` (ou como constante). Em cada página o fio assume um papel, e o papel tem medida (o QA avisa fora
dela):

| Papel | Medida |
|---|---|
| `contrapeso` | ≥ 1/3 da altura da página, sangrando |
| `selo` | ≤ 1/6 da página |
| `separador` | ≤ 1 altura de maiúscula do título |
| `eco` | opacidade ≤ .24 |
| `textura` | ≥ 1/4 da página |
| `estrutura`, `moldura` | sem medida; presos ao bloco que organizam ou emolduram |

O fio muda de papel, de escala, de lugar e de opacidade; o **tratamento** não muda: o desenho (tipo e parâmetros que não
são medida), o blend, a máscara e o material são os mesmos em toda página (mudar reprova). O mesmo papel em páginas
seguidas avisa.

A **tabela de continuidade** se escreve no `direcao-criativa.md` antes da maquete (fio × página: o papel do fio, ou "-")
e se confere depois do render com `qa_conjunto.py <pasta> --continuidade`, que imprime a mesma tabela com o motivo
presente ou não, a intensidade calculada e os recursos de cada página.

**Motivo de momento** é o recurso que aparece só onde o conteúdo pede: as estrelas na página da premiação, o troféu na
cota principal, a bandeirinha no território. Não atravessa o kit; é dito com a página no `direcao-criativa.md` e conta
na intensidade da página dele.

## Intensidade e ritmo

| Nível | O que é |
|---|---|
| 0 nenhuma | a página respira: nenhum recurso (o porquê diz por quê) |
| 1 sutil | percebido de perto: até cerca de 10 pontos de luminância sobre o fundo, ou opacidade ≤ .12 |
| 2 presente | aparece em 2 segundos, lido depois do título |
| 3 marcante | a segunda coisa que se lê (o foco continua sendo o campo `foco`) |

A **intensidade calculada** da página é a maior entre a declarada (`acabamento.intensidade`, senão `intensidade.padrao`)
e o número de recursos distintos dela: quatro recursos numa página passam de 3, qualquer que seja o rótulo. Acima do
teto avisa; acima de 3 reprova. **Ritmo**: 3 páginas seguidas em 3 reprova; 4 seguidas sem nenhuma 0 ou 1, vizinhas com
o mesmo conjunto de recursos e a mesma textura na mesma escala e área em páginas seguidas avisam. A intensidade 3 vai
onde a narrativa tem pico (capa, o ativo principal, a cota principal, o contato). Meta do teste da AME v3 (em teste,
plano de 12/10): num kit de 18 páginas, 3 em 4 a 7 páginas, nunca 3 seguidas, toda página com pelo menos 2 famílias.

## Rota por recurso

A regra de references/09 §6 vale para o acabamento: o que tem texto, linha, ritmo regular ou medida exata é código; o que
tem volume, luz e matéria é imagem; logo e mascote são sempre do cliente.

| Família | Código (`grafismos.py`, CSS da lista branca) | Imagem (Codex) e tratamento (`tratar.py`, `recortar.py`) | Híbrido |
|---|---|---|---|
| ornamento-identidade | `selo`, `carimbo`, `fita`, `estrelas`, `numeral`, `microtexto`, `aneis` (anéis concêntricos como ornamento ou selo; vira `pattern-textura` quando cobre mais de um quarto da página) | objeto do motivo: `elementos.sh <pasta> <id> objeto --descricao-de <arquivo> --material ouro` | objeto do Codex com selo por código |
| pattern-textura | `hachura`, `malha`, `ondas`, `curvas-nivel`, `pontos-radiais`, `pattern-simbolo`, `meio-tom-foto` | textura única: `tratar.py textura` (JPEG a 1x, uma por área, nunca ladrilhada) | `pattern-simbolo` com a silhueta de um objeto do Codex |
| sobreposicao-recorte | `efeito.mascara`, `efeito.cruza` | `recortar.py --classe pessoa-livre --da-cena --comparar isnet` e âncora `registro` | objeto do Codex que cruza o título (`cruza`) |
| profundidade-3d | `malha` e `campo` em perspectiva, `sombra: deslocada` em SVG | objeto com `--material`; `sombra: contato` e `reflexo: piso` (o render chama o `tratar.py`) | |
| tratamento-imagem | `acabamento.luz` (véu de luz), `acabamento.grao` | `tratar.py tingir`, `tratar.py alfa-degraus` (esmaecer em degraus) | |
| tipografia-expressiva | `eco`, `numeral-eco`, `texto-curva`, contorno como `<path>` | nunca: texto não sai da IA | figura recortada na frente do eco (`registro`) |
| acabamento-borda | `cantoneira`, `moldura-dupla`, `regua-borda`, `fio-borda`, `efeito.mascara` | | |
| composicao-hibrida | `mapa`, `placar`, `campo` | cena do Codex sem texto | lettering e "SEU LOGO AQUI" pelo `compor.py` (homografia) |

Material (`elementos[].material`, vocabulário no contrato acima) entra no prompt do objeto como uma linha de render de
estúdio com a luz da família (`elementos_prompt.montar_prompt`); sem material, o prompt sai igual ao de antes. Recurso
com `risco_pdf` diferente de `nenhum` no repertório se confere no PDF (`contact_sheet.py --acabamento --pdf` e
`validar_pdf.py --imagens-esperadas`, que o `qa.py` já chama).

**Orçamento de imagens**: cada imagem nova que um recurso pede entra em `assets.json` antes de gerar (recurso, página,
material, descrição em arquivo); o total vai no mock. Regerar conta no orçamento; imagem fora dele não se gera.

## Efeitos permitidos e proibidos

No HTML do kit só entra o que `pipeline/prova_pdf.py` provou no PDF do Chromium (`test_prova_pdf.py`). Cada efeito roda
numa página mínima em três versões (base sem o efeito, o efeito e um mutante com `filter: saturate(1.4)` no mesmo nó) e
passa por cinco checagens: `pdffonts` sem Type 3, `pdfimages` com os mesmos objetos de imagem da base (pelo conteúdo),
`pdftotext`, raster do `pdftoppm` contra o PNG do Chromium (diferença média até 3 por canal) e bytes acrescentados.
Medição de 12/10/2026:

| Permitido | Como o render escreve | Bytes sobre a base | O mutante com filter |
|---|---|---|---|
| opacidade e blend no nó | `opacity` e `mix-blend-mode` (normal, multiply, screen, soft-light) no próprio nó, nunca num contêiner | +0,8 KB | reescreve a imagem (+10,5 KB) |
| clip-path polygon | máscaras `diagonal`, `chanfro`, `arco-base` | +0,05 KB | raster novo (+14 KB) |
| clip-path circle | máscara `circulo` | +1,5 KB | raster novo (+15,5 KB) |
| clip-path inset | máscara `janela` (inset com raio), corte do `cruza`, recorte do `registro` | +0,9 KB | raster novo (+15 KB) |
| véu de luz | `data-luz`: gradiente `in oklab` de 4 paradas em `screen` (37-acabamento.css) | +15,2 KB (shading) | raster novo (+207 KB) |
| duas cópias com corte | o mesmo data URI duas vezes: o PDF guarda a imagem uma vez | +0,02 KB | raster novo |
| eco por texto preenchido | `<text>` com `fill` e opacidade em degrau (grafismo da frente G) | +5,8 KB (subconjunto da fonte) | o texto vira imagem |
| contorno como `<path>` | contorno dos glifos pelo fontTools, nunca `<text>` com stroke | +0,6 KB | raster novo |
| mask-image com PNG de alfa | cor chapada sobre o alfa do PNG (preparar_uso) | +5,2 KB (o PNG) | raster novo |

| Proibido | Acusado por (no caso medido) | Variantes que passaram limpas (continuam proibidas) |
|---|---|---|
| `perspective` | em foto: a imagem vira outro raster; em texto com 40°: raster 4,4 | texto com giro leve (rotateY 28°) e recorte com rotateX: sem sinal |
| `matrix3d` | raster 5,0 | |
| `text-shadow` | raster novo, raster 8,9, +15 KB | |
| stroke em `<text>` | fonte Type 3 | |
| `background-clip: text` | raster 5,2 | |
| `mask-image` com gradiente | em texto: raster 5,0 e +10 KB | sobre foto: máscara suave vetorial (+8,7 KB linear, +56 KB radial), sem raster novo |
| `filter` (qualquer um) | raster novo, texto perdido, raster 7,2, +23 KB | |

Os proibidos sem sinal numa variante ficam proibidos pelo caso em que quebram: quem escreve o kit não escolhe a variante
que o Chromium vai achar segura. Esmaecer é sempre em degraus gravados no alfa (`tratar.py alfa-degraus`) ou no svg
(`params.esmaecer` do gerador), nunca `mask-image` com gradiente.

### Como o render aplica cada campo

- `efeito.opacidade` e `.blend`: no próprio nó (img, div da cor chapada ou div do svg); vencem `elementos[]`. Valor fora
  do vocabulário não vira CSS (sai com aviso). No svg o blend só entra quando o efeito declara (o legado nunca teve).
- `efeito.mascara`, em px da caixa do nó: `diagonal` corta o lado esquerdo no ângulo do kit (12°, o da máscara diagonal
  da cena); `chanfro` corta só o canto de cima à esquerda, no mesmo ângulo, até a metade da altura (um ângulo por kit,
  references/05); `circulo` é o maior círculo centrado; `arco-base` desce a base em arco de 1/6 da altura (24 segmentos);
  `janela` arredonda o topo (inset com raio de meia largura). Um clip-path por nó: o corte do `cruza` e o recorte do
  `registro` vencem a máscara. O clip-path gira e espelha com o transform do nó: no elemento espelhado a forma sai
  espelhada, para o corte da diagonal e do chanfro cair no lado que a página pede; no girado, a máscara gira junto.
- `efeito.esmaecer`: PNG pelo `tratar.py alfa-degraus` (cache por sha256 + esmaecer, mesma caixa de corte do original);
  grafismo por `params.esmaecer` do gerador.
- `efeito.cruza` (só PNG de `elementos[]`, camada frente): o corte é a `linha_base`, o `cap` ou o `cy` do alvo, medido na
  página. A metade de cima vai para a camada atras (sob o texto, `data-corte="atras"`), a de baixo fica na frente
  (`data-corte="frente"`); um item no plano, com `cruza: {alvo, corte, y, corte_px}`. Alvo ausente, linha fora do
  elemento ou giro viram erro da âncora (FALHA no QA) e o elemento sai inteiro.
- `efeito.sombra: contato` e `.reflexo: piso`: itens derivados `<id>-sombra` e `<id>-reflexo` (papel acabamento,
  `derivado_de`, encaixe `derivado`), feitos pelo `tratar.py` (sombra com a luz da família, senão a da página; reflexo
  altura .35, opacidade .32, achatar .9) com cache por sha256, na mesma escala do pai: a sombra no canto do PNG de origem
  (o render dá margem transparente antes, senão o desfoque saía cortado reto na borda), o reflexo com o topo na base da
  tinta. Pintam logo antes do pai, na camada dele. Com giro: erro da âncora.
- `acabamento.grao` e `.luz` da página: `data-grao` (opacidade do grão do tema: nenhum tira, leve .3, padrao .5, forte .75)
  e `data-luz` (véu de luz) na section. O 37-acabamento.css só entra em kit com `direcao_criativa`, `acabamento` ou `efeito`.
- Textura (papel acabamento sem alfa): uma imagem por área, a 1x do uso em JPEG q80 (`tratar.textura`), sem o grão da
  frente; blend padrão multiply no papel, screen no escuro, soft-light sobre foto (metade ou mais da caixa numa foto).
- Âncora `registro`: o PNG tem de ter a proporção da foto (1%); a caixa da imagem desenhada sai da mesma conta de
  object-fit e object-position que o JS mede (`ancora.caixa`), o item é a área visível do PNG e a parte que o object-fit
  cortou ganha clip-path (`recorte`).
- `receitas[].fontes.lettering`: token `--fonte-lettering` (cai no display), conferido como display e corpo
  (`familias_faltando`, filtro de formato, fonte carregada); vai ao `ctx.fontes.lettering` dos grafismos. Com a camada
  declarada, o título inteiro da página e a tese vão a `ctx.textos` (grafismo de `texto_de` titulo ou tese).

## Estudo A/B

Etapa 3b.4, antes de o recurso entrar no kit, para três casos: recurso novo (nenhum kit do histórico usou), de
intensidade 3, ou que passa sob texto (corpo, preço, número). Um estudo por recurso:

1. Componha só a página de maior risco para ele (`paginas` com um item, como nas pilotos) e renderize com `--png`.
2. `python3 contact_sheet.py <pasta> --estudo <recurso> [--receita r1]` grava `estudos/<recurso>.png`:
   - cabeçalho com o id, a família, a rota, o motivo, o princípio e o que não copiar;
   - **A**: até 3 recortes do repertório (o recurso do índice com o mesmo id; senão a `referencia` como recurso, como
     padrão ou como referência, com a página: os recortes tirados dela, o mapa e a página capturada), a versão anotada
     quando existe;
   - **B**: cada página que usa o recurso, inteira, com a tinta dele marcada na cor da família, e o detalhe ampliado da
     região (a tinta mais 20% de folga, no mínimo 48 px), onde se vê a matéria e a legibilidade.
3. Recusa, com código 1 e sem gravar nada: recurso fora de `direcao_criativa.recursos`, id fora do formato (minúsculas,
   números e hífen: vira nome de arquivo), referência sem recorte no repertório e recurso que nenhuma página usa.

Perguntas: o princípio veio sem a forma? o texto continua lido em cima dele? o material e a luz chegam perto do recorte?
o recurso veste o motivo do cliente? Passou: o recurso entra no kit. Não passou: troque o recurso, a intensidade ou a
página. O veredito vai ao `direcao-criativa.md` (data, o que se viu, o que mudou). O recorte é material de estudo: ele
nunca entra no kit.

Limite conhecido: o pacote leve da skill (`empacotar_skill.py --leve`) sai sem os recortes; na conta do claude.ai o
estudo recusa por falta de recorte até o pacote levar `repertorio/recortes/`.

## Revisão

Etapa 9, depois das seções I e L do guia, em kit mk-2.1:

1. `python3 contact_sheet.py <pasta> --acabamento [--receita r1]` grava `saida/acabamento-<receita>.png`, e com `--pdf`
   `saida/acabamento-<receita>-pdf.png` sobre o raster do PDF entregue. Uma linha por página: a página com a tinta de
   cada recurso na cor da família; ao lado, o recorte do repertório de até 3 recursos dela; embaixo, a intensidade
   declarada e a calculada (em vermelho acima do teto ou de 3), profundidade, grão, luz e o porquê. Página composta sem
   `acabamento` e recurso sem recorte saem marcados.
2. `qa_conjunto.py <pasta> --continuidade`: o fio em cada página e a linha de intensidade.
3. As 7 perguntas da seção M do guia de qualidade (identidade, integração, continuidade, variedade, valoriza e se lê, lado
   a lado com o recorte, pontos fortes da versão anterior preservados), página a página, com a etapa para onde volta
   cada resposta ruim.
4. Um revisor independente (subagente com modelo explícito) recebe só os PNG das páginas e as 7 perguntas, sem o plano,
   sem a direção criativa e sem os porquês. O que ele não reconhece sozinho não está na página; a divergência volta
   para a etapa da seção M.

Recurso que falhou (QA, estudo, revisão ou o Ugo) vira aprendizado com a medida na etapa 11.

## Prova para dono cético

Antes de dizer que o kit novo é melhor que o anterior, a prova sai dos artefatos, não da opinião. Na pasta `pipeline/`,
sobre o kit renderizado com `--png`:

```
python3 qa.py "<v3>" > "<v3>/saida/qa.txt"                  # o QA gravado; sem ele o veredito sai INCOMPLETO
python3 medir_kit.py "<v3>" --antes "<v2>" [--json]          # as medidas do kit e do anterior, lado a lado, e a diferença
python3 contact_sheet.py "<v3>" --antes "<v2>"               # saida/antes-depois-<receita>.png
python3 contact_sheet.py "<v3>" --cega "<v2>" --semente N    # saida/escolha-cega.png e saida/escolha-cega-chave.json
```

`medir_kit.py` lê só o mediakit.json, o plano, o render-report, os PNG, o PDF e o qa.txt, e não escreve na pasta de
nenhum dos dois kits. Sai com 1 quando alguma medida falha.

| Medida | O que diz | Meta |
|---|---|---|
| famílias por página | quantas famílias cada página usa (recursos da composição e do plano) | ≥ 2 em toda página fora do respiro (intensidade declarada 0 ou 1) |
| cobertura das famílias | em quantas páginas cada família aparece | as 8 menos as de `nao_usa`, cada uma em ≥ 3 |
| elementos ancorados | herói, apoio, estrutura e acabamento com âncora resolvida e cumprida no render final | 100% |
| continuidade do fio | páginas com o motivo do fio e o mesmo hash do tratamento (o que o QA compara) | ≥ 6; nenhuma com outro |
| variedade | estrutura = rótulo (arquétipo e variante) mais o esqueleto ancorado (função e relação) | distintas ≥ as do antes; nenhuma vizinha igual |
| ritmo | intensidade calculada por página | nunca 3 seguidas em 3 (respiro em cada 4: aviso) |
| legibilidade | contraste mínimo por página pela conta do `qa.py`; corpo, preço, número e micro sobre textura fora do véu | 0 abaixo do mínimo; mediana ≥ 95% da do antes; 0 sobre textura |
| PDF | fontes Type 3; título de cada página e tese como texto | 0; todos; sim; o tamanho só informa |
| QA | falhas no qa.txt | 0 |

O kit mk-2.0 sai "não se aplica" nas medidas da camada (famílias, fio, ritmo), nunca zero. Número de páginas diferente
avisa e não quebra; as folhas pareiam as páginas por composição, rótulo e posição.

Escolha cega: o comando imprime o sha256 da chave. Registre esse sha256 (no `direcao-criativa.md` ou na mensagem ao Ugo)
antes de qualquer juiz, pessoa ou subagente, ver a folha; o juiz recebe só `escolha-cega.png`, com os pares rotulados A e
B. Depois, confira as escolhas contra a chave: o sha256 prova que ela não mudou. A mesma semente refaz a mesma folha.

A página de respiro (intensidade declarada 0 ou 1) fica fora da meta de 2 famílias, porque 2 recursos já dão
intensidade calculada 2: o detalhe mostra as páginas de respiro, o mínimo com elas e o mínimo sem elas
(`minimo_sem_respiro`). Família em `direcao_criativa.nao_usa` sai da cobertura (decisão de 13/10/2026).

## QA

Toda regra abaixo só dispara em kit que declara a camada (`acabamento.usa_acabamento`: direção criativa, papel
`acabamento`, `efeito`, `formato_base`...) ou diz `mk-2.1`; as marcadas "mk-2.1" só no rótulo mk-2.1. Exceção: o PDF
vertical vai ao `validar_pdf.py` em todo kit que gera vertical (ordem de 12/10/2026, o vertical saía partido). Fora o vertical, kit mk-2.0
sem campo novo dá as mesmas linhas de antes (provado contra o golden de 12/10/2026). Provas: `test_qa.py`,
`test_qa_geometria.py`, `test_qa_conjunto.py`, `test_validar_pdf.py` (cada regra com o mutante que falha e o inverso).

| Regra | Onde | Nível |
|---|---|---|
| `schema_version` mk-2.0 ou mk-2.1 (antes só mk-2.0) | qa.py | FALHA fora disso |
| `paginas`, `formato_base` e `direcao_criativa` fora do acento e do número sem prova (são ids); a prosa da direção (`principio`, `nao_copiar`, `porque_repete`) continua sem travessão | qa.py | corrige falso positivo |
| falhas e avisos do `acabamento.validar` no relatório (a falha que a composição decide sozinha não repete quando há plano) | qa.py | FALHA / AVISO |
| `formato_base`: diferença contra o `travado` do formato, lacuna `{...}` aberta, formato que não se confere | qa.py (formato.conferir) | AVISO |
| mk-2.1 sem `consulta-repertorio.json` (ou ilegível) | qa_conjunto | FALHA |
| consulta com `indice_sha256` diferente do índice atual, ou sem sha | qa_conjunto | AVISO |
| mk-2.1: recurso da página fora de `direcao_criativa.recursos`, ou com `referencia` fora do índice do repertório (padrão, recurso ou referência; `ref:página` vale) | qa_conjunto | FALHA |
| mk-2.1: página composta sem `acabamento`, ou sem `porque` | qa_conjunto | FALHA |
| mk-2.1: menos de 4 famílias em `direcao_criativa.recursos` (no `acabamento.validar` é aviso) | qa_conjunto | FALHA |
| mk-2.1: fio condutor com tratamento diferente entre páginas (tipo, parâmetros que não são medida, blend, máscara, material) | qa_conjunto | FALHA |
| página da tabela do fio sem elemento com o motivo; o mesmo papel em páginas seguidas; medida fora do papel (contrapeso ≥ 1/3 da altura e sangrando; selo ≤ 1/6p; separador ≤ 1 cap do título; eco ≤ .24; textura ≥ 1/4 da página) | qa_conjunto | AVISO |
| recurso igual (id ou referência) a um dos 3 últimos kits de outro cliente no histórico, sem `porque_repete` | qa_conjunto | AVISO |
| intensidade calculada acima do teto / acima de 3 | qa_conjunto | AVISO / FALHA |
| ritmo: 3 páginas seguidas em intensidade 3 | qa_conjunto | FALHA |
| ritmo: 4 seguidas sem nenhuma 0 ou 1; vizinhas com o mesmo conjunto de recursos; a mesma textura na mesma escala e área em páginas seguidas | qa_conjunto | AVISO |
| item de papel acabamento no plano sem motivo (nem dele, nem da composição, nem de `elementos[]`) | qa_conjunto | AVISO |
| `eco`, `numeral-eco` ou `texto-curva` com `params.texto` (texto livre) em vez de `texto_de` (titulo, evento, tese, local ou data): "texto fora do gate de copy"; `texto` junto com `texto_de` também avisa, porque o gerador usa o `texto` | qa_conjunto | AVISO |
| acabamento fora da régua de família e da novidade, com OCR; derivado (`derivado_de`) fora de tudo | qa_conjunto | relaxa |
| 3º acabamento na página (derivado não conta) | qa_geometria | FALHA |
| derivado fora da conta de herói, apoio e pattern, da sobreposição com o pai e o irmão, e do "solto" | qa_geometria | relaxa |
| acabamento com opacidade ≤ .24 atrás ou sob o véu não conta na sobreposição | qa_geometria | relaxa |
| acabamento translúcido atrás ou sob o véu de corpo, preço, número ou micro: contraste amostrado no PNG no lugar dos 4% (4,5:1; número 3:1; sem PNG reprova); textura sob texto corrido | qa_geometria | FALHA se cair; AVISO |
| `cruza`: a linha mais coberta do alvo aceita até 20%, uma linha só, com contraste 3:1 | qa_geometria | AVISO fixo; FALHA acima, sem PNG ou sem contraste |
| `registro`: caixa no DOM igual à conta de object-fit sobre a foto (mapeada pelo `alfa_bbox`), e `ancora.caixa` idem, 1 px | qa_geometria | FALHA |
| acabamento na cor da marca com opacidade ≥ .46 | qa_geometria | AVISO |
| máscara da tinta: SVG de acabamento com PNG rasterizado em `uso` usa o alfa dele | qa_geometria | precisão |
| imagens por página do PDF acima das que o HTML do render pede (`<img>`, `<image>`, `url()` da seção) | validar_pdf `--imagens-esperadas` | FALHA |
| PDF vertical vai ao `validar_pdf.py` (página 1080x1920, texto por página, fontes), em todo kit que gera vertical | qa.py | FALHA / AVISO |
| kit que não gera vertical (`paginas` só horizontal e sem render-report, ou render-report sem `vertical`; `acabamento.gera_vertical`): as composicao `vertical:*` saem de todas as regras do acabamento (sem `acabamento`, recurso, fio, intensidade, máximo por página; ritmo e continuidade já olham só o horizontal) e o PDF vertical não vai ao `validar_pdf.py`; um aviso lista o que ficou de fora. O render-report, quando existe, vence a declaração: render sem `--sem-vertical` volta a cobrar | qa.py, qa_conjunto | AVISO |
| peso do PDF | validar_pdf | só informação |

Contas que a tabela usa:
- Intensidade calculada da página = a maior entre a declarada (`acabamento.intensidade`, senão `intensidade.padrao`) e o
  número de recursos distintos da página (`acabamento.recursos` e `recurso` dos elementos). Quatro recursos numa página
  passam de 3 qualquer que seja o rótulo.
- Tratamento do fio = o desenho (grafismo com os parâmetros menos os de medida: largura, altura, comprimento, tamanho,
  escala, raio, caixa, pontos; ou o arquivo do elemento), o blend, a máscara e o material. Papel, escala, posição e
  opacidade mudam com o papel e ficam fora.
- Textura = tipo `textura`, `pattern`, `tipo-textura`, `pattern-simbolo`, `meio-tom-simbolo`, `grade-pontos`, `listras`,
  `mosaico` (elemento) ou `hachura`, `malha`, `pontos-radiais`, `ondas`, `curvas-nivel`, `meio-tom-foto` (grafismo), ou
  recurso da família `pattern-textura`.
- `--imagens-esperadas` calibrado nos 5 kits do golden (`schema/fixtures/imagens-golden-2026-10-12.json`): 187 páginas
  horizontais, nenhuma acima do esperado, 180 exatamente iguais.

Campos do plano que o QA lê (o render grava): no item, `papel: acabamento`, `efeito` (cópia da composição; opacidade
efetiva também em `opacidade`), `motivo`, `recurso`, `derivado_de` (`<id>-sombra`, `<id>-reflexo`), `cruza {alvo, corte,
y}` (um item só; no DOM, dois nós com o mesmo `data-elemento`), `ancora.relacao: registro` com `ancora.caixa` e
`ancora.registro.img`, `alfa_bbox`, `uso` (PNG do SVG de acabamento) e `grafismo.params.cor`; na página,
`composicao.chave` e `alvos.foto.img {fit, pos, nat_w, nat_h}`. `qa_conjunto.py <kit> --continuidade` imprime a tabela
fio × página e a linha de intensidade.
