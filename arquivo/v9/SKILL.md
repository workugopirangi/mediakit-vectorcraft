---
name: gerar-mediakit-motion
description: "Gera o mídia kit comercial de patrocínio de um evento esportivo cliente da Motion Perform no nível dos kits Corre por Elas e Levinrun: três direções (causa, performance, território) a partir de um único mediakit.json, cenas do ativo em uso com 'SEU LOGO AQUI' geradas pelo Codex, render determinístico e QA que barra número sem fonte, cota sem posição, foto sem direito e patrocinador vetado. Use SEMPRE que pedirem mídia kit, media kit, proposta ou projeto de patrocínio, apresentação para marcas, kit de cotas, 'monta o kit do fulano', 'o cliente respondeu o onboarding', ou quando um cliente de 'Venda de cota de patrocínio' precisar de material para vender cota, mesmo sem a palavra mídia kit. O Claude executa tudo pelo chat; o Ugo nunca abre terminal."
---

# Gerar Mídia Kit Motion Perform

**Versão v9, 13/10/2026.** (Esta linha diz qual versão está na conta do claude.ai: confira nela antes de usar.)

## 🚨 A regra que vem antes de todas

**O Ugo digita `/gerar-mediakit-motion` e não sai do chat.** Nenhum comando pra ele copiar, nenhum arquivo pra clicar, nenhum "roda isso e me manda". Os scripts em `pipeline/` são **ferramenta do Claude**, executadas por ele. Se o ambiente não permitir um passo (sem Codex, sem Chrome, sem rede), o Claude resolve por outro caminho e registra em `pendencias.md`. Nunca delega. **Se a resposta contiver um bloco de comando pro Ugo rodar, a resposta está errada.**

**Raiz do vault:** `~/Developer/UGO's Second Brain`
**Decisões travadas (08/10/2026):** RocGrotesk licenciada pelo Ugo, mas o arquivo ainda NÃO está instalado no Mac (conferido em 09/10/2026: a bancada usa só o subconjunto recuperado do PDF do Corre por Elas; kit novo usa as receitas da cartela livre, `catalogos/pares.json`); imagens da web pela rota do carrossel, bibliotecas públicas gratuitas, sem banco pago; entrega padrão PDF; cotas aprovadas pelo cliente no Motion Events.
**Pasta da skill:** `01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT/` (espelho de `memoria-mediakit/` e `pipeline/` desta skill)
**Pasta do cliente:** `01 EMPRESAS/MOTION PERFORM/CLIENTES/{CLIENTE}/MEDIAKIT/{evento}/`

**A régua é o conjunto das referências das pesquisas, não um kit só:** os PDFs de `regua/fontes.json` (Corre por Elas e Levinrun como kits-régua; Amazônia NIV, Praia Delas, Saudade e SemJuizo como variantes de tom; Sprint só pela arquitetura comercial; Território em Percurso como antiexemplo) e os links de `memoria-mediakit/referencias.md`. O `regua/indice.json` diz, por tipo de página, quais páginas comparar e qual princípio cada uma ensina. Cada página do kit precisa ter a força de composição das equivalentes; se não tiver, não chega no Ugo. O Corre por Elas também é a **bancada** (teste técnico de reconstrução, `pipeline/regressao.sh`), o que não faz dele a única régua (Ugo, 08/10/2026). A gramática inteira está em `memoria-mediakit/gramatica.md`; esta SKILL.md é o processo.

---

## Fluxo (v9: a página primeiro, o acabamento junto)

```
0   Contexto: cliente, evento, o que foi vendido                              → _STATUS.md lido
1   Memória + pré-voo (uma linha por arquivo; lacunas perguntadas)            → nada em aberto sem pergunta
2   Insumos: onboarding.json + pesquisa do Hub + acervo → brief.json          → todo ativo com número ou foto; sem isso não entra
3   DIREÇÃO DE ARTE: direcao-de-arte.md (ideia central, assinatura, bloco de  → cada escolha explica por que serve a ESTE evento;
    estilo das cenas, tratamento, grid, densidade) + moodboard anotado           as 3 direções diferem em tipo/máscara, não só em cor
    + SISTEMA DE ELEMENTOS (motivos, família por receita, constantes)          → âncora de cada família aprovada pelo Ugo
    + LÍNGUA DOS ELEMENTOS e GRAMÁTICA POR TIPO DE PÁGINA, com 4 a 8 padrões    → cada padrão citado pelo id do repertório
      do repertório (repertorio.py buscar e folha)
    + GATE DE COPY (tese, manifesto, títulos, cotas, territórios)              → OK explícito
3b  DIREÇÃO CRIATIVA (acabamento): Leitura em 4 linhas → consulta gravada     → consulta-repertorio.json sobre o índice atual;
    (repertorio.py consultar) → 5 a 9 recursos de ≥ 4 famílias, 2 fios,          cada recurso com referência, princípio, rota,
    motivos de momento, o que o kit não terá → estudo A/B do recurso arriscado   motivo e o que não copiar; estudos/<recurso>.png
4   PAGE PLAN + COMPOSIÇÃO POR PÁGINA (mensagem, foco, leitura, estrutura,     → ritmo: sem 3+3 seguidos, sem 1-1-1, oferta depois da prova;
    padrões; cada elemento com função, âncora nos dois eixos e escala em       todo elemento ancorado num alvo de conteúdo;
    degrau) + ACABAMENTO por página e tabela de continuidade + MAQUETE           acabamento em toda página, fio com um tratamento só;
    (render.py --maquete) + assets.json                                          maquete revisada ANTES de gerar qualquer asset
5   Assets: nascem da maquete (prompt com o bloco Composition: área,           → contact sheet de assets; ≤ 2 Reads; luz igual entre cenas;
    proporção, lado cortado, luz); rota por recurso; cenas (sem texto) →         halo zero; temperatura igualada; só Codex
    compor.py; tratar.py; recortar.py; elementos: biblioteca → gerar o que     → ≥ 60% novos; pattern e herói de capa novos;
    falta → OCR, costura, família → registrar (texto só por grafismos.py)        folha da família sem membro fora
6   PÁGINAS-PILOTO (4): capa, dados, foto + objeto recortado, cota, já com    → render + qa + comparação lado a lado com a régua e com o
    o acabamento (uma delas a de maior intensidade)                              recorte do recurso; "slide" = volta à direção de arte
7   Ajuste do sistema (tokens/arquétipo com OK) e mediakit.json completo       → mock aprovado (com recursos e intensidade por página)
8   render.py --todas --png --fundo → qa.py (JSON + geometria + contraste      → 0 falhas nas 3 direções
    + qa_geometria + qa_conjunto + validar_pdf.py)
9   REVISÃO VISUAL: contact_sheet.py + folha de composição (--composicao,      → nenhum "slide" ou "template de IA";
    também sobre o raster do PDF) + 8 perguntas (seção I) + 6 da seção L         nenhum "solto" sem resposta;
    + folha de acabamento (--acabamento) + 7 da seção M + revisor que não        nenhuma resposta ruim da seção M
    vê o plano
10  Entrega: PDF (padrão); PPTX híbrido só se pedido; 5 linhas ao Ugo          → validar_pdf.py no arquivo entregue
11  Memória: banco de copy, histórico (padrões, recursos, formato), formato    → kit aprovado vira formato; recurso que falhou vira
    do kit aprovado, biblioteca, checklist, aprendizados, escada                 aprendizado com a medida
```

