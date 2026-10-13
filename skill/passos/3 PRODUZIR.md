# 3. Produzir as imagens
- Antes de gerar, procure na biblioteca de peças (`python3 -c "from mediakit import pecas; print(pecas.listar('camisa'))"`) uma base que sirva.
- Cena com marca: gere já com o logo anexado (`src/mediakit/imagens/gerar_cena.sh <id> <prompt> <acervo> <logo> [outras]`). O prompt pede: logo exatamente como o arquivo, nenhum outro texto, e "não regenere se a conferência falhar; liste os defeitos". Só use a rota compor (logo colado) se a gerada errar o logo.
- Gere só o número de imagens que o Ugo aprovou; cada uma fica em `acervo/cota.json`.
- Confira cada cena no olho: logo fiel ao oficial, logo fantasma, cenário inventado. Aprovada: `python3 -c "from mediakit import cenas; cenas.marcar('<acervo>', '<arquivo>', 'usar')"`.
- Elementos decorativos (faixas, raias, padrões) não são gerados: saem do livro de receitas (`receitas/indice-*.md`), novos a cada kit.
