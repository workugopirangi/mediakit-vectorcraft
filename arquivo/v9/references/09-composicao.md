# Composição da página: o elemento nasce do conteúdo

Pedido do Ugo (09/10/2026): ornamentos, imagens e assets continuam ALTAMENTE IMPORTANTES, mas têm de parecer concebidos
para a página. Elemento posto onde sobra espaço lê como adesivo solto. Este documento é o processo; os exemplos estão no
repertório (`repertorio/`, consulta por `pipeline/repertorio.py buscar`); o contrato técnico está em
`references/08-sistema-elementos.md` (acréscimos da composição) e em `schema/elementos.schema.json#/definitions/composicao`.

## 1. A ordem: página, estrutura, elemento, asset

Para cada página, nesta ordem, antes de buscar ou gerar qualquer imagem:

1. **Mensagem**: o que a página diz, numa frase. Se não cabe numa frase, a página tem dois assuntos: divida.
2. **Foco**: o que se lê primeiro (título, número, preço, foto, objeto, lettering). Um só.
3. **Leitura**: a ordem dos olhos depois do foco (2 a 4 passos).
4. **Estrutura**: como o grid divide a página (painel 5/12 + foto 7/12; número sangrando à esquerda e lista na coluna 8;
   título centrado entre duas faixas).
5. **Padrões**: `repertorio.py buscar --pagina <tipo> --problema "<o que a página precisa resolver>"` e a folha dos 2 ou 3
   mais próximos. Copie o PRINCÍPIO (a relação), nunca a forma.
6. **Elementos**: para cada um, função, âncora, escala, camada e porquê (seções 2 a 4).
7. **Acabamento** (kit mk-2.1, seção 9): os recursos da direção criativa que esta página usa, a intensidade, a
   profundidade, o grão, a luz e o porquê, em `acabamento`; o elemento que realiza um recurso leva `recurso`, e o de papel
   `acabamento` leva `motivo` e, se precisar, `efeito`. Página sem recurso também decide: intensidade 0 com o porquê.
8. **Maquete** (`render.py --maquete`): caixas rotuladas no lugar dos elementos (os de acabamento também). Só depois o
   asset é buscado ou gerado, já com área, proporção, orientação e luz certas (seção 6).

Tudo isso vai em `composicao` no `mediakit.json`, por rótulo de página. O rótulo do tipo (`ativo`, `cota`) é a
gramática daquele tipo; a página específica (`ativo:2`, `cota:Master`) vence quando precisa.

## 2. Função: todo elemento tem uma, e a decorativa vale

| Função | O que faz | Exemplo |
|---|---|---|
| foco | é o ponto de atenção da página | troféu gigante na página da premiação |
| contexto | diz onde e com quem o conteúdo acontece | linhas do campo atrás dos números de público |
| identidade | reforça a marca do evento | faixa de advertência preta e amarela na borda |
| conexao | liga duas áreas | fio do número até o rótulo; bola que sai da foto em direção ao título |
| organizacao | ordena informação | régua de categorias; divisória entre entregáveis |
| profundidade | cria planos | objeto que entra na foto e sai dela |
| equilibrio | contrapesa a massa da página | numeral fantasma no quadrante oposto ao título |
| acabamento | personalidade, ritmo, textura (a decorativa) | microtexto de borda, estrelas, grão |

A decorativa é desejada (Ugo, 09/10). O que não pode é elemento sem relação com a página: até o acabamento ancora em
margem, coluna ou borda, e repete do mesmo jeito.

## 3. Âncora: os dois eixos, um deles no conteúdo

Todo elemento prende os DOIS eixos, e pelo menos um numa linha de conteúdo: linha de base ou borda de título, número,
preço, borda de foto, de painel ou de bloco. Só o acabamento pode prender os dois eixos em margem, página ou coluna.
"Encostado na margem por acaso" é o que lê como solto.