**Nada está aprovado sem OK explícito.** Não renderize o kit inteiro antes das quatro páginas-piloto. **Nunca mostre página com fonte de fallback ou cena placeholder como resultado**: se as fontes não estiverem instaladas, diga isso antes de qualquer imagem (o `qa.py` reprova; `--ambiente-sem-fontes` só para conferência estrutural fora da máquina do Ugo).

## Etapa 0: Contexto

1. `<current_note>` em `CLIENTES/{CLIENTE}/` significa cliente ativo; senão, a conversa diz.
2. Leia `CLIENTES/{CLIENTE}/CLAUDE.md` e `_STATUS.md`. O que foi vendido tem que ser "Venda de cota de patrocínio"; se for outro serviço, pare e pergunte.
3. Liste `CLIENTES/{CLIENTE}/MEDIAKIT/{evento}/`: existe `onboarding.json`? existe `acervo/`? Já houve kit anterior (`historico-kits.json`)?
4. Existe formato para este cliente (entrada do histórico com `formato`) ou para um cliente parecido (`formatos/LEIA-ME.md`)? Então `formato.py aplicar <id> <pasta-do-kit>` antes da etapa 3 (references/11-formatos.md): o kit herda por `formato_base` o que o formato trava (receita, constantes, gramática por tipo, padrões e a `direcao_criativa` com intensidade e recursos; o `fio_condutor` ainda não viaja no formato e se escreve na 3b), e cada item de `trocar` vira linha em `pendencias.md`. O formato adianta decisões, não pula etapa: a 3b roda inteira e o kit vence o formato.

## Etapa 1: Ler a memória e fazer a auto-crítica pré-voo

**Leia SEMPRE, antes de perguntar qualquer coisa, e escreva uma linha por arquivo dizendo o que ele trouxe pra ESTE kit:**

| Arquivo | O que traz |
|---|---|
| `memoria-mediakit/gramatica.md` | a sequência-mestre (§2), as 13 regras (§4), os eixos do sistema (§7), os arquétipos (§8), a produção de cena (§9), os antiexemplos (§10). **É o arquivo de desempate** |
| `memoria-mediakit/guia-qualidade.md` | **as regras verificáveis** (tokens, composição, limites de slot, imagem, narrativa, exportação, proibições, perguntas da revisão). Toda escolha visual tem que caber nele |
| `memoria-mediakit/mapeamento-pesquisa.md` | de onde cada regra veio e o que ainda é PARCIAL ou PENDENTE |
| `memoria-mediakit/diagnostico-v3.md` | o que a v3 perdia para o Corre por Elas, com evidência, e o que a v4 corrigiu |
| `memoria-mediakit/referencias.md` | catálogo de referências por tom; para o moodboard anotado |
| `memoria-mediakit/aprendizados.md` | regras nascidas de correções reais do Ugo. Nunca renumere |
| `memoria-mediakit/banco-copy-kit.md` | teses, manifestos, títulos de ativo e frases de cota aprovados; fórmulas saturadas |
| `memoria-mediakit/escada-cotas.md` | a escada padrão e as faixas por porte, calibradas pelos kits entregues |
| `memoria-mediakit/historico-kits.json` | anti-repetição entre clientes: tese, títulos, cenas, direção escolhida |
| `references/01-onboarding-para-json.md` | mapa campo a campo do onboarding para o JSON |
| `references/02-qa-e-entrega.md` | o que o QA barra e o loop |
| `references/03-assets-e-cenas.md` | de onde vem cada imagem (cliente, redes, banco, IA, edição), prompt e composição |
| `references/04-geracao-por-codigo.md` | PDF × PPTX editável × SVG; o fluxo recomendado; o que rasteriza no PDF |
| `references/05-efeitos.md` | catálogo de efeitos: quando usar, evitar, parâmetros, defeitos, o que o PDF faz |
| `references/06-base-tecnica.md` | a base técnica escolhida e o que foi descartado; como montar uma bancada |
| `references/07-elementos.md` | patterns e ornamentos próprios do evento: gerar com alfa, costura, variantes, limites e contrato `elementos[]`; como o render encaixa (§5), grafismos por código (§6), âncora de estilo (§7) |
| `references/08-sistema-elementos.md` | o sistema de elementos: motivos, família por receita, constantes, 1 herói por página, biblioteca, contratos entre os scripts (inclusive os da composição: alvos, âncoras, liga, caixa única, zonas vendáveis, maquete) |
| `references/09-composicao.md` | **o processo de composição**: página, estrutura, elemento, asset; funções; âncoras; degraus; gramática por tipo; código × imagem; revisão |
| `references/10-acabamento.md` | **a camada de acabamento** (mk-2.1): famílias, leitura, consulta, escolha, fios e motivos de momento, intensidade, rota por recurso, efeitos que o PDF aguenta, estudo A/B, revisão, contrato e QA |
| `references/11-formatos.md` | o formato reprodutível: o que trava e o que troca, `exportar`, `aplicar`, `conferir`, `provar` |
| `repertorio/LEIA-ME.md` | o repertório (31 padrões de 72 referências, com recortes, e os recursos de acabamento da v2 em `repertorio/recursos/`): como buscar, como consultar (`consultar`, etapa 3b) |
| `memoria-mediakit/biblioteca.md` | catálogo de tokens, componentes, arquétipos e assets por esporte |

Depois, **auto-crítica pré-voo**: liste o que está em aberto (o que foi vendido, acervo real e direitos, lettering, cotas definidas ou a montar, pessoas de contato, modalidade, tom) e pergunte o que faltar. Não avance com buraco.

## Etapa 2: Insumos

- **Com `onboarding.json`** (saída do chat do Motion Events): é a fonte. Não repergunte o que está lá. Siga `references/01-onboarding-para-json.md`.
- **Pesquisa do Motion Hub** (`pesquisar-lead` já rodada): seguidores, patrocinadores vistos, plataforma de inscrição, documentos. Entra como prova com `fonte: pesquisa:<url>`.
- **Acervo**: liste `acervo/`. Lettering e logo em PNG transparente ou SVG; fotos reais só com `direito_uso: true`. Sem lettering, a capa usa o nome em display e vira pendência.
- **Fontes e lettering do cliente a partir do kit antigo**: se o cliente tem um PDF anterior (kit, manual, apresentação), rode `pipeline/fontes_do_pdf.py <pdf> <pasta>` (recupera as fontes embutidas como TTF, com a cobertura de caracteres impressa) e `pdfimages`/`pdftocairo -svg` para fotos e lettering vetorial. Registre a licença em `pendencias.md`: fonte comercial exige licença para entregar. O render recebe `--fontes <pasta>`.
- **Sem onboarding**: entrevista batchada, até 4 perguntas por chamada, em duas rodadas: (1) evento, edição, data, local, modalidade, contato; (2) histórico com ano, público, inventário físico, cotas ou "Motion monta", marcas vetadas. Nunca uma rodada por pergunta.

