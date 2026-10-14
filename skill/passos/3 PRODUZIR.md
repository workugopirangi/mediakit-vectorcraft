# 3. Produzir as imagens
- Antes de gerar, procure na biblioteca de peças (`python3 -c "from mediakit import pecas; print(pecas.listar('camisa'))"`) uma base que sirva.
- Cena com marca: gere já com o logo anexado (`src/mediakit/imagens/gerar_cena.sh <id> <prompt> <acervo> <logo> [outras]`). O prompt pede: logo exatamente como o arquivo, nenhum outro texto, e "não regenere se a conferência falhar; liste os defeitos". Só use a rota compor (logo colado) se a gerada errar o logo.
- Gere só o número de imagens que o Ugo aprovou; cada chamada (deu certo ou não) fica em `acervo/cota.json`.
- **Se a geração falhar, pare e pergunte ao Ugo** por AskUserQuestion (tentar de novo gasta outra chamada). O script tenta uma vez só.
- Confira cada cena no olho: logo fiel ao oficial, logo fantasma, cenário inventado. Aprovada: `python3 -c "from mediakit import cenas; cenas.marcar('<acervo>', '<arquivo>', 'usar')"`.
- Pessoa ou produto recortado (pessoa saindo do quadro, texto atrás da pessoa): `scripts/py src/mediakit/ferramentas/recortar.py <foto> <saida.png> --classe atleta|pessoa-livre|produto|equipamento`. Se o modelo ainda não estiver baixado, ele para e diz o tamanho: pergunte ao Ugo antes de baixar.
- Cena gerada com letra ou logo inventado (logo fantasma): `src/mediakit/ferramentas/cena_limpar.sh` (gasta uma chamada do Codex; uma tentativa só).
- Elementos decorativos (faixas, raias, padrões) não são gerados: saem do livro de receitas (`receitas/indice-*.md`), novos a cada kit.
