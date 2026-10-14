# Sistema de elementos: contratos entre as frentes (congelado em 09/10/2026)

Schema: `schema/elementos.schema.json` (sistema_elementos, elemento, encaixes, plano_elementos, biblioteca_indice). Fixture: `schema/fixtures/sprint-sistema-elementos.json`.

## Fluxo no render (por receita)

1. `plano_elementos.planejar(...)` (Frente C) diz QUAIS elementos vão em cada página e com que papel.
2. `encaixes.resolver(...)` (Frente A) diz ONDE, sobre o layout já medido (depois do data-fit), evitando as caixas protegidas.
3. `grafismos.gerar(...)` (Frente B) produz os elementos de formato svg (texto vivo, fonte do kit).
4. `camadas.py` (Frente A) injeta no DOM na camada certa (sob-veu logo depois da cena; atras sob o texto; frente sobre tudo menos etiqueta, fio e logo) e grava `saida/plano-elementos-<receita>.json`.
5. `qa_geometria.py` (A) e `qa_conjunto.py` (C) leem o plano.

## Assinaturas (não mudar sem acordo)

```python
# Frente C: pipeline/plano_elementos.py
def planejar(sistema: dict, elementos: list[dict], receita_id: str,
             paginas: list[dict],          # [{"n": 1, "rotulo": "capa:c", "tipo": "capa"}, ...]
             encaixes: dict,               # conteúdo de pipeline/encaixes.json
             biblioteca: dict | None = None) -> list[dict]:
    """Determinístico. Devolve [{"n": 1, "atribuidos": [{"id": "asa-capa", "papel": "heroi",
    "encaixes_preferidos": ["canto-sup-dir"], "camada": "frente"}, ...]}, ...]. Aplica sistema.excecoes por cima."""

# Frente A: pipeline/encaixes.py
def resolver(atribuidos: list[dict], rotulo: str, catalogo: dict, medidas_pagina: dict,
             dims_elementos: dict) -> list[dict]:
    """medidas_pagina = caixas protegidas medidas no DOM (classe, x, y, w, h). dims_elementos = {id: (w, h, alfa_bbox)}.
    Devolve itens do plano_elementos (id, papel, encaixe, camada, x, y, w, h, rot)."""

# Frente B: pipeline/grafismos.py
def gerar(tipo: str, params: dict, ctx: dict) -> dict:
    """ctx = {"fontes": {"display": fam, "peso_display": int, "corpo": fam}, "paleta": {...}, "evento": {...},
    "logo_png": caminho|None, "fontes_dir": caminho}. Devolve {"svg": "<svg ...>...</svg>" inline com viewBox e
    width/height, "w": int, "h": int, "texto": str (o texto vivo que o PDF deve conter), "fontes": [fam, ...]}.
    Glifo ausente na fonte do kit = ValueError nomeando o caractere."""
```

## Regras do dono que o QA cobra

- Elementos altamente importantes; 1 herói por página elegível + 2 a 3 constantes; prova sem herói.
- Herói não repete em páginas seguidas; no máximo 3 usos do mesmo herói por receita; cobertura de herói ≥ 70% das páginas elegíveis.
- Kit com ≥ 60% de elementos novos (gerados neste kit: kit_origem = kit atual), ≥ 1 pattern novo, herói da capa novo.
- Elemento com exclusivo_cliente ≠ cliente do kit reprova.
- Todo elemento de uma receita pertence à família dela (medido pelo familia.py) ou é constante.
- Nenhum texto escrito pela IA (OCR); texto só por grafismo (svg, texto vivo).

## Acréscimos da Frente C: composição no plano e no QA de conjunto (09/10/2026)

**Contrato da página no `planejar`.** Dois campos opcionais, além de `n`, `rotulo`, `tipo` e `rotulos`:

- `composicao: true`: a composição da página traz `elementos` (a mesma condição em que o render troca os heróis, apoios e
  estruturas do plano pelos dela; entrada só com `mensagem`, `foco` ou `sem` não conta).