## Etapa 3: Direção de arte (ideia, moodboard, key visual), depois o GATE DE COPY

Antes de qualquer texto de página, três artefatos na pasta do cliente e o sistema de elementos:

1. **`insight.md`** (5 linhas): uma verdade humana do evento em uma frase, mais 3 a 5 traços do território (paisagem, cultura, gesto esportivo). A frase tem que gerar decisão visual ("pedra portuguesa → padrão modular"); se não gerar, é slogan: reescreva.
2. **Moodboard anotado** (`mood/`, 12 a 20 imagens de `memoria-mediakit/referencias.md` e do acervo do cliente), cada uma com a anotação do princípio ("copiar o princípio": crop, camada, tipo, cor) e separadas em "copiar" e "não copiar". Imagem sem anotação sai.
3. **`direcao-de-arte.md`** (meia página): direção (causa, performance, território) e por quê, para este esporte, público e objetivo comercial; **ideia central** em uma linha e 3 palavras proibidas; **key visual** (a composição-mãe: que cena, que lettering, que objeto, que gesto gráfico) e a prova de que sobrevive a 16:9, 9:16 e 1:1; **elemento-assinatura único** (`marca.assinatura`); **bloco de estilo das cenas** (`marca.estilo_cena`); tratamento fotográfico (véu, grão, tingir); grid e densidade por tipo de página; o que este kit NÃO vai ter (lista de acessórios cortados). As três direções diferem em tipografia e máscara, não só em cor. Se a resposta a "por que esta escolha serve a este evento" for "porque a régua manda", ainda não é direção de arte: volte.
4. **Sistema de elementos** (`sistema_elementos` no `mediakit.json`, contrato em `references/08-sistema-elementos.md`). Ornamentos, patterns e grafismos são "ALTAMENTE IMPORTANTES" (Ugo, aprendizado 32): página sem ornamento lê como slide. Declare: 3 a 5 **motivos** com origem (símbolo do cliente, esporte, território: "o mesmo sentido"); uma **família** por receita (meio, estilo de render, paleta, traço, luz e a **âncora**, o elemento que fixa o estilo); 2 a 3 **constantes** que repetem em toda página (grão, microtexto, selo, faixa diagonal); por receita, a família, os motivos e o pattern. Receitas diferentes podem ter famílias diferentes; dentro da receita, cada página recebe um herói diferente da mesma família. A folha da âncora de cada família (`familia.py folha`) vai ao Ugo **antes** de gerar o resto; o OK dele vira `familia.py aprovar` (amarrado ao sha256: se a âncora mudar, a aprovação cai).
5. **Língua dos elementos e gramática por tipo de página** (no `direcao-de-arte.md`; processo em `references/09-composicao.md`). A língua: que elemento existe no kit, por que rota (código ou imagem), com que função e onde (tabela). A gramática: a relação-mãe de cada tipo de página (ex.: "todo ativo tem o objeto do esporte cruzando a borda da foto em 1/3, na altura do título"); as páginas do tipo variam só dentro das faixas (lado, degrau de escala, degrau de corte), e fugir dela pede um porquê escrito. Antes de decidir, consulte o repertório: `repertorio.py buscar --pagina <tipo> --problema "<o que a página precisa resolver>"` e a `folha` dos 2 ou 3 primeiros; escolha 4 a 8 padrões para o kit (copiar o PRINCÍPIO, nunca a forma) e use as folhas do repertório no moodboard. A unidade vem da língua e da gramática, não da mesma coordenada.

Copy é o ingrediente mais barato de refazer. Apresente e espere OK antes de qualquer cena:

```
Gate de copy: aprova, corta ou reescreve antes de eu gerar cena.
Direção sugerida: {causa | performance | territorio} porque {motivo da gramática §7}

CAPA        frase: "{tese.frase}"
MANIFESTO   "{titulo em duas linhas}" / "{subtitulo}" / caixa: "{frase}"
PÚBLICO     3 destaques: {prova} · {prova} · {prova}
ATIVOS      01 "{Sua marca na|largada}" · 02 "..." · 03 "..."   (um por cena)
COTAS       {Apresenta R$ X · Master R$ Y · Oficial R$ Z} com a frase de cada uma
CONTATO     {nome, telefone, e-mail}
```

Regras do conjunto: título de ativo sempre em duas partes com `|` (a segunda na cor, 1 a 3 palavras); frase de capa com até 12 palavras; manifesto diz por que o evento existe, não o que ele é; frase de cota diz o que a marca ganha, em uma linha; cada cota amarrada a um território físico (`cotas[].territorio`: naming da distância, pórtico, kit); nenhum número fora de `provas`; limites de slot do guia seção D valem já no gate (o QA reprova depois). Consulte `banco-copy-kit.md` e não repita tese ou título usado nos 3 últimos kits (`historico-kits.json`).

Se `cotas.quem_define = motion`: monte a escada por `memoria-mediakit/escada-cotas.md`, escreva `cotas-proposta.md` e **pare**: o cliente aprova no chat do Motion Events antes do render.

## Etapa 3b: Direção criativa (o acabamento nasce do cliente e do repertório)

A camada de acabamento (material, luz, profundidade, textura, tratamento de imagem, tipografia expressiva, borda) é o que separa peça de estúdio de página correta (references/10-acabamento.md). Ela nunca sai da cabeça: sai da leitura do evento e da consulta ao repertório. Dois artefatos: **`direcao-criativa.md`** (o porquê e a origem de cada escolha, para o Ugo e para o próximo kit) e **`direcao_criativa` no `mediakit.json`** (o contrato que o render e o QA leem; o kit passa a `schema_version: "mk-2.1"`). Se os dois discordarem, vale o JSON, que é o que sai no PDF: corrija o .md.

