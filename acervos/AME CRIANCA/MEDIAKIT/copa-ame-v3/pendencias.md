# Pendências · Copa AME 2027 (v3)

> **v3, 13/10/2026: teste da skill v9, só horizontal, 18 páginas.** As pendências da v2 seguem abaixo, sem mudança;
> as que são com a A.M.E (cotas, logo em vetor, e-mail, data, camisas, ex-atletas, Record TV) continuam abertas.

## Preparo da v3 (13/10/2026)
- [ ] Sexta cena reduzida da v2: `acervo/tratado/c-capa-composta.jpg` (`c-cotas`, divisor de cotas, p.14) continua em
  1936 px. O plano lista 5 cenas; o original de 2752 px está em `copa-ame/acervo/tratado/c-capa-composta.jpg`.
  Recomendo voltar ao original pelo mesmo motivo das outras 5 (sem teto de peso).
- [ ] Teto de intensidade: o formato trouxe `direcao_criativa.intensidade` com teto 2; a matriz pede 3 em 5 páginas.
  Subir o teto na etapa 3b (o kit vence o formato; o `formato.py conferir` passa a mostrar a diferença).
- [ ] Matriz de `criterios-aceite.md`: a família OI só aparece por meio de F1 (fita) e M3 (estrelas); F1 está em 4
  páginas e F2 em 3 (a meta é 6 ou mais); a p.14 só tem 2 famílias se F1 contar como família. Fechar na composição.
- [ ] As composições `vertical:capa`, `vertical:numeros` e `vertical:contato` ficaram no `mediakit.json`, sem uso: o
  kit é só horizontal e o render roda com `--sem-vertical`. O QA do mk-2.1 já cobra `acabamento` nelas (3 das 21
  falhas de acabamento do QA de 13/10). Saídas: tirar as 3 do kit (o `formato.py conferir` passa a mostrar a diferença
  se a gramática do formato as tiver) ou o QA pular `vertical:*` quando o kit não gera vertical (mudança na skill).
- [ ] Elementos novos: o QA só conta papel herói, ornamento, apoio ou pattern (não `acabamento`). Com os 6 da v2 e as 8
  imagens novas, ficam 8 de 14 (57%), abaixo dos 60%: 1 imagem a mais ou 1 elemento da v2 a menos, e uma textura
  nova com papel `pattern` (`criterios-aceite.md`, seção 4).
- [ ] `acervo/MANIFESTO.json` da v3 no fechamento (o da v2 não veio: descrevia outro acervo).
- Nota, sem regra: o PDF não tem teto de peso (ordem do Ugo, 12/10). Um PDF muito pesado pode não passar por e-mail ou
  WhatsApp; o tamanho sai como informação no relatório.

## Formato sabado-de-campo v1 (aplicado em 13/10/2026)
O formato trava receita, constantes, família modelo e gramática; o que é do cliente fica aqui até ser trocado (formato.py conferir mostra o que falta).
- [x] Trocar `receitas[].paleta.marca`, `marca.cor_primaria`, `marca.cor_secundaria`: a cor da marca do cliente (acento) e o tom claro dela (na origem: #F5D80A, #FFF6B8). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.
- [x] Trocar `receitas[].paleta.apoio`: a cor de apoio do cliente (na origem: #C9A227). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.
- [x] Trocar `sistema_elementos.motivos[advertencia]`: motivo de origem simbolo do cliente (na origem: a faixa preta e amarela dos posts da A.M.E). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.
- [x] Trocar `sistema_elementos.motivos[estrelas]`: motivo de origem simbolo do cliente (na origem: as 5 estrelas do escudo e a Noite das Estrelas). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.
- [x] Trocar `marca.estilo_cena`: o bloco de estilo das cenas: momento, lugar, material da paisagem e cor das roupas do cliente; a luz, a lente e a atmosfera ficam como no modelo (na origem: momento 'Saturday morning'; lugar 'the interior of São Paulo state'; material 'red earth and tall trees'; cores 'black and yellow'). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.
- [x] Trocar `marca.logo_id`, `acervo[logo]`: o logo do cliente (na origem: acervo/logo-ame-320-x3.png). Confirmado, mesmo cliente (13/10/2026): a v3 é da A.M.E.

---

# Histórico da v2
O `pendencias.md` da v2 como estava em 09/10/2026, sem mudança.

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
