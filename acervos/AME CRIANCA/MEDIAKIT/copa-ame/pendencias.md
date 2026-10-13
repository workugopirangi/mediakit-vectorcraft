# Pendências · kit A.M.E (08/10/2026)

## Antes de enviar ao Nicollas (Ugo)
- [ ] Revisar os preços das cotas em `cotas-proposta.md`. Para mudar: me diga os valores e eu altero o `mediakit.json` e renderizo de novo.
- [ ] Escolher a direção: **causa** (recomendada; está também como `AME - Midia Kit de Patrocinio 2027.pdf`), performance ou território.

## Com o Nicollas
- [ ] Aprovar as cotas (preço, quantidade, entregáveis).
- [ ] Logo em vetor (SVG, AI ou PDF). Hoje só existe em raster de 320 px, ampliado 3×.
- [ ] E-mail de contato. O contato usa @amecrianca por enquanto.
- [ ] Data de início da temporada 2027. A capa mostra "Temporada 2027".
- [ ] O que significa o "1.000 a 2.000" da resposta 3.4.
- [ ] Se a parceria com a Record TV continua em 2027. Hoje não aparece no kit, porque só há prova de 2024.

## Sistema
- **Fontes:** RocGrotesk não existe neste ambiente; usei Inter Display, TeX Gyre Heros Cn e Poppins (licenças livres). Quando os arquivos da RocGrotesk estiverem no vault, o render refeito leva minutos.
- **Cenas geradas por IA:** projeção, arbitragem, transmissão, beira do campo e pai e filho saíram do Higgsfield (Nano Banana 2, 10 créditos). É o plano B, porque não há Codex e o plano gratuito bloqueia o GPT Image. Todas estão rotuladas como "projeção ilustrativa". A logo da marca de bola foi apagada da cena da arbitragem.
- **Repetição:** a cena do pórtico aparece na projeção, no ativo 01, na capa (desfocada) e na cota Master. Sem créditos para gerar mais; trocar quando houver.
- **Mudança no pipeline:** `render.py` e `qa.py` agora aceitam `data_inicio` só com o ano (vira "Temporada AAAA"). O exemplo Travessia da Lua continua com 0 falhas. A bancada Corre por Elas não foi montada, então a regressão completa está pendente.
- **Diferença entre as direções:** as três mudam só a tipografia. Máscara diagonal e arquétipos de futebol ainda não existem.
- **Kit antigo:** a foto de 1.265 px que parecia ser a logo é, na verdade, um goleiro recortado. Fica no acervo como opção de foto.