1. **Leitura** (seção `## Leitura` do `direcao-criativa.md`, 4 linhas). Cada linha é um fato do evento, do esporte, do lugar ou do público que termina numa consequência visual: "corrida à noite sob a lua: a luz vem de lado, então o objeto ganha sombra de contato e brilho de metal". Linha sem consequência visual é adjetivo: reescreva. A consulta tira as palavras daqui.
2. **Consulta, obrigatória e gravada**: `repertorio.py consultar <pasta>` lê a Leitura, os tipos de página do kit e o histórico, busca os recursos de cada uma das 8 famílias (recurso de um dos 3 últimos kits de outro cliente perde pontos) e grava `consulta-repertorio.json` (com o `indice_sha256` do repertório) e `mood/consulta-recursos.png`, que se lê com um Read. Sem a consulta gravada o QA do mk-2.1 reprova; consulta feita sobre outro índice avisa: refaça e confira se a escolha continua de pé. Família que a consulta não trouxe se busca à mão (`repertorio.py buscar --entidade todos --dimensao <família>`) ou fica de fora, por escrito.
3. **Escolha** (`direcao_criativa` no JSON, tabela no .md): 5 a 9 recursos de pelo menos 4 famílias. Cada um com `id` (o do recurso no repertório; quando a origem é um padrão ou uma página de referência, um nome do kit), `familia`, `referencia` (o recurso, o padrão ou o `ref:página` que a consulta trouxe: referência fora do índice reprova), `principio` adaptado (a relação, numa frase; nunca a forma), `rota` (`codigo`, `imagem`, `hibrido`), `motivo` (um de `sistema_elementos.motivos`: o recurso veste um motivo do cliente) e `nao_copiar`. E mais:
   - **2 fios condutores**: o que atravessa o kit e liga as páginas (a fita de advertência, a linha de cal que liga título e número). O principal vai em `fio_condutor {motivo, papeis}`, com o papel em pelo menos 3 páginas (`contrapeso`, `selo`, `separador`, `estrutura`, `eco`, `textura`, `moldura`); o segundo, em `repete_entre_paginas` ou como constante. O fio troca de papel, de escala e de lugar, nunca de tratamento.
   - **Motivos de momento**: o recurso que só aparece onde a página pede (as estrelas da premiação, o troféu da cota principal), com a página dita no .md.
   - **O que o kit não terá**: `nao_usa` (famílias proibidas neste kit, com o porquê) e os acessórios cortados.
   - `intensidade {padrao, teto}`: 0 nenhuma, 1 sutil, 2 presente, 3 marcante (a segunda coisa que se lê). Sem declarar, 1 e 2.
4. **Estudo A/B** para recurso novo (que nenhum kit usou), de intensidade 3 ou que passa sob texto: componha só a página de maior risco (`paginas` com um item, como nas pilotos), renderize com `--png` e rode `contact_sheet.py <pasta> --estudo <recurso>`: grava `estudos/<recurso>.png` com A, o recorte do repertório, e B, a página com a tinta do recurso marcada e o detalhe ampliado. Perguntas: o princípio veio sem a forma? o texto continua lido em cima dele? o material e a luz chegam perto do recorte? Resposta ruim troca o recurso, a intensidade ou a página; o recurso não entra no kit antes de o estudo passar.

A tabela dos recursos (id · família · de onde · princípio · páginas), os 2 fios e o que o kit não terá vão ao Ugo no mock (etapa 7), com a folha da consulta.

## Etapa 4: Page plan, composição por página, maquete e brief dos assets

**Composição antes do elemento** (`composicao` no `mediakit.json`, por rótulo de página; contrato em references/08 e 09). Para cada página: `mensagem` (uma frase), `foco` (o que se lê primeiro), `leitura`, `estrutura` (como o grid divide a página), `padroes` (ids do repertório consultados) e `elementos`: cada um com `funcao` (foco, contexto, identidade, conexão, organização, profundidade, equilíbrio, acabamento; a decorativa vale), `ancora` nos dois eixos com pelo menos um alvo de CONTEÚDO (título e linha de base, número, preço, foto, bloco; só acabamento ancora em margem), `escala` em degrau (fração da página, colunas, altura de maiúscula) e `porque`. Relações: `alinha`, `sangra` (corte 1/4, 1/3, 1/2), `sobrepoe` (fração 1/4, 1/3, 1/2) e `liga` (fio ou moldura presos a alvos: conecta, emoldura, separa, continua uma linha da foto). A chave do tipo (`ativo`, `cota`) é a gramática; a página específica (`ativo:2`, `cota:Master`) vence. Página sem elemento também é decisão (`elementos: []`, com o porquê na estrutura). Num kit com composição, herói que veio do catálogo sem âncora reprova: componha todas as páginas que levam elemento, inclusive as `vertical:*`.

**Maquete antes do asset**: `render.py "<pasta>" --maquete [--receita r1]` desenha cada elemento planejado como caixa rotulada (`id · função · relação→alvo`) no lugar e no tamanho resolvidos; asset que ainda não existe entra pela `proporcao` [w, h] declarada no elemento da composição. `contact_sheet.py "<pasta>" --composicao --maquete` mostra as caixas, as linhas até os alvos e a mensagem de cada página. Só depois de revisar a maquete se busca ou gera asset.

**Acabamento por página** (kit mk-2.1, contrato em references/10). Toda página composta declara `acabamento {recursos, intensidade, profundidade, grao, luz, porque}`, inclusive a de intensidade 0 (o porquê diz por que ela respira); página composta sem ele reprova. Os recursos vêm só de `direcao_criativa.recursos`. O elemento que realiza um recurso leva `recurso`; o de papel `acabamento` (no máximo 2 por página, fora da conta de herói e apoio) leva também `motivo` e, se precisar, `efeito` (opacidade, blend, máscara, sombra, reflexo, `cruza`, esmaecer, só nos valores do vocabulário). Antes da maquete, escreva no `direcao-criativa.md` a **tabela de continuidade** (fio × página: o papel do fio em cada uma) e confira depois do render com `qa_conjunto.py <pasta> --continuidade`. **Intensidade**: a calculada é a maior entre a declarada e o número de recursos da página; acima do teto avisa, acima de 3 reprova. **Ritmo** (o QA cobra): 3 páginas seguidas em intensidade 3 reprova, e o fio com tratamento diferente entre páginas também; 4 seguidas sem nenhuma de intensidade 0 ou 1, vizinhas com o mesmo conjunto de recursos e a mesma textura na mesma escala e área em páginas seguidas avisam. Na maquete, textura, eco e malha entram como caixas, como qualquer elemento: textura sob texto corrido se resolve ali, não no PDF (o grão e a luz da página não aparecem na maquete; conferem-se na piloto).

`pageplan.json` sai do `render.py` (função: impacto / prova / oferta / ação; peso 1 a 3) e o `qa.py` barra ritmo quebrado: duas páginas de peso 3 seguidas, três informativas seguidas, oferta antes da prova. Para fugir da sequência-mestre, escreva `paginas[]` no JSON. Para cada cena e cada objeto recortado, um brief em `assets.json` antes de buscar ou gerar (campos em `references/03-assets-e-cenas.md` §7): função na narrativa, página, âncora e largura, direção, luz, partes cortadas, resolução mínima, origem pretendida. No máximo 1 objeto por página e 3 por kit. Elementos: `plano_elementos.faltantes` diz, por receita, quantos heróis faltam, de que motivo e aspecto, para cobrir pelo menos 70% das páginas elegíveis e cumprir a novidade.

## Etapa 5: Assets e cenas

Toda página de capa, manifesto, projeção, ativo, cota e contato tem uma imagem. Decida a origem página a página pela tabela de `references/03-assets-e-cenas.md` (cliente → cena gerada pelo Codex → bibliotecas públicas gratuitas pela mesma rota do carrossel, com ledger de IDs e sem repetição; nunca foto de outro cliente, nunca foto com texto em outro idioma, nunca banco pago) e registre no `briefing.md`. Foto real do cliente vale mais que cena gerada quando mostra o que a página promete.