| Relação | Quando usar | Como se escreve |
|---|---|---|
| alinha | a borda, o eixo ou a linha de base do elemento cai na do alvo | `{"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}` |
| sangra | o elemento é maior que a página e a borda o corta: escala, energia | `{"relacao": "sangra", "borda": "dir", "corte": "1/3", "y": "cy=foto.cy"}` |
| sobrepoe | o elemento entra na foto ou no bloco: profundidade, ponte entre áreas | `{"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3", "y": "base=foto.base-e5"}` |
| liga | linha ou moldura presa a alvos: conecta, emoldura, separa, continua uma linha da foto | `{"relacao": "liga", "modo": "conecta", "de": "numero.dir", "para": "titulo.esq"}` |

Bordas: x `esq`, `dir`, `cx`; y `topo`, `base`, `cy`, `linha_base`, `cap`. Alvos: `titulo` (e `titulo.l2` para a
segunda linha), `numero`, `preco`, `subtitulo`, `corpo`, `micro`, `foto`, `painel`, `logo`, blocos por classe
(`caixa`, `direitos`, `invest`, `lista-num`...), `coluna:N`, `margem`, `pagina`. Deslocamento só em degrau (`e1` a `e8` =
8, 16, 24, 32, 48, 64, 96, 128 px). A linha de base do título é a da última linha; o cap, o da primeira.

## 4. Escala e corte em degraus

- Escala: uma dimensão da tinta, em fração da página (1/6, 1/4, 1/3, 1/2, 2/3, 3/4, 1: `"1/3p"`), em colunas (`"4col"`)
  ou em múltiplos da altura de maiúscula de um alvo (`"3cap"`, `"de": "titulo"`). A outra dimensão segue o aspecto.
  Px solto é aceito e o QA avisa: o mesmo asset em 560 px numa página e 284 px em outra foi o que a Sprint mostrou.
- Corte e sobreposição: 1/4, 1/3 ou 1/2 da tinta. Corte em ponto de articulação (punho, tornozelo, joelho, borda da
  logo) nunca.

## 5. Unidade e variação

- **Constantes** (selo, microtexto, faixa) ocupam a MESMA caixa em toda página onde aparecem, por receita e formato. Se
  algo bloqueia, o conteúdo cede ou a constante sai daquela página; ela nunca muda de lugar.