- `herois_composicao: ["asa-capa"]`: os ids dos elementos que a composição põe de herói nessa página (papel `heroi`). Id de
  grafismo declarado só na página (`<id>-p<n>`) pode vir na lista e é ignorado.

Quem manda é o render (`camadas.planejar`), a partir de `composicao.entrada_da_pagina`: `ent = ...[1]`, `composicao =
bool(ent and "elementos" in ent)` e `herois_composicao = [e["id"] for e in ent["elementos"] if e.get("papel", "heroi") == "heroi"
and not e.get("grafismo")]`. Sem os campos, ou com `false` e lista vazia, o plano é o de sempre (kit legado sai igual; provado
por instantâneo de 41 cenários).

- Página composta não recebe herói automático nem o apoio de exceção; constantes e pattern ficam. Precedência: composição >
  ajuste manual > exceção > catálogo. `elegivel(p, encaixes, excecao, auto=True)` devolve falso para ela (assim o `faltantes`
  não pede herói para página que a composição resolve); `auto=False` responde só pelo catálogo, que é o que o render grava em
  `elegivel_heroi` (e o `plano_provisorio` também).
- O herói que a composição pôs conta nos "no máximo 3 usos" e na regra de "não repetir em página seguida": os vizinhos
  automáticos respeitam. Ele sai no plano como item comum, sem `origem`, para a vertical (derivada do plano do horizontal)
  repetir o herói da página equivalente; sem `herois_composicao`, a página composta fica só com constantes na vertical, a
  menos que a composição `vertical:*` a componha.
- Defeito corrigido junto: herói fixado por exceção, ajuste manual ou composição numa página tardia só contava o uso quando a
  busca chegava nela (2 heróis e exceção na página 8: o herói saía 4 vezes). Agora o limite de 3 vale para o total.

**QA de conjunto (`qa_conjunto.py`), sobre o plano que o render grava** (não rodam no plano provisório). Todos AVISO:

| Regra | Quando |
|---|---|
| herói ou apoio sem `funcao` | só em kit com `composicao`; o que veio do encaixe automático não tem função |
| mesmo elemento (mesmo id ou mesma imagem, pelo sha256) com altura diferente em páginas diferentes, sem as duas serem degrau declarado (`ancora.degrau`) | vale também no kit legado: é o caso real da Sprint (asa de 560x327 na capa e 284x166 no público). Tolerância de 5% (mínimo 6 px) |
| composição da página (chave de página ou variante) com relação que a gramática do tipo não usa, sem `porque_fora_da_gramatica` | só em kit com `composicao`; a gramática é a entrada da chave do tipo (`plano.paginas[].composicao.gramatica`) |

Herói ancorado pela composição (`origem: composicao`) conta em cobertura, repetição e novidade como os outros. Grafismo
declarado só na composição da página é o item do plano que traz o `grafismo` que o gerou (ou `origem: composicao` em
`formato: svg`), como `fio-p8` e `fio-p8-s1` da relação `liga`: não está em `elementos[]` e não precisa estar, então não gera o
aviso "está no plano mas não em elementos[]" (o item comum que sumiu do JSON continua avisando); nasce no kit, e por isso vale
como novo (o herói de capa em grafismo não reprova). A regra "constante na mesma caixa em toda página" é do `qa_geometria`.

## Acréscimos da integração (09/10/2026)

As três frentes passaram nas próprias provas e a junção quebrou em 6 pontos de costura. Ficou combinado assim:

- **Rótulos da página:** além de `n`, `rotulo` e `tipo`, cada página do `planejar` leva `rotulos` (todos os nomes pelos
  quais o JSON se refere a ela: `cota:Naming`, `ativo:3`). Sem isso o `paginas` manual de um elemento não acha a página.
- **Quem planeja:** receita declarada em `sistema_elementos.receitas` usa o `plano_elementos.planejar`; kit ou receita
  fora do sistema usa o modo manual do `camadas.py`. O `planejar` com receita ausente devolve só as constantes.