**O asset nasce para a página.** Com a maquete aprovada, o prompt de cada elemento e cena leva o bloco "Composition" tirado da composição e da caixa resolvida (`composicao_prompt.py`): área e proporção reais, lado da página, para onde olha (o foco), que borda o corta e onde fica o detalhe que não pode ser cortado, luz e lente da foto da página. O objeto nasce INTEIRO e centrado; o corte é da página (`sangra`). Em `elementos.sh` use `--pagina <rótulo>` (e `--elemento <id>` quando o id da composição for outro); em `cena_prompt.py`, `--composicao --pagina <rótulo> --elemento <id do herói>`: o bloco diz onde o texto corrido, o escudo e o herói vão cobrir a foto, para o gerador deixar essas áreas calmas. A cena e o sujeito de cada página são decisão da direção de arte e entram por `--cena "<em inglês>"`; câmera, luz do kit, local, composição e restrições continuam do sistema (aprendizado 45).

**Cena gerada: sempre sem texto.** O modelo não escreve na imagem (texto é a dimensão mais fraca de todo gerador). A cena nasce com painéis lisos; lettering, logo e "SEU LOGO AQUI" entram pelo `compor.py`, em perspectiva e herdando a luz. **O Claude roda, por cena:**
```
python3 pipeline/cena_prompt.py "<pasta>" ativo --ativo "Pórtico" --salvar c-portico   → prompt na ordem cena → sujeito → câmera → luz → restrições
bash   pipeline/cena.sh "<pasta>" c-portico                                              → acervo/c-portico.png (Codex, GPT Image); lê acervo/c-portico.prompt.txt, que o --salvar acima gravou
                                                                                           (o prompt nunca vai na linha de comando: um $(...) ou crase dentro de aspas rodaria no seu shell)
python3 pipeline/compor.py acervo/c-portico.png acervo/c-portico.png --lote compor-portico.json   → lettering + placeholders nos painéis
```
**Imagem nova só pelo Codex** (ordem do Ugo, 09/10/2026; o Higgsfield saiu da skill). Erro passageiro: o script repete até 3 vezes com espera crescente. Cota ou login (código 3): pare e espere, nunca troque de fornecedor. Reprovação de qualidade: reescreva o prompt com o defeito nomeado e gere de novo no Codex. Recorte de fundo só pelo `rembg` local (`recortar.py`).

Bloco de estilo (`marca.estilo_cena`) fixo em todas as cenas do kit: mesma hora, luz, lente e paleta. Ordem: projeção → capa → um ativo por cota → cotas → manifesto → contato. Contact sheet único; ≤ 2 Reads individuais. Critério de aceite: real e não pôster; painéis lisos e bem iluminados; pessoas nítidas na frente e multidão desfocada; mãos corretas; luz igual à das outras cenas; resolução ≥ 1920 px. Reprovada → regera com o defeito nomeado no prompt.

Cada imagem entra no `acervo[]` com `funcao`, `direito_uso`, `gerada`, `composta` (quando recebeu lettering/placeholder), `rotulo` quando a página falar de futuro, e `foco` para o corte.

**Rota por recurso** (kit mk-2.1; a tabela inteira, com os comandos, está em references/10). A `rota` de cada recurso decide como ele é feito:

| Família | Código (`grafismos.py` e o CSS da lista branca) | Imagem (Codex) e tratamento |
|---|---|---|
| ornamento-identidade | selo, carimbo, fita, numeral, estrelas | objeto do motivo (troféu, medalha) |
| pattern-textura | hachura, malha, ondas, curvas de nível, pattern do símbolo | textura única (`tratar.py textura`), nunca ladrilhada |
| sobreposicao-recorte | máscara (`efeito.mascara`), `cruza` sobre o título | recorte (`recortar.py`, `--classe pessoa-livre`), âncora `registro` |
| profundidade-3d | malha em perspectiva, `sombra: deslocada` em SVG | objeto com `--material`, `sombra: contato`, `reflexo: piso` |
| tratamento-imagem | véu de luz (`acabamento.luz`), grão (`acabamento.grao`) | `tratar.py tingir`, `alfa-degraus` |
| tipografia-expressiva | `eco`, `numeral-eco`, `texto-curva`, contorno como `<path>` | nunca: texto não sai da IA |
| acabamento-borda | cantoneira, moldura dupla, régua de borda, máscara | nenhuma |
| composicao-hibrida | mapa, placar, campo em perspectiva | cena do Codex com lettering pelo `compor.py` |

Híbrido é o objeto do Codex com o resto por código (o pattern do símbolo com a silhueta do objeto, o objeto que cruza o título). O material do objeto vai para o prompt (`elementos.sh --material`, vocabulário em references/10). **Orçamento de imagens**: cada imagem nova que um recurso pede entra em `assets.json` antes de gerar, com o recurso, a página e o material; o total é o orçamento do kit e vai no mock. Imagem fora do orçamento não se gera; regerar conta no orçamento.

**Tratamento raster acontece aqui, nunca no CSS** (filtro rasteriza o PDF e perde texto): `tratar.py preparar` (até 2880 px, JPEG q85; cena que ocupa a página inteira não precisa passar de 1936 px, e o PDF agradece, aprendizado 49), `tratar.py igualar` contra a cena-referência do bloco só quando a cena veio de outro estilo, e sempre conferindo a prévia (a média de cor confunde conteúdo com luz, aprendizado 46), `tratar.py tingir` quando a direção pedir duotone, `recortar.py --classe` para objetos, `tratar.py recortar-borda` e `tratar.py sombra` (sombra de contato na direção da luz). O objeto entra em `objetos[]` com o brief completo e `temperatura_igualada: true`.

