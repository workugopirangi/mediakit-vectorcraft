---
tags: [MP]
tipo: nota
status: ativo
updated: 2026-10-13
autor: agente
---

# Gerar a cena já com o logo; compor só quando a geração errar

**Decisão (13/10/2026, teste Sprint × World Tennis):** as cenas com marca são geradas pelo GPT Image com o logo anexado. A rota "compor" (logo colado sobre cena limpa, `compor.py` da v9) vira reserva.
**Evidência:** pórtico, estande e camisa foram feitos pelas duas rotas e comparados lado a lado. A gerada ganhou nas 3: logo fiel e integrado à luz; a composta pôs o logo numa tenda de massagem.
**Custo:** cada cena gerada gasta 1 imagem da cota do ChatGPT; o kit registra em `cota.json` e nunca regera sozinho.
**Limite conhecido:** o gerador entrega 1672 px (84 ppi em página cheia) e às vezes inventa cenário (roda-gigante no pórtico). Por isso toda cena gerada leva o selo "projeção ilustrativa".