- **Id de constante:** `constante-<tipo>`, e `constante-<tipo>-<n>` a partir da segunda do mesmo tipo, contado sobre a
  lista inteira de constantes (antes do `exceto`). O grão é do tema (`.pagina::after`) e sai do plano no render.
- **Tamanho do grafismo constante:** nasce no tamanho do encaixe (o selo, no diâmetro do canto de selo do catálogo);
  o resolver só encolhe texto vivo até 25%. `constantes[].params` vai para o `grafismos.gerar` (ex.: `recorte`).
- **OCR:** `padrao.texto(caminho) -> str` é o veredito calibrado ("" = sem texto). A biblioteca chama direto; só a
  falta do tesseract deixa pendente.
- **Grafismo no PDF:** o texto continua texto; a única imagem que um grafismo pode trazer é o logo do cliente no miolo
  do selo. Texto em arco (selo) só sai inteiro no `pdftotext -raw`, comparado sem espaços (o `validar_pdf.py` já faz).

## Acréscimos da composição (Fase 0, 09/10/2026)

O Ugo apontou que os elementos pareciam soltos: o encaixe punha o herói onde sobrava espaço, sem relação com o conteúdo.
A composição da página (`composicao` no `mediakit.json`, processo em `references/09-composicao.md`) passa a decidir a
posição quando existe. Contrato:

- **Precedência**, do mais forte ao mais fraco: composição da página, ajuste manual (`x`, `y`, `w` do elemento), exceção
  (`sistema_elementos.excecoes`), catálogo (`encaixes.json`). Com `elementos`, a composição troca os heróis, apoios e
  estruturas que o plano pôs na página; constantes e pattern ficam, menos os que ela tira em `sem`.
- **Rótulo:** a chave mais específica vence: página (`ativo:2`, `cota:Master`) > variante (`cota:b`) > tipo (`cota`, que
  vale como gramática do tipo). A vertical só usa `vertical:capa|numeros|contato`; o que veio ancorado do horizontal sai dela.
- **Alvos:** o render mede, em cada página e nas duas passagens, `alvos`: `pagina`, `margem`, `colunas` (módulo do tema:
  128 px + calha de 24 a partir da margem; 11 colunas no horizontal e 6 na vertical), `titulo` (h1, h2) com `linhas`,
  cada linha com `linha_base` e `cap` (métrica da fonte usada), `subtitulo`, `numero`, `preco`, `corpo`, `micro`, `foto`
  (com tamanho natural e object-position da imagem), `painel`, `logo` e os blocos por classe (`caixa`, `card`,
  `direitos`, `invest`, `lista-num`...). O primeiro de cada nome responde por `nome` e `nome:1`; os seguintes, `nome:2`...
- **Âncora:** `composicao.resolver(atribuido, dims, medidas)` dá posição E tamanho. Relações: `alinha` (x e y),
  `sangra` (borda, corte 1/4, 1/3 ou 1/2, mais o outro eixo), `sobrepoe` (alvo, lado, fração 1/4, 1/3 ou 1/2, mais o
  outro eixo) e `liga` (linha ou moldura presa a alvos; resolvida pela Frente A). Escala em degrau: fração da página,
  colunas ou múltiplo da altura de maiúscula.
- **Tinta:** a caixa que encosta na linha é a da tinta (alfa ≥ 128, `elemento.tinta_bbox` calculado na carga), girada
  pelo centro. O item do plano continua sendo a caixa do PNG de uso (alfa > 8), que é o que o render desenha. Grafismo
  pode devolver `tinta` e `linhas` (`{"linha_base": y}`) no `gerar`, para alinhar pela letra e não pela caixa.