**Elementos (ornamentos, patterns, grafismos).** Reaproveitar quando couber, nunca se prender ao que já existe: todo kit tem pelo menos 60% de elementos novos, 1 pattern novo e o herói da capa novo (o `qa_conjunto.py` reprova). Na ordem:
1. **Buscar** na biblioteca única da Motion (`MARKETING/BIBLIOTECA DE OBJETOS/`): `biblioteca.py buscar --cliente "<CLIENTE>" --motivo … --meio …  --folha <png>`. Exclusivo de outro cliente nunca aparece; `biblioteca.py usar <id> <pasta>` copia e devolve a entrada pronta para `elementos[]`.
2. **Gerar o que falta** (`plano_elementos.faltantes`). Pela IA, só objeto, ilustração, pictograma, textura, motivo de pattern e desenho de adesivo: `ELEMENTOS_DRY=1 bash pipeline/elementos.sh <pasta> <id> <tipo> --descricao-de <arquivo com a descrição em inglês> --estilo "<bloco da família>" --paleta "#hex,…" --aspecto quadrado|largo|alto|faixa --familia … --motivo … [--ref <âncora>]` mostra o prompt sem gastar cota; sem o `ELEMENTOS_DRY`, gera (uma geração por imagem, fundo transparente; regerar é decisão do Ugo). A descrição vai num arquivo, nunca entre aspas na linha de comando: ela traz texto do evento, e um `$(...)` ou uma crase rodaria no shell. `--ref` é opcional: no teste de 09/10 não aproximou o estilo da família fotográfica (references/07 §7). **Tudo que tem texto sai por código** (`grafismos.py`: microtexto, selo, numeral, etiqueta, moldura, fios técnicos, linha de percurso, meio-tom e pattern do símbolo, tipo-textura, faixa diagonal, mosaico), texto vivo na fonte do kit.
3. **Conferir** cada PNG: `padrao.py texto` (a IA escreveu algo? reprova; se a leitura for falso positivo de textura, como os pontos de meio-tom, amplie a região e registre com `padrao.py revisar-texto <png> --evidencia "…"`: a revisão vale só para aquela imagem e aquela leitura, e o `checar` continua avisando; nunca afrouxe o leitor, decisão do Ugo em 09/10), `padrao.py checar` (costura do pattern; acima de 0,5, `tornar-seamless`), `familia.py pertence` (paleta, meio, traço e luz da família). A folha da família vai ao Ugo com a âncora antes do resto (etapa 3) e com todos os membros antes do render final.
4. **Registrar** na biblioteca: `biblioteca.py registrar <pasta>` (exclusivo do cliente em `_EXCLUSIVOS/<cliente>/`; o `INDICE.md` do carrossel é regerado entre marcadores, o resto do arquivo fica como está). Texto escrito sobre textura carregada pode escapar do OCR: a folha continua sendo olhada.

## Etapa 6: Quatro páginas-piloto antes do kit inteiro

Renderize só capa, página de dados (público ou alcance), uma página de foto com objeto recortado (cota principal ou ativo) e uma cota, já com a composição de cada uma (a maquete delas vem antes). Quando houver um kit anterior do cliente ou um kit-régua com assets recuperáveis, faça antes a **bancada** (`references/06-base-tecnica.md`): reconstrua 4 a 6 páginas da referência com os assets dela e compare; o que divergir é do sistema e se corrige antes do kit real. `render.py` com `paginas` reduzido no JSON (cada item é um tipo ou `{tipo, variante}`; o render gera só essas, nessa ordem), `qa.py`, e `contact_sheet.py --regua`. As pilotos já saem com o sistema de elementos (herói, constantes, pattern) e, em kit mk-2.1, com o acabamento: uma das quatro é a página de maior intensidade do kit (se ela não está entre as quatro, entra no lugar da mais parecida), e cada piloto se compara também com o recorte dos recursos dela (`contact_sheet.py --acabamento`). Piloto sem ornamento ou sem acabamento não prova nada sobre o kit. Compare cada uma com as páginas equivalentes que o `regua/indice.json` aponta (a do kit-régua e a do mesmo tom da direção) com as 8 perguntas. Se qualquer uma ler como "slide" ou "template de IA", a causa é investigada (asset, direção, token, arquétipo) e corrigida na origem; não se expande uma composição fraca porque já está pronta. Só depois: `mediakit.json` completo e mock.

## Etapa 7: Escrever o mediakit.json completo e mostrar o mock

O Claude escreve **um arquivo**: `mediakit.json` (schema `mk-2.0` em `schema/mediakit.schema.json`; `mk-2.1` quando o kit declara a camada de acabamento da 3b). **Nunca escreve CSS nem HTML.** O `render.py` deriva a sequência-mestre (gramática §2) do JSON; `paginas` no JSON sobrescreve a ordem quando houver motivo. Com `receitas` (até 3: par tipográfico, paleta, fundo escuro/papel/cor, máscara reto/diagonal/arredondado/sangria, pattern e variante por tipo de página, catálogo em `pipeline/templates/arquetipos.html`), o render gera `kit-<id>.pdf` por receita; `paleta.py <pasta>` propõe as paletas com o contraste medido e `contact_sheet.py --receita <id>` compara cada variante com a página da régua que a inspirou.

Mock: uma mensagem com a sequência (tipo de página · **dominante** · título · cena · prova ou cota · **recursos** · **intensidade**), a assinatura, a direção e, em kit mk-2.1, a tabela dos recursos, os 2 fios, o que o kit não terá e o orçamento de imagens. Espere OK. Ajuste só o mock e reconfirme.

Regras do JSON (o QA confere): todo número em `provas` com `edicao`, `tipo` (realizado, informado, meta, projecao, proxy) e `fonte`; `realizado` só com documento ou pesquisa; proxy só com nota visível; cota com preço, quantidade, entregáveis posicionais, `aprovada_por`; exclusividade com categoria e prazo; sem travessão; sem acento faltando; marca vetada em lugar nenhum.

## Etapas 8 e 9: Render, QA, validação do arquivo e revisão visual (o Claude roda, o Ugo só vê)

```
python3 pipeline/render.py       "<pasta>" --png --fundo --fontes "<pasta-de-fontes>"          # kit com receitas: uma por PDF
python3 pipeline/render.py       "<pasta>" --todas --png --fundo --fontes "<pasta-de-fontes>"  # kit sem receitas: as 3 direções (o --todas força as direções)
python3 pipeline/qa.py           "<pasta>"
python3 pipeline/contact_sheet.py "<pasta>" --direcao causa --regua "<cofre>/GERAR MEDIAKIT/regua"
python3 pipeline/contact_sheet.py "<pasta>" --acabamento [--pdf]                              # kit mk-2.1: a folha de acabamento (seção M)
python3 pipeline/qa_conjunto.py   "<pasta>" --continuidade                                     # kit mk-2.1: fio × página e a linha de intensidade
```

`render.py` monta as três direções do mesmo JSON, deriva o page plan, injeta a assinatura e o grão (PNG), resolve objetos recortados com sombra e oclusão, mede cada `[data-fit]`, coleta no DOM as caixas de texto e mídia, fontes carregadas, dominante, densidade, grid e cor por página, e exporta PDF 1920×1080, vertical e o fundo sem texto (para PPTX). Com `sistema_elementos`, o render também mede as linhas de texto, planeja (`plano_elementos.py`), encaixa (`encaixes.json` por variante), injeta cada elemento na camada certa (`camadas.py`) e grava `saida/plano-elementos-<receita>.json`. `qa.py` chama `validar_pdf.py` no arquivo gerado: tamanho de página, fontes embutidas sem Type 3 e sem fallback, títulos como texto, nome do evento e tese como texto, nenhuma imagem de página inteira além das cenas e das texturas declaradas; o tamanho é só informado (sem teto de peso por ordem do Ugo (12/10/2026)). Elementos: `qa_geometria.py` (a máscara alfa real do elemento contra cada LINHA de texto: mais de 4% de uma linha de corpo, preço, número ou micro, ou 8% de um título, reprova; encostar em logo, etiqueta ou crédito reprova; e a composição, sobre as caixas medidas de novo no render final: âncora não cumprida em 2 px, DOM diferente do plano, constante fora da caixa única, elemento sem âncora num kit com composição e painel vendável "SEU LOGO AQUI" coberto acima de 2% são FALHA; solto, escala fora do degrau, o mesmo asset em tamanhos diferentes e confete são AVISO que a revisão responde) e `qa_conjunto.py` (herói em pelo menos 70% das páginas elegíveis, nunca o mesmo em páginas seguidas, no máximo 3 usos por receita, 60% de novos, pattern e herói de capa novos, exclusivo de outro cliente, membro fora da família, texto escrito pela IA). `qa.py` barra (código 1) em duas camadas: **JSON** (número sem prova, limites de slot, cota sem posição, marca vetada, travessão, acento) e **geometria** (fonte com fallback, texto fora da página, encolhimento acima de 28%, viúva em título, tamanho fora da escala, micro em duas linhas, mais de 4 ícones, densidade acima de 45%, página sem dominante, contraste amostrado no PNG abaixo de 4,5:1 ou 3:1, arquétipo repetido em sequência). **Se reprovar, não mostre a arte.** Corrija o JSON (texto, foco, qual cena) e rode de novo. Mudança de visual é proposta no `tema.css`/arquétipo com OK do Ugo; nunca no PDF nem no HTML gerado.

