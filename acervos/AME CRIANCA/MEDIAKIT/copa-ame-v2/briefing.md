---
cliente: A.M.E (Associação de Menores no Esporte) · @amecrianca
evento: Copa AME, temporada 2027 (43ª edição)
servico: venda de cota de patrocínio
processo: skill v8 (composição por página + repertório), teste completo pedido pelo Ugo em 09/10/2026
atualizado: 2026-10-12
---

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