- **Papel `estrutura`:** linha, fio ou moldura presa a alvos. Fica fora do limite de 1 herói e 1 apoio por página.
- **Plano gravado:** cada página leva `rotulos`, `alvos` (do render FINAL), `composicao` (chave, gramática, mensagem,
  foco, leitura, estrutura, padrões), `erros_composicao` e `dom` (caixa de cada elemento no DOM final); o plano leva
  `composicao_erros` (validação do kit). Item ancorado: `encaixe: "composicao"`, `origem`, `funcao`, `porque` e `ancora`
  (relação, restrições com o valor do alvo, tinta na página, escala e se é degrau). O `encaixes.resolver` preserva
  `funcao`, `porque` e `origem` também nos itens do catálogo.
- **QA:** composição que não valida (schema estrito e regras) e âncora que não resolve são FALHA no `qa_geometria`.
- **Ambiente de prova:** o `test_camadas` acha o repositório pelo `git-common-dir` (funciona dentro de worktree) e usa uma
  pasta temporária por cópia do pipeline (frentes paralelas não apagam o kit uma da outra).
- **Grade:** os templates foram desenhados no módulo de 152 px a partir da margem (posições 248 e 400 dos painéis). A
  12ª coluna passaria da margem direita; por isso a medida tem 11 colunas e a margem direita é linha estrutural própria.
- **Grafismo preso a geometria** (contrato para a relação `liga` e para grafismo ancorado com escala): o
  `grafismos.gerar` recebe a geometria já resolvida em coordenadas da PÁGINA e devolve, além de `svg`, `w`, `h`,
  `texto`, `fontes`: `origem` ([x, y] da página onde o canto superior esquerdo do svg cai), `tinta` ([x0, y0, x1, y1]
  na caixa do svg) e, quando houver texto, `linhas` (`{"linha_base": y, "cap": y}` na caixa do svg).
  - `fio`: `{"pontos": [[x, y], ...] (2 ou mais, página), "espessura": px, "terminais": [início, fim] (nenhum, ponto,
    seta, barra), "tracejado": [traço, vão] | null}`.
  - `colchetes`: `{"caixa": [x, y, w, h] (página, já com a folga), "braco": px, "espessura": px}`.
  - `moldura` (já existia): `largura` e `altura` vêm da caixa do alvo mais 2× a folga.
  - Grafismo ancorado com `escala` é gerado na medida da colocação (não esticado): `params` ganha `largura` ou
    `altura` da escala; cache pelo conjunto de parâmetros.

## Acréscimos do render e do QA da composição (Frente A, 09/10/2026)

- **`liga`** (`composicao.resolver_itens`; a geometria sai dos alvos, o grafismo é gerado COM ela e o item fica na
  `origem` que o gerador devolve, sem escala):
  - `conecta`: `de` e `para` = `<alvo>[.lN].<borda>[±desloc]` (a borda e o centro do outro eixo) ou
    `<alvo>.<borda_x>.<borda_y>` (canto). Gera `fio` de 2 pontos. Quando uma ponta é a borda da página ou da margem
    (`pagina.esq|dir`, `margem.esq|dir`), ela herda o y da outra (fio horizontal que entra pela borda na altura do alvo);
    `pagina.topo|base` e `margem.topo|base` herdam o x (fio vertical). `folga` (e1..e8 ou px) abre o vão na ponta
    `para` e também na `de` quando ela é conteúdo. Ex.: `{"relacao": "liga", "modo": "conecta", "de": "pagina.esq",
    "para": "titulo.esq", "folga": "e3"}` = fio de x=0 até 24 px antes do título, no cy da caixa do título.
  - `emoldura`: `alvo` + `folga` (obrigatória). `colchetes` com `caixa` = alvo inflado pela folga (texto: da borda das
    linhas, do cap da 1ª à linha de base da última); `moldura` quando `grafismo.tipo` pede (largura e altura da caixa).
  - `separa`: `entre` = bloco de lista (`lista-num`, `direitos`, `direitos-2col`, `inv-colunas`, `cards`, `caixas4`;
    `card`, `caixa-num` e `inv-item` apontam para o bloco). O render mede `itens` desses blocos. Um `fio` POR divisória,
    cada um item próprio (`<id>-s1`, `<id>-s2`...), porque o `fio` do contrato é uma polilinha. Itens empilhados: fio
    horizontal no meio do vão; todos lado a lado numa linha só: vertical.
  - `continua`: `de_foto` [u, v] em fração da IMAGEM, levado à página pelo object-fit + object-position medidos
    (`alvo`, padrão `foto`); `angulo` em graus (0 = direita, 90 = para cima); `ate` = `<alvo>.<borda>`. Reprova se o
    ponto da foto foi cortado pelo cover ou se a reta cruza a linha fora do alvo.
  - Liga sem `grafismo` e com id fora de `elementos[]` usa o tipo do modo e ganha id por página (`<id>-p<n>`). O item
    leva `ancora.geometria` ({tipo, pontos | caixa, espessura}) e `grafismo` ({tipo, params}).