- **Gramática por tipo**: cada tipo de página tem uma relação-mãe (ex.: "todo ativo tem o objeto sobrepondo a borda da
  foto do lado oposto ao título"). As páginas do tipo variam dentro de faixas: lado, degrau de escala, degrau de corte.
  Fugir da gramática pede `porque_fora_da_gramatica`.
- **Herói**: muda a cada página, do mesmo motivo e da mesma família (references/08).
- A unidade vem da língua dos elementos (cor, forma, textura, tratamento) e da gramática, não da mesma coordenada.

## 6. Código ou imagem: decidir antes de produzir

| Recurso | Rota | Por quê |
|---|---|---|
| linhas retas e anguladas, fios, divisórias, molduras, colchetes, réguas, setas | código (`grafismos.py`) | espessura e ângulo exatos, alinha no grid, cor por token, vetor no PDF |
| padrão geométrico (listras, linhas paralelas, grade de pontos, ondas regulares) | código, com espaçamento, inclinação, densidade e espessura | varia por página sem perder a identidade |
| linhas de campo, pista, quadra; placar e tabela; mapa esquemático por coordenadas | código | desenho técnico exato e paramétrico |
| numeral, microtexto, selo, etiqueta, tipo-textura | código (texto vivo) | a IA escreve mal; o PDF precisa do texto |
| objeto (bola, troféu, apito, medalha), ilustração, textura de material, motivo orgânico de pattern | imagem: acervo do cliente, depois Codex | volume, luz e material não saem bem em vetor |
| foto de gente e lugar | acervo do cliente, depois cena pelo Codex | prova real vale mais |
| logo e mascote | sempre do cliente | personagem e marca não se redesenham |

A IA gera só pelo Codex (Ugo, 09/10): nunca Higgsfield. Se falhar, repita no Codex com o defeito nomeado no prompt.

**O asset nasce para a página.** O prompt de geração leva o bloco "Composição" (`elementos_prompt.py`, `cena_prompt.py`):
área e proporção reais, orientação ("aponta para o título, à esquerda"), onde fica o detalhe que não pode ser cortado,
luz do bloco de estilo (mesma direção da foto da página), perspectiva e fundo transparente. O objeto nasce INTEIRO e
centrado: o corte é decisão da página (sangra), não do gerador.

## 7. Revisão: a página como conjunto

`contact_sheet.py --composicao` desenha sobre cada página a caixa de cada elemento na cor da função, a linha até o alvo,
o grid e a mensagem; a mesma marcação vai sobre o raster do PDF entregue. Perguntas, página a página (guia de
qualidade, seção L):

1. Cada elemento tem função reconhecível?
2. Parece feito para esta página, ou poderia estar em qualquer outra?
3. Valoriza o conteúdo ou disputa com ele?
4. A leitura continua clara (o foco declarado é o que se lê primeiro)?
5. O peso está equilibrado, ou a assimetria é intencional?
6. Os elementos falam a mesma língua (cor, forma, textura, tratamento)?

Desequilíbrio volta para a composição (âncora, escala, escolha do elemento), nunca para um ajuste de pixel no PDF.

## 8. Na prática: os comandos, na ordem (o Claude roda)

1. Repertório: `pipeline/repertorio.py buscar --pagina <tipo> --problema "<o que resolver>"` e `pipeline/repertorio.py folha
   <id> <id> --saida /tmp/folha.png` (uma leitura). O `repertorio/repertorio.html` é a versão para o Ugo folhear.
2. Composição escrita no `mediakit.json` (`composicao`, por rótulo). Asset que ainda não existe leva `proporcao` [w, h].
   Constante que precisa de lugar fixo declara `ancora` em `sistema_elementos.constantes[]` (só margem, página e coluna).
3. Maquete: `pipeline/render.py <pasta> --maquete [--receita r1]` e `pipeline/contact_sheet.py <pasta> --composicao
   --maquete`. Revisar: cada caixa no lugar certo, nenhuma em cima de painel vendável, a leitura declarada se confirma.
4. Assets na medida: `pipeline/elementos.sh <pasta> <id> <tipo> --descricao-de <arquivo> --pagina <rótulo> ...` e
   `pipeline/cena_prompt.py <pasta> <arquétipo> --composicao --pagina <rótulo>`; o bloco Composition sai do
   `composicao_prompt.py` (área, proporção, lado cortado, para onde olha, luz). Só Codex.
5. Render e QA: `pipeline/render.py <pasta> --png --fontes <pasta>` e `pipeline/qa.py <pasta>` (âncora, caixa única,
   zona vendável e o resto, sobre o render final).
6. Revisão: `pipeline/contact_sheet.py <pasta> --composicao` e `--composicao --pdf` (sobre o raster do PDF entregue), com
   as 6 perguntas da seção 7.
7. Memória: `pipeline/repertorio.py usados <pasta>` vai para o `historico-kits.json` (`padroes`).

Detalhes que mudam o resultado:
- `liga` modo `conecta` com uma ponta na borda da página ou da margem herda o eixo da outra (fio horizontal que entra na
  altura do título); `folga` abre o vão em degrau.
- A foto de página inteira (`.full`) tem a borda na borda da página: `sobrepoe` na foto só cruza uma borda de verdade
  quando a foto é bloco (painel + foto). Em foto de página inteira, ancore no texto ou deixe a foto mandar.
- Num kit com composição, herói do catálogo sem âncora reprova: componha todas as páginas que levam elemento.

## 9. Acabamento: a camada de cima

A composição decide onde cada coisa está e por quê; o acabamento decide de que matéria ela é feita: material, luz,
profundidade, textura, tratamento de imagem, tipografia expressiva, borda. Ele vem depois da página e nunca a conserta:
recurso posto para salvar uma composição fraca é o mesmo adesivo solto da seção 2, com brilho. O processo (leitura,
consulta ao repertório, escolha dos recursos, fios condutores, intensidade e ritmo, rota por recurso, efeitos que o PDF
aguenta, estudo A/B e revisão) está em `references/10-acabamento.md`; o contrato que o render e o QA leem
(`direcao_criativa`, `composicao.<rótulo>.acabamento`, `efeito`), na mesma referência. Na SKILL, é a etapa 3b mais o
acabamento por página da etapa 4.
