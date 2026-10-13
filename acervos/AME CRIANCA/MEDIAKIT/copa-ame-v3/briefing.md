---
cliente: A.M.E (Associação de Menores no Esporte) · @amecrianca
evento: Copa AME, temporada 2027 (43ª edição)
servico: venda de cota de patrocínio
processo: skill v9 (camada de acabamento), teste AME v3 (Parte E do plano de 12/10/2026)
atualizado: 2026-10-13
---

# Briefing do kit A.M.E v3

> **v3, 13/10/2026: teste da skill v9, só horizontal, 18 páginas.** O briefing da v2 segue abaixo, sem mudança.

## Por que existe esta pasta
Teste ponta a ponta da skill v9 (camada de acabamento) com o mesmo cliente da v2. Parte do kit v2 (09/10/2026, 18
páginas, QA 0 falha). `copa-ame` (08/10) e `copa-ame-v2` (09/10) são só leitura: os manifestos sha256 das duas foram
tirados antes do preparo e conferidos depois, idênticos.

## Decisões do Ugo que valem aqui (12/10/2026)
| Decisão | Como entra no kit |
|---|---|
| Só horizontal, 18 páginas | `paginas` no `mediakit.json` lista as 18, na ordem da v2. O vertical não é gerado: render com `--sem-vertical` (o `qa.py` só valida o PDF que existe). As composições `vertical:*` da v2 ficaram no JSON, sem uso |
| Sem teto de peso do PDF | as 5 cenas de 08/10 voltam aos originais de 2752 px (tabela abaixo) |
| Imagem nova só pelo Codex | orçamento de 8 imagens em `assets.json`, seção `v3` |
| Direto até o fim | eu passo os portões e registro cada decisão no fim deste briefing |

## O que veio de onde (preparo de 13/10/2026)
| Item | Origem | Como |
|---|---|---|
| `acervo/`, `fontes/`, `referencia/`, `mood/` | `copa-ame-v2` | clone APFS (`cp -cR`) |
| `compor-apoio.json`, `compor-noite.json`, `insight.md`, `fontes.lock.json`, `tema-projeto.css` | `copa-ame-v2` | clone APFS (`cp -c`) |
| `fontes.md` e `.gitignore` | `copa-ame-v2` | clone APFS. Fora da lista do plano: o `fontes.md` é a tabela de onde sai cada número do kit, e o `.gitignore` mantém `saida/`, as cenas cruas e os registros do Codex fora do git |
| `mediakit.json`, `direcao-de-arte.md`, `assets.json`, `briefing.md`, `pendencias.md` | `copa-ame-v2` | copiados e editados: cabeçalho v3, histórico da v2 preservado |
| as 5 cenas de 08/10 (cru em `acervo/`, tratado em `acervo/tratado/`) e `compor-arb`, `compor-beira`, `compor-proj`, `compor-tr` | `copa-ame` | clone APFS; trocaram as cópias reduzidas a 1936 px que vieram da v2 |
| `acervo/MANIFESTO.json` da v2 | não veio | lista o sha256 do acervo da v2, que aqui mudou em 10 arquivos; a v3 grava o seu no fechamento |
| `saida/` | não veio | o render da v3 cria |