- **Grafismo ancorado com escala:** a escala vira `largura`/`altura` nos params e o svg nasce nessa medida (uma correção
  se a tinta devolvida for menor que a caixa); gerador que não honra o parâmetro sai esticado e marcado
  (`ancora.medida` = "esticada", aviso). Cache por (ctx, tipo, params); svg gerado por página e por item.
- **Constante com caixa única** por receita e formato: a `ancora` da constante (`sistema_elementos.constantes[].ancora`,
  alinha ou sangra, só margem, página e coluna) ou, sem ela, a caixa do catálogo que serve a MAIS páginas (empate: a
  primeira). A regra "primeira página onde coube" pura punha o microtexto da capa em y=1032 e o tirava das páginas com
  o fio de progresso. A constante nasce no tamanho do encaixe e não encolhe; onde a caixa bate em texto, bloco, zona
  vendável ou painel chapado, sai da página com aviso. As caixas já escolhidas são obstáculo das seguintes. O
  microtexto de faixa ocupa o comprimento inteiro entre as margens (o teto de 1600 px saiu). O encaixe de canto encosta
  no canto da margem quando o espaço está livre (a grade de 8 px deixava o selo 2 px aquém).
- **Zonas vendáveis da foto:** `acervo[].paineis` = o JSON do `--lote` do compor.py (quads em px da própria imagem).
  O render acha o acervo da foto pela impressão digital do src (`img.chave`), leva cada quad e o `foco` (um terço da foto
  visível em volta do ponto) à página e grava `paginas[].vendaveis` (classe `vendavel`). São obstáculo do encaixe e
  FALHA no QA acima de 2% de cobertura.
- **Acabamento da frente:** o PNG de uso de elemento na camada `frente` recebe no raster o grão do tema (blend, opacidade
  e tile lidos do `.pagina::after`) e, se a receita declarar, `tingir` ({cor, forca, preto}) e `temperatura`
  ({referencia, forca}), as contas do tratar.py. Cor chapada continua máscara sem acabamento. `VERSAO_USO` = 3; o arquivo
  ganha o sufixo da chave do acabamento e o item do plano, `acabamento`.
- **Maquete:** `render.py --maquete` = o mesmo render com cada elemento como caixa hachurada na cor da função e rótulo
  `id · função · relação→alvo`; asset ainda não gerado entra pela `proporcao` [w, h] do elemento da composição (no
  render normal, ele reprova). Saída `saida/maquete-<receita>.pdf`, `png/maquete-<receita>-NN.png` e
  `saida/plano-maquete-<receita>.json`; não toca no kit nem no render-report. Kit só com `composicao` já liga o sistema.
- **Plano:** `composicao_kit`, `maquete`, `paginas[].vendaveis`; itens com `caixa_unica`, `acabamento`, `grafismo`,
  `ancora.declarada` (a âncora como foi escrita), `ancora.linhas` (linha de base e cap do grafismo, na página).
