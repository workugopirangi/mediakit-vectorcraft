# Pendências · Copa AME 2027 (v2, 09/10/2026)

## Com a A.M.E (antes de enviar às marcas)
- [ ] Aprovar as cotas (Master R$ 18.000, Oficial R$ 6.000, Apoio R$ 2.400 ou permuta, por semestre). O Ugo validou os valores em 09/10; falta a A.M.E.
- [ ] Logo em vetor (SVG, AI ou PDF). Hoje só existe em raster pequeno, ampliado 3 vezes.
- [ ] E-mail de contato. O contato usa @amecrianca.
- [ ] Data de início da temporada 2027. A capa mostra só o ano.
- [ ] Onde o brinde da cota Apoio é entregue ("Brinde da marca em dia de jogo" não diz o lugar).
- [ ] Camisa do goleiro (capa e contato) e do árbitro com o mascote (p.4): o leitor de texto achou marcas reais nas camisas. Confirmar que podem aparecer; se não, o atleta da p.14 entra no lugar do goleiro.
- [ ] Foto original do goleiro em tamanho maior, se existir (o recorte tem 1164 px; na capa ele aparece com 617 px, abaixo de 2x).
- [ ] Confirmar os ex-atletas citados no manifesto (Luan, Igor Gomes, Delatorre, Zeca): nome informado, sem foto.
- [ ] Se a parceria com a Record TV continua em 2027. Hoje não aparece no kit (só há prova de 2024).

## Imagens
- Cenas de 08/10 (pai e filho, pórtico, beira do campo, transmissão, árbitros) vieram do Higgsfield, que saiu da skill em 09/10. Reaproveitadas porque já existiam; todas rotuladas como projeção ou imagem ilustrativa. Nesta pasta estão reduzidas a 1936 px (o PDF passava de 15 MB); os originais seguem em `copa-ame`.
- Cenas novas pelo Codex em 09/10: Noite das Estrelas, capa (campo de sábado), cota Master (equipes perfiladas), cota Apoio (placas na grade, "SEU LOGO AQUI" composto) e contato (campo vazio). Peças: apito e cartões, bola, troféu e o pattern dos objetos do jogo. Bola e troféu espelhados para a luz vir da esquerda, como nas cenas.
- Fotos reais da A.M.E (equipe, arbitragem, goleiro, mascote com árbitros, backdrop, tabela do app) recuperadas do PDF "Patrocinadores 2026". Fotos com crianças autorizadas pelo Ugo em 08/10.

## Avisos do QA aceitos (QA final: 0 falha, 21 avisos)
| Aviso | Por que fica |
|---|---|
| data do evento só com o ano | pendência acima; a capa mostra "2027" |
| entregável do Apoio sem posição (brinde) | texto aprovado pelo cliente; pendência acima |
| sem página de projeção | decisão: a A.M.E não tem arena, e o pórtico aparecia em 4 páginas no kit de 08/10 |
| goleiro e mascote fora da medida da família | fotos reais do cliente; a família é de peças de estúdio. Aceito por mim (portão delegado) |
| apito fora da medida da luz | a medida pega o cordão preto à esquerda; o brilho do metal vem da esquerda. Aceito com o motivo |
| texto lido nas camisas (goleiro, mascote) | marca real na roupa; pendência acima |
| goleiro abaixo de 2x | é o maior recorte que existe; pendência acima |
| ritmo: 6 páginas sem página de impacto até a p.7 e a p.13 | é a sequência-mestre da skill; a bancada Corre por Elas tem o mesmo aviso |
| amarelo em 7 e 8 papéis nas cotas | dentro do limite (8); acima dos 6 do Corre por Elas |
| contato com blocos fora das colunas | o contato b é centrado por desenho |
| mascote, metade do campo e goleiro encostam no fio do rodapé | os três sangram pela base e cruzam o fio de propósito |
| estrelas pequenas na Noite das Estrelas | são as 5 estrelas do escudo, ao lado do 05; pequenas por desenho |
| cena da Master sem "SEU LOGO AQUI" | a foto não tem superfície de marca; o nome da copa aparece na tabela (p.8) e no placar (p.11) |
| PDF com imagens a 96 ppi | as cenas ocupam a página inteira a 1x (1920 a 1936 px numa página de 1920) |

Nenhum aviso de elemento "solto" no QA final: o único (o goleiro da capa, preso ao escudo por deslocamento nos dois eixos) foi resolvido prendendo o goleiro à faixa diagonal (sobrepõe).

## Sistema (registro do teste)
- A página de projeção saiu: a A.M.E não tem arena, e a cena do pórtico aparecia em 4 páginas no kit de 08/10.
- O microtexto de borda saiu das constantes: a caixa única batia no logo do canto, no crédito da foto e no título em 9 páginas.
- `tema-projeto.css` só com o token `--acento-curva: transparent` (o arco tracejado da cota virava o nono papel do amarelo).