## Cenas originais (as 5 de 08/10)
Na v2 estas cenas foram reduzidas a 1936 px para o PDF caber em 15 MB, com os quads dos painéis reescalados. Na v3
voltam os originais de 2752 px da `copa-ame`, com os quads originais de lá (as composições de lettering e "SEU LOGO
AQUI" foram feitas nessa resolução).

| Cena | Página (id no acervo) | Arquivo na v2 (px) | Original na v3 (px) | `compor-*.json` usado |
|---|---|---|---|---|
| pai e filho | p.2 manifesto (`c-paifilho`) | `acervo/tratado/c-paifilho.jpg` (1936 × 1081) | `acervo/tratado/c-paifilho.jpg` (2752 × 1536); cru `acervo/c-paifilho.png` (2752 × 1536) | nenhum (a cena não tem painel) |
| pórtico | p.8 ativo 1 (`c-projecao`) | `acervo/tratado/c-projecao-composta.jpg` (1936 × 1081) | `acervo/tratado/c-projecao-composta.jpg` (2752 × 1536); cru `acervo/c-projecao.png` (2752 × 1536) | `compor-proj.json` da `copa-ame` (6 painéis) |
| beira do campo | p.10 ativo 3 (`c-beira`) | `acervo/tratado/c-beira-composta.jpg` (1936 × 1081) | `acervo/tratado/c-beira-composta.jpg` (2752 × 1536); cru `acervo/c-beira.png` (2752 × 1536) | `compor-beira.json` da `copa-ame` (4 painéis) |
| transmissão | p.11 ativo 4 (`c-transmissao`) | `acervo/tratado/c-transmissao-composta.jpg` (1936 × 1081) | `acervo/tratado/c-transmissao-composta.jpg` (2752 × 1536); cru `acervo/c-transmissao.png` (2752 × 1536) | `compor-tr.json` da `copa-ame` (1 painel) |
| árbitros | p.16 cota Oficial (`c-arb-cota`) | `acervo/tratado/c-arbitragem-composta.jpg` (1936 × 1081) | `acervo/tratado/c-arbitragem-composta.jpg` (2752 × 1536); cru `acervo/c-arbitragem.png` (2752 × 1536) | `compor-arb.json` da `copa-ame` (3 painéis) |

Como conferi (13/10, scripts no scratchpad, sem escrever nos kits):
- cada arquivo de 1936 px da v2 é a redução do tratado de 2752 px da `copa-ame`: diferença média de 2,3 a 3,2 níveis
  (de 255), o que sobra de duas compressões JPEG;
- os quads da v2 são os da `copa-ame` divididos por 1,4215 (2752 ÷ 1936), com os mesmos textos e a mesma ordem;
- o cru contra o tratado de 08/10: diferença média de 2,5 a 4,3 níveis, e só 0,16% a 0,73% dos pixels mudam mais de 30
  níveis nas 4 cenas com painel (0% no pai e filho), o que bate com os painéis compostos;
- os 10 arquivos na v3 têm o mesmo sha256 dos da `copa-ame` (prova colada no relatório do preparo).

O render lê os painéis de `acervo[].paineis` em px da própria imagem (`camadas.zonas_da_foto`): imagem e quads agora
estão os dois em 2752, então as zonas vendáveis caem no lugar sem reescalar nada.

Fora da lista: a v2 reduziu **6** cenas, não 5. A sexta é `acervo/tratado/c-capa-composta.jpg` (`c-cotas`, a foto do
atleta no divisor de cotas, p.14), que continua aqui em 1936 × 1081. O original de 2752 px está em
`copa-ame/acervo/tratado/c-capa-composta.jpg` (pendência).

### Etapa de assets (preparado, não rodado)
Os tratados de 08/10 já estão em JPEG de qualidade 85 (estimada pela tabela de quantização) e 2752 px, que é o que o
`tratar.py preparar` grava nessa largura (abaixo de 2880 ele não reduz). O render usa esses arquivos como estão. Se a
etapa de assets refizer a composição (outro placeholder, outro corte), parte do cru e dos quads originais, gravando o
composto fora do cru para ele continuar limpo:
```
python3 pipeline/compor.py "<v3>/acervo/c-projecao.png" "<v3>/acervo/c-projecao-composta.png" --lote "<v3>/compor-proj.json"
python3 pipeline/tratar.py preparar "<v3>/acervo/c-projecao-composta.png" "<v3>/acervo/tratado/c-projecao-composta.jpg"
```
O mesmo para `c-beira` com `compor-beira.json`, `c-transmissao` com `compor-tr.json` e `c-arbitragem` com
`compor-arb.json`. O pai e filho só passa pelo `preparar` (`acervo/c-paifilho.png` → `acervo/tratado/c-paifilho.jpg`).

## Formato
`formato.py aplicar sabado-de-campo` (13/10): gravou `formato_base` (`sabado-de-campo` v1, sha256 `a2192d52…`),
preencheu só `direcao_criativa` (intensidade padrão 1 e teto 2, recursos vazios), guardou `mediakit.antes-do-formato.json`
e escreveu 6 pendências de "trocar", confirmadas como mesmo cliente no `pendencias.md`. `formato.py conferir`: 0
diferenças e 0 lacunas.

Para a etapa 3b: a matriz de `criterios-aceite.md` pede intensidade 3 em 5 páginas, acima do teto 2 que veio do formato.
O kit vence o formato: a 3b sobe o teto para 3 e o `conferir` passa a mostrar essa diferença, de propósito.

## Critérios de aceite
`criterios-aceite.md`: metas da Parte F, matriz por página, conferência da própria matriz e tabela de inferência dos
elementos da v2. Gravado antes de qualquer render.

## Decisões durante a execução
(preenchido abaixo, com data, a cada portão ou correção)
- 13/10, preparo: pasta montada só com clones APFS; as 5 cenas de 08/10 em 2752 px com os quads originais;
  `schema_version` mk-2.1; `paginas` com as 18 horizontais; formato aplicado; o resto do `mediakit.json` igual ao da v2.
- 13/10, QA do preparo (`qa.py`, sem render): 25 falhas e 8 avisos, esperados antes da 3b: falta a consulta ao
  repertório, `direcao_criativa.recursos` vazio, `acabamento` em cada uma das 21 composições (18 horizontais e as 3
  `vertical:*` sem uso) e elementos novos (0 de 6, os 6 vieram da v2). Uma falha foi minha: escrevi "2752" na `_nota`
  do `mediakit.json` e o QA cobra prova de todo número no texto; reescrevi a nota sem o número.

---

# Histórico da v2
O `briefing.md` da v2 como estava em 12/10/2026, sem mudança. O cabeçalho YAML dela virou o bloco abaixo.

```yaml
cliente: A.M.E (Associação de Menores no Esporte) · @amecrianca
evento: Copa AME, temporada 2027 (43ª edição)
servico: venda de cota de patrocínio
processo: skill v8 (composição por página + repertório), teste completo pedido pelo Ugo em 09/10/2026
atualizado: 2026-10-12
```

# Briefing do kit A.M.E v2

## Estado final (12/10/2026)
O kit foi entregue em 09/10 e os documentos desta pasta não foram reescritos. Quando um deles diverge do que o kit
virou, vale a coluna "o que vale".

| Documento | O que diz | O que vale | Fonte da verdade |
|---|---|---|---|
| `direcao-de-arte.md` | assinatura `fio` como tempo de jogo de 0' a 90'; microtexto de borda como constante; círculo central atrás do título na capa; a área do campo emoldurando o preço nas cotas; fio ligando o número do ativo ao título; dourado só na Noite das Estrelas | é o plano de antes da execução (09/10). O 0' a 90' não foi implementado: `render.py:injetar_fio` só desenha a linha de progresso no rodapé. O microtexto saiu das constantes, o círculo central saiu da capa, a área saiu das cotas e o fio do ativo não entrou; o troféu dourado também aparece na cota Master (decisões de 09/10, abaixo) | `mediakit.json` (`receitas`, `sistema_elementos`, `composicao`) e o render em `saida/` |
| `assets.json` | âncora e escala de cada asset (apito "sobrepõe 1/3 da borda esquerda da foto"; troféu com "1/2 da altura da página"; bola com "2 alturas de maiúscula") | âncoras de antes da maquete. Valem as da `composicao`: apito sobrepõe 1/2 da foto, na altura do título; troféu de pé dentro da foto, na base da caixa, com 1/3 da página; bola com 3 alturas de maiúscula, pousada na 1ª linha do título | `mediakit.json` → `composicao` |
| `mediakit.json` → `pendencias` | 7 pendências da rodada de 08/10 (por exemplo, "o kit usa Inter Display" e cenas do Higgsfield como "plano B sem Codex") | é histórico da rodada de 08/10: a fonte do kit é Barlow e as cenas novas são do Codex. Vale o `pendencias.md` (09/10) | `pendencias.md` |
| `composicao` → `vertical:contato` (e o resumo da vertical, abaixo) | a composição escreve "foto da equipe com véu"; o resumo diz "contato com o campo vazio" | vale o que a composição manda: escudo e contatos centrados, sem elemento, padrão `a-foto-manda-zona-lisa-e-fuga`. A foto que o render usa é a do contato, o campo vazio (`saida/png/kit-r1-vertical-03.png`) | `composicao.vertical:contato` e o render |

Formato: este estado final virou o formato `sabado-de-campo` v1 da skill (`SISTEMAS/GERAR MEDIAKIT/formatos/sabado-de-campo/`),
exportado sem ler o `direcao-de-arte.md`. Git: acervo leve (`.gitignore`, `fontes.lock.json` e `acervo/MANIFESTO.json`,
que lista com sha256 inclusive o que fica fora do git).

**Ressalva:** se o cofre ganhar repositório remoto (hoje o git é só local, sem remoto), as fotos `real-*` (crianças da
A.M.E: `acervo/real-*-recorte.png` e `acervo/tratado/real-*.jpg`) saem do rastreio ANTES do primeiro envio.

## Por que existe esta pasta
O Ugo pediu (09/10/2026) um teste ponta a ponta da skill nova com outro cliente, usando o PDF "Patrocinadores 2026" e
os prints do Instagram e do YouTube. A pasta `copa-ame` (kit de 08/10, processo antigo) fica intacta para comparação.

## Insumos
- PDF do cliente "Patrocinadores 2026" (22 páginas): fotos reais recuperadas em `acervo/` e `acervo/pdf/`.
- 8 prints das redes em `referencia/` (perfil, painel profissional, grade de reels, canal TV AME).
- Conteúdo aprovado do kit de 08/10 (provas, inventário, cotas, contato).
- Cenas geradas em 08/10 (pai e filho, pórtico, beira do campo, transmissão): reaproveitadas porque já existem;
  foram feitas no Higgsfield, que agora saiu da skill (decisão do Ugo, 09/10). Nada novo sai do Higgsfield.

## Portões passados por mim (o Ugo mandou seguir direto até o fim, 09/10)
| Portão | Decisão | Por quê |
|---|---|---|
| Cotas | Master R$ 18.000 (1), Oficial R$ 6.000 (4), Apoio R$ 2.400 ou permuta (8), por semestre, sem selo | decisão do Ugo em 09/10 ("tá certo os valores, pode manter sem nenhum selo") |
| Números de público | 750 a 800 equipes, cerca de 10 mil atletas e 10 mil famílias, tipo informado | decisão do Ugo em 08/10 (resposta do Nicollas) |
| Fotos com crianças | autorizadas | decisão do Ugo em 08/10 |
| Patrocinadores citáveis | todos os 7 atuais | decisão do Ugo em 08/10 |
| Receita | uma só ("Sábado de campo"), levada ao máximo, mais a vertical | decisão do Ugo em 09/10 |
| Imagem nova | só Codex; se falhar, repetir no Codex | ordem do Ugo em 09/10 |
| Copy | tese, manifesto, títulos e texto da Noite das Estrelas abaixo | passei o gate; registro aqui |
| Página de projeção | fora do kit | a A.M.E não tem arena; a cena do pórtico aparecia em 4 páginas no kit de 08/10 |

## Gate de copy (aprovado por mim, com o critério da skill)
- CAPA: "Dez mil atletas em campo. E a família inteira na beira dele." (11 palavras)
- MANIFESTO: "Um pai criou|um campeonato" / "para o filho ter onde jogar." / caixa: Walter Neves, 2005, e os
  ex-atletas Luan, Igor Gomes, Delatorre e Zeca (nomes informados pelo organizador; foto deles não entra, sem direito).
- PÚBLICO: 10.000 atletas · 750 equipes · 10.000 famílias (informado).
- QUEM JÁ JOGA: as 7 marcas de 2026, com o backdrop real como prova.
- TERRITÓRIO: "Quatro cidades,|uma copa" (Rio Preto, Araçatuba, Taquaritinga, Bauru). Era "um campeonato"; encolhia 34% no título.
- ATIVOS: 01 "Sua marca no||nome da copa" · 02 "na||arbitragem" · 03 "na||beira do campo" · 04 "na||transmissão ao vivo" ·
  05 "na||Noite das Estrelas".
- COTAS: Master (nome da copa), Oficial (camisa da arbitragem), Apoio (beira do campo).
- CONTATO: Júnior (17) 99147-2050 · Nicollas (17) 99711-1195 · @amecrianca.

## Direção de arte
`insight.md` e `direcao-de-arte.md`. Ideia: "a marca entra em campo junto com a família". Receita r1 "Sábado de campo"
(Barlow Condensed 800 e Barlow; preto, amarelo A.M.E, branco, papel; dourado só na Noite das Estrelas).

## Plano de páginas (18) e composição (final, 09/10)
A composição de cada página está em `mediakit.json` → `composicao` (mensagem, foco, leitura, estrutura, padrões do
repertório e elementos ancorados). Resumo do que foi entregue:
| # | Página | Foco | Elemento e âncora | Padrão do repertório |
|---|---|---|---|---|
| 1 | capa (c), cena nova do campo | escudo | goleiro real à direita do escudo, entra por trás da faixa amarela (que esconde o corte da cintura) | figura-recortada-atravessa-a-borda |
| 2 | manifesto | título | nenhum: a foto manda | a-foto-manda-zona-lisa-e-fuga |
| 3 | público (b) | número | nenhum: o número é o herói | numeral-heroi-com-legenda-travada |
| 4 | quem já joga | backdrop | cantoneiras emolduram o backdrop real; mascote real com árbitros entra pela base, na borda do título | mural-de-logos, marca-na-superficie-do-ativo |
| 5 | território | mapa | mapa das 4 sedes (5 colunas), no eixo do texto, domina a direita | percurso-e-mapa-como-argumento |
| 6 | alcance digital | números | nenhum | dados-em-modulos |
| 7 | divisor (c) | número | metade do campo sangra pela direita na altura do título; pattern dos objetos do jogo na faixa de cima | grafismo-do-equipamento-do-esporte |
| 8 | ativo 01 nome da copa (topo) | foto | nenhum: a tabela real da rodada é a prova | marca-na-superficie-do-ativo |
| 9 | ativo 02 arbitragem | foto | apito e cartões cruzam a borda da foto na altura do título | figura-recortada-atravessa-a-borda |
| 10 | ativo 03 beira do campo (sangria) | foto | bola pousada na primeira linha do título | peca-em-estudio |
| 11 | ativo 04 transmissão (diagonal) | foto | placar da TV AME no painel, na borda do título, sobre a caixa de aplicações | placar-como-estrutura |
| 12 | ativo 05 Noite das Estrelas | troféu | troféu dourado de pé na foto, na base da caixa; 5 estrelas ao lado do 05 | um-motivo-em-varios-papeis |
| 13 | inventário (papel) | lista | fios separam os itens | fio-que-organiza-a-informacao |
| 14 | divisor de cotas | título | nenhum | a-foto-manda-zona-lisa-e-fuga |
| 15 | cota Master (a), cena nova das equipes perfiladas | preço | troféu de pé na base da caixa de direitos, já no gramado | cabecalho-de-cota-e-preco-heroi, peca-em-estudio |
| 16 | cota Oficial (a), árbitros com o peito liso | preço | apito e cartões na base da caixa de direitos | idem |
| 17 | cota Apoio (a), cena nova das placas na grade | preço | bola na base da caixa de direitos, no gramado diante das placas | idem |
| 18 | contato (b), cena nova do campo vazio | título | o goleiro da capa volta, cortado pela base | um-motivo-em-varios-papeis |
Vertical: capa com a foto do campo recortada em volta do jogo e a faixa de advertência na borda de baixo; números e
cota Master sem grafismo; contato com o campo vazio.
Constantes: faixa de advertência no canto de cima (mesma caixa em todas as páginas, fora das cotas), grão.

## Decisões durante a execução
(preenchido abaixo, com data, a cada portão ou correção)
- 09/10, maquete 1: a maquete mostrou 6 problemas antes de qualquer asset: goleiro atrás da tese na capa, apito encostando no título, bola dentro da caixa de aplicações, placar sobre o texto, mascote fora da página no inventário e grande área estreita passando atrás dos direitos nas cotas. Recompus com as medidas reais dos alvos.
- 09/10, maquete 2: a `fracao` do sobrepõe é quanto o objeto ENTRA na foto (1/3 entra, 2/3 ficam fora); corrigido no apito (1/2) e no troféu (de pé dentro da foto, na linha de base da caixa). A faixa amarela da capa foi medida nas coordenadas reais para esconder o corte da cintura do goleiro.
- 09/10, constantes: o microtexto de borda saiu (a caixa única batia no logo do canto, no crédito e no título em 9 páginas); a faixa de advertência foi para a borda de cima.
- 09/10, cotas: em vez da grande área atrás do preço (atravessava a lista de direitos), cada cota leva o objeto do território dela ao lado do nome: troféu na Master, apito e cartões na Oficial, bola na Apoio. O mesmo objeto da página de ativo, em outro papel.
- 09/10, ativo 1 (naming) e público: sem elemento; a prova (a tabela real da rodada) e o número são o que a página precisa.
- 09/10, Noite das Estrelas: cena gerada no Codex com o prompt da composição; o Codex pôs um símbolo de marca no peito das crianças e o `cena_limpar.sh` apagou; "SEU LOGO AQUI" composto no backdrop do palco (zona vendável protegida).
- 09/10, primeiro render completo: 36 falhas no QA. Corrigidas na origem (configuração do kit ou regra da skill, nunca
  silenciando o aviso):
  - capa, cotas e contato sem cena (a gramática exige imagem): 4 cenas novas no Codex (campo de sábado; equipes
    perfiladas antes da final; placas lisas na grade com as famílias; campo vazio com o gol). Prompt com a cena decidida
    aqui e o bloco Composition da maquete (painel de texto, escudo e objeto como áreas calmas). Placas da Apoio com
    "SEU LOGO AQUI" composto em perspectiva (`compor-apoio.json`, cantos medidos na imagem);
  - cotas na variante a (cena inteira com painel), cada uma com a foto do território que vende; a Oficial reaproveita a
    cena dos árbitros de 08/10, que não estava em uso;
  - três direitos da Master reescritos mais curtos para caber na página com foto, sem mudar nenhum direito: "Copa AME +
    sua marca na tabela, no app e nos posts", "Janela fixa no app, com link direto ao seu WhatsApp", "4 placas e 2 wind
    banners no campo, aos sábados";
  - herói na capa, no divisor (metade do campo), na transmissão (placar da TV AME) e nas 3 cotas: cobertura 12 de 17;
  - família da receita: meio "foto-objeto" e luz "esquerda" (estava "foto", que não existe no vocabulário); bola e
    troféu espelhados porque a luz medida vinha da direita (peças simétricas; o bruto do Codex fica intacto); o apito
    aceito com o motivo registrado (a medida pega o cordão preto à esquerda); goleiro e mascote, fotos reais, aceitos
    fora da medida da família. Família aprovada por mim (portão delegado);
  - exclusividade dos recortes reais com o nome do cliente do kit ("A.M.E");
  - pattern novo do kit: objetos do jogo vistos de cima (Codex, família da receita), a 10% no divisor;
  - círculo central saiu da capa (cruzava a tese e encostava no escudo) e a grande área saiu da vertical (passava
    atrás do preço e dos direitos);
  - território: título mais curto e mapa de 5 colunas no eixo do texto;
  - arco tracejado do arquétipo de cota apagado (`tema-projeto.css`, token `--acento-curva`) e faixa de listras fora
    das 3 cotas: o amarelo passava de 8 papéis;
  - PDF de 16,9 MB: as 6 cenas de 08/10 reduzidas a 1936 px (altura de página) nesta pasta, com as zonas vendáveis
    reescaladas; os originais continuam em `copa-ame`. Ficou em 14,4 MB;
  - backdrop ampliado para preencher o painel do "quem já joga".
- 09/10, regras da skill corrigidas pelo teste (com prova): data do evento só com o ano, posição de entregável no
  futebol, elemento-foco da composição conta como dominante, texto em foto real é aviso (não falha), vocabulário de
  cota e contato no futebol, painel de texto como área calma no prompt de cena.
- 09/10, resultado: QA 0 falha e 21 avisos, todos explicados em `pendencias.md`.

## Decisões do coordenador depois do preparo (13/10/2026, sem portão: "direto até o fim")
1. A sexta cena reduzida (p.14, `tratado/c-capa-composta.jpg`) também volta ao original de 2752 px da `copa-ame`, pelo mesmo motivo das outras cinco (feito na etapa de assets, antes do primeiro render).
2. F1 (fita de advertência) e M3 (estrelas douradas) entram como família `ornamento-identidade`: a matriz fecha (OI em 6 páginas, 3D em 4) e a tabela de rota da skill já põe fita e estrelas nessa família; a imagem continua sendo objeto 3D pelo Codex com `material`.
3. Novidade de elementos: a conta do QA (herói, ornamento, apoio, pattern) dá 8 de 14 com as 8 imagens previstas (57%, abaixo dos 60%). A 3b decide entre uma nona imagem e um elemento da v2 a menos; a textura de cal e a terra vermelha entram com papel `acabamento` (rota textura única), não como pattern.
4. As três composições `vertical:*` ficam no JSON (gramática do formato), mas o kit não gera vertical: o render roda sem vertical e o QA passa a pular `vertical:*` quando o kit não tem página vertical nem PDF vertical (mudança pequena no qa.py, com prova, feita na skill antes do primeiro QA da v3).
5. Teto de intensidade sobe para 3 na 3b (o kit vence o formato; a diferença no `conferir` é de propósito e fica registrada aqui).
6. O `acervo/MANIFESTO.json` da v3 nasce no fim, com o acervo final.