- **QA (`qa_geometria`), sobre o render final:** âncora recalculada com os `alvos` finais contra a tinta (2 px, cada eixo
  sozinho) e DOM igual ao plano (1 px) são FALHA; herói, apoio ou estrutura do catálogo sem âncora é FALHA em kit com
  composição e aviso no legado; constante fora da caixa única é FALHA (a mensagem conta cantos, alturas e larguras);
  zona vendável coberta acima de 2% é FALHA; solto, escala fora do degrau, o mesmo herói em tamanhos diferentes sem
  degrau e confete são aviso. A liga conta só o traço da geometria. Elemento `atras` sob título ou número passa se o
  contraste do texto, amostrado no PNG deste render (render-report `png_dir`), continua em 3:1.
- **Folha de composição:** `contact_sheet.py <pasta> --composicao [--receita r1] [--pdf] [--maquete] [--vertical]` →
  `saida/composicao-<receita>[-pdf|-maquete].png`.

## Acréscimos do teste da AME (09/10/2026)
- Grafismos por código (`grafismos.TIPOS`, 28): campo, celular, circulos, colchetes, divisoria, estrelas, etiqueta,
  faixa-diagonal, fio, fio-borda, fios-tecnicos, grade-pontos, linha-percurso, linhas, listras, mapa, meio-tom-simbolo,
  microtexto, moldura, mosaico, numeral, pattern-borda, pattern-simbolo, placar, regua, selo, setas, tipo-textura. Os
  parâmetros de cada um estão na docstring da função `_<tipo>`; `largura` e `altura` são a medida da TINTA. `gerar()`
  devolve também `tinta`, `linhas` (quando há texto) e `origem` (fio e colchetes).
- Parâmetros que são arquivo (`imagem` do celular, `png` do símbolo, do mosaico e do selo) e o logo do contexto são
  resolvidos a partir da pasta do kit e não podem sair dela (`caminhos.dentro_do_kit`).
- Elemento-foco: quando a composição da página declara `foco: grafico` ou `foco: objeto`, a tinta do herói entra na
  conta do dominante (`qa.tinta_do_foco`). Sem essa declaração, elemento é camada e não disputa com texto e foto.
- OCR: texto em foto REAL do cliente (`gerado: false` ou `rota: real`) é aviso (marca de verdade na roupa ou na placa);
  em peça gerada continua falha (`qa_conjunto.leitura_de_texto`).
- Página de cota com herói: o arco tracejado do arquétipo usa `--acento-curva` (padrão: a cor da marca); o kit apaga
  com `--acento-curva: transparent` no `tema-projeto.css`. A faixa de listras sai das cotas por `sem` na composição.

## Acréscimos da camada de acabamento (12/10/2026)
- `grafismos.TIPOS` passa de 28 para 43: entram os 15 de acabamento (hachura, malha, aneis, pontos-radiais, cantoneira,
  moldura-dupla, regua-borda, eco, texto-curva, ondas, curvas-nivel, fita, carimbo, numeral-eco, meio-tom-foto), com o
  enum de `elemento.tipo` no schema junto (`test_grafismos.py` cobra que andem juntos). `regua-borda` vale também em
  `sistema_elementos.constantes[].tipo`; `campo` aceita `perspectiva`. Catálogo, parâmetros e defeitos em references/05.
- Papel de fonte `lettering` (cai no display quando a receita não declara) e `texto_de` com `titulo` e `tese`, que o
  render põe em `ctx["textos"]` quando algum grafismo da página pede.
- Papel `acabamento` (em `elementos[].papel` e na composição): fora do limite de 1 herói e 1 apoio, no máximo 2 por página
  (o 3º reprova no `qa_geometria`), sempre com `motivo` de `sistema_elementos.motivos`. O `encaixes.py` resolve o
  acabamento por último e o de opacidade até .24 não ocupa lugar. Os derivados `<id>-sombra` e `<id>-reflexo` levam
  `derivado_de` e ficam fora da conta de herói, apoio e pattern. O contrato inteiro está em references/10.
- O `png` do `meio-tom-foto` é parâmetro de arquivo como os outros (`camadas.ARQUIVOS_DE_GRAFISMO`): resolvido a partir
  da pasta do kit, sem sair dela.
