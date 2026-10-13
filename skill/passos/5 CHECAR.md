# 5. Checar (até 3 voltas) e aprovação 2
1. `PYTHONPATH=src python3 -m mediakit.checagem.checar <pdf> <ficha.md>`: falha barra (sobreposição pela tinta, travessão, arquivo); aviso vai para o Ugo (número fora da ficha, foto abaixo de 96 ppi).
2. Renderize as páginas (`pdftoppm -r 96 -png <pdf> <pasta>/pag`) e olhe todas, com a ficha e a referência ao lado.
3. Revisor independente: um subagente com modelo explícito (sonnet) e o prompt de `prompt_revisor(...)` (`src/mediakit/checagem/checar.py`). Confira no olho cada achado grave antes de agir: achado sem prova não vira correção.
4. Corrija e volte ao 1. No máximo 3 voltas. O que for decisão do Ugo (cota, uso de imagem de terceiro, cenário inventado pela IA, divergência da ficha) sai da volta e vai para a aprovação 2.
5. Aprovação 2 por AskUserQuestion: o PDF aberto, o que foi corrigido, o que ficou e por quê, e as decisões pendentes, cada uma com recomendação.