**Revisão visual obrigatória (etapa 9).** Abra o contact sheet com um Read e responda, página a página, às 8 perguntas do `guia-qualidade.md` seção I: dominante é o declarado? o que a página diz em 3 s? peça ou slide? o que sai sem perda (corte um acessório)? a cena mostra o que a página promete? a cor da marca está só onde foi contada? há texto sobre luz sem véu? parece template escuro de IA? E, para os elementos: a página tem ornamento, e ele é do mesmo sentido do resto (motivo e família)? Página sem ornamento lê como slide (aprendizado 32). Depois, a folha de composição (`contact_sheet.py "<pasta>" --composicao`, e `--pdf` sobre o raster do arquivo entregue) com as 6 perguntas da seção L do guia: função reconhecível? feito para ESTA página? valoriza o conteúdo? leitura clara? peso equilibrado ou assimetria intencional? mesma língua? Resposta ruim volta para a escolha, a composição ou a direção de arte; aviso de "solto" aceito vai para `pendencias.md` com o motivo. Em kit mk-2.1, depois, a **folha de acabamento** (`contact_sheet.py "<pasta>" --acabamento`, e `--acabamento --pdf` sobre o raster do PDF entregue): cada página com a tinta de cada recurso na cor da família e, ao lado, o recorte do repertório de onde ele veio, mais a intensidade declarada e a calculada. Responda às 7 perguntas da seção M do guia (identidade, integração, continuidade, variedade, valoriza e se lê, lado a lado com o recorte, pontos fortes da versão anterior preservados). Depois, um **revisor independente** (um subagente com modelo explícito, que recebe só os PNG das páginas e as 7 perguntas, sem o plano, sem a direção criativa e sem os porquês) responde às mesmas perguntas: o que ele não reconhece sozinho não está na página. Divergência entre as duas leituras volta para a etapa que a seção M aponta. Confira também o PDF aberto (cortes, fontes, páginas iguais aos PNGs). Resposta "slide" ou "template de IA" em qualquer página bloqueia a entrega, mesmo com QA zero. Fonte de fallback ou cena placeholder invalida a revisão: pare e diga.

Mostre o contact sheet das três direções no chat, com o veredito por página.

## Etapa 10: Salvar e entregar

```
CLIENTES/{CLIENTE}/MEDIAKIT/{evento}/
├── onboarding.json       ← vem do Motion Events
├── brief.json            ← objetivo da marca-alvo, audiência, inventário com número ou foto
├── insight.md · direcao-de-arte.md · mood/ · assets.json
├── direcao-criativa.md   ← kit mk-2.1: leitura, escolha e porquês do acabamento, tabela de continuidade
├── consulta-repertorio.json · estudos/   ← a consulta gravada (3b.2) e os estudos A/B (3b.4)
├── mediakit.json         ← a única coisa que o Claude escreve à mão para o render
├── cotas-proposta.md     ← só quando a Motion monta a escada
├── acervo/               ← lettering, fotos reais, cenas geradas (+ .prompt.txt); tratado/ e objetos/
├── saida/                ← kit-{direcao}.pdf, vertical, png/, render-report.json
├── fontes.md             ← tabela id · valor · edição · tipo · fonte
├── pendencias.md         ← o que ficou fora e por quê; direções e cenas pendentes; rota de geração usada
└── briefing.md           ← contexto, gate de copy, direção e motivo, cenas e prompts, decisões
```

Ao Ugo, em cinco linhas: cliente e evento · direções prontas · falhas (zero) e avisos · as duas ou três pendências que importam · caminho dos PDFs. Ele aprova ou devolve com o defeito específico. Devolução volta ao loop; aprovação registra data em `pendencias.md`.

Motion Hub: registrar `entrega` + `entrega_versao` + `aprovacao` quando o escritor existir (fase 2). Até lá, PDFs ao cliente pelo chat do Motion Events ou WhatsApp. **Não pergunte feedback no chat depois da entrega.**

## Etapa 11: Gravar a memória

1. `banco-copy-kit.md`: tese, manifesto, títulos de ativo e frases de cota aprovados, com o id do kit. O que ficou bom e não entrou vai pra "Descartadas mas boas".
2. `historico-kits.json`: entrada com `id`, `data`, `cliente`, `evento`, `modalidade`, `tom`, `direcao_escolhida`, `tese`, `titulos_ativos`, `cenas` (prompts), `cotas`, `pasta`, `status`, as `receitas` com a família e os elementos usados, `padroes` e `recursos` (os ids do repertório usados, de `repertorio.py usados <pasta>`) e, quando houver, `formato`, para não repetir a mesma solução em clientes seguidos.
3. Biblioteca: `biblioteca.py registrar <pasta>` com os elementos finais do kit (o uso fica registrado; exclusivo do cliente em `_EXCLUSIVOS/`), `biblioteca.py checar` sem falha e `sincronizar` (o `INDICE.md` do carrossel é regerado entre os marcadores).
4. `checklists/mk-XXX-{slug}.md`: o que passou, **o que o Ugo corrigiu**, decisões, pendências.
5. `aprendizados.md`: correção que virou regra entra com número novo. Recurso que falhou (no QA, no estudo A/B, na seção M ou com o Ugo) entra com a medida: o que se mediu, em que página, e o número. **Não edite a gramática nem esta SKILL.md por conta própria; proponha e espere o OK.**
6. `escada-cotas.md`: preço praticado entra na calibração por porte.
7. **Formato**: kit aprovado pelo Ugo, com QA 0 falha, vira formato (`formato.py exportar <kit> <id>`; o kit que herdou de um formato e mudou o que trava gera `--nova-versao`) e a entrada do histórico ganha `"formato": "<id>"` (references/11 §3).

---

## O que nunca fazer

- Inventar público, histórico, patrocinador, preço, exclusividade ou resultado. Falta vira pendência.
- Rotular meta como realizado, ou fala do organizador como realizado.
- Citar marca com `pode_citar: false`.
- Prometer vendas, leads ou alcance como entregável.
- Apresentar cena gerada como registro de edição anterior.
- Editar PDF, HTML gerado ou CSS para corrigir conteúdo.
- Usar dado, foto ou cena de outro cliente.
- Travessão ou meia-risca nos textos do kit.
- Mostrar render com fonte de fallback ou placeholder como resultado.
- Deixar o modelo de imagem escrever texto, logo ou número na cena.
- Tamanho de fonte, espaço ou raio fora dos tokens; ícone para decorar; numeral sem sequência; gradiente de duas paradas; sombra ou brilho.
- Tabela de cotas com "x" por coluna.
- `filter`, `drop-shadow`, `feTurbulence` ou `mask-image` com gradiente no CSS (rasterizam o PDF); efeito raster é no `tratar.py`. A máscara com o alfa de um PNG é permitida (lista branca provada em references/10).
- Expandir o kit inteiro antes das quatro páginas-piloto passarem na comparação com a régua.
- Objeto recortado sem brief, sem sombra pré-renderizada ou sem temperatura igualada.
- Página elegível sem ornamento; o mesmo herói em páginas seguidas; elemento fora da família da receita.
- Herói em cima do que a página vende (pórtico, escultura, placa "SEU LOGO AQUI"): o QA reprova acima de 2% do painel vendável.
- Elemento sem âncora nos dois eixos, ou ancorado só na margem sem ser acabamento: é o que lê como solto.
- Gerar asset antes da maquete, ou pedir ao gerador que corte o objeto (o corte é da página).
- Constante (faixa, selo, microtexto) mudando de lugar entre páginas: ela fica na mesma caixa ou sai da página.
- Gerar imagem fora do Codex (Higgsfield saiu da skill em 09/10/2026).
- Caminho de arquivo fora da pasta do kit (absoluto, `..` ou link para fora), texto do kit com marcação além de `<b>`, ou valor fora do formato em campo que vai para atributo ou CSS (foco, cor, fonte, id): o render recusa, porque o arquivo iria embutido no PDF e o navegador do render executaria o resto (revisão de segurança de 09/10).
- Elemento com texto vindo da IA (texto é sempre grafismo por código); exclusivo de um cliente no kit de outro.
- Escolher recurso de acabamento sem a consulta gravada (`consulta-repertorio.json`), ou de cabeça.
- Copiar a forma da referência: o kit copia o princípio. O recorte do repertório nunca entra em kit (é material de estudo).
- Efeito que não veste um motivo do cliente, ou que tira contraste do texto.
- Contorno vazado em texto (stroke em `<text>`) ou efeito tipográfico por filtro (`text-shadow`, `background-clip: text`, `filter`): no PDF vira Type 3 ou raster. Contorno só como `<path>`.
- 3 páginas seguidas em intensidade máxima, ou o mesmo conjunto de recursos em páginas vizinhas.
- Fio condutor mudando de tratamento entre páginas: muda o papel, a escala e o lugar; desenho, blend, máscara e material ficam.
- Testar recurso, efeito ou formato em kit entregue: o teste é num clone ou no kit fictício (`exemplos/acabamento-prova`).
- Pedir pro Ugo rodar qualquer coisa.

## Checklist final

**Processo**: [ ] Ugo não abriu terminal · [ ] memória lida com 1 linha por arquivo · [ ] pré-voo feito
**Copy**: [ ] gate aprovado antes de cena · [ ] títulos de ativo com `|` · [ ] nenhum número fora de provas · [ ] tese e títulos não repetidos (histórico)
**Antes do primeiro render** (aprendizado 43): [ ] família com o meio e a luz do vocabulário do `familia.py` (foto-objeto, traco, chapado...; esquerda, direita, cima) · [ ] `exclusivo_cliente` igual ao `cliente.nome` do kit · [ ] cena em capa, manifesto, ativos, cotas e contato
**Cenas**: [ ] uma por página que exige · [ ] cena sem texto do modelo; nome do evento e placeholders compostos pelo `compor.py` em superfície (regra 7, aprendizado 23) · [ ] contact-sheet, ≤2 Reads · [ ] prompts salvos
**Direção**: [ ] `insight.md`, moodboard anotado e `direcao-de-arte.md` (ideia, key visual em 3 recortes, assinatura, bloco de estilo, cortes) · [ ] cada escolha explica por que serve a este evento · [ ] as 3 direções diferem em tipo/máscara
**Plano**: [ ] page plan com ritmo aprovado pela QA · [ ] brief de toda cena e objeto antes de buscar · [ ] quatro páginas-piloto comparadas com a régua antes do kit
**Composição**: [ ] língua dos elementos e gramática por tipo no `direcao-de-arte.md`, com os padrões do repertório · [ ] `composicao` em toda página que leva elemento (mensagem, foco, leitura, estrutura, padrões) · [ ] todo elemento com função, âncora nos dois eixos e escala em degrau · [ ] maquete revisada antes de gerar asset · [ ] folha de composição revisada (seção L), também sobre o PDF · [ ] avisos de "solto" respondidos em `pendencias.md`
**Acabamento** (kit mk-2.1): [ ] Leitura em 4 linhas, cada uma com consequência visual · [ ] `consulta-repertorio.json` sobre o índice atual · [ ] 5 a 9 recursos de ≥ 4 famílias, com referência do índice, princípio, motivo e o que não copiar · [ ] 2 fios e motivos de momento · [ ] estudo A/B dos recursos novos, de intensidade 3 ou sob texto · [ ] `acabamento` com porquê em toda página composta · [ ] tabela de continuidade conferida (`--continuidade`) · [ ] folha de acabamento com as 7 perguntas da seção M e o revisor independente
**Elementos**: [ ] motivos, famílias e constantes declarados · [ ] âncora de cada família aprovada pelo Ugo antes do resto · [ ] biblioteca consultada e ≥ 60% novos, pattern e herói de capa novos · [ ] OCR, costura e família conferidos · [ ] `qa_geometria` e `qa_conjunto` sem falha · [ ] registrados na biblioteca
**Arte**: [ ] mock aprovado antes do render · [ ] `qa.py` passou nas 3 direções (JSON + geometria + contraste) · [ ] revisão visual com as 8 perguntas por página · [ ] um acessório cortado por arquétipo · [ ] fontes reais instaladas · [ ] cenas sem texto do modelo, lettering composto
**Entrega**: [ ] 3 PDFs + 3 verticais · [ ] `validar_pdf.py` 0 falhas no arquivo entregue (fontes, Type 3, raster; tamanho só informado) · [ ] PPTX híbrido só se pedido · [ ] `fontes.md`, `pendencias.md`, `briefing.md`, `direcao-de-arte.md` · [ ] 5 linhas ao Ugo · [ ] sem pedir feedback
**Aprendizado**: [ ] `banco-copy-kit.md`, `historico-kits.json` (com `padroes`, `recursos` e `formato`), `checklists/` · [ ] kit aprovado exportado como formato · [ ] `aprendizados.md` se houve correção · [ ] `escada-cotas.md` calibrada
