# 4. Montar no VectorCraft sem tela
- Copie a estrutura de `kits/sprint-world-tennis/kit.py` para `kits/<kit>/kit.py`: cores e fontes do kit no topo, os elementos do estilo como funções, uma função `p_<papel>(P)` por página da ficha, e `PAGES` na ordem da ficha.
- Fotos sempre por `foto(...)` e cenas sempre por `cena(...)` (que só usa a gerada aprovada, e só se o arquivo ainda é o que o Ugo viu).
- `P.image(...)` mede a resolução na caixa real; abaixo de 96 ppi vira aviso em `saida/avisos-foto.json`. Imagem baixa de propósito (textura de fundo, cena gerada pela IA) leva `aceito="<motivo>"`.
- `Pagina.fit` estica o texto até a largura máxima: para diminuir, reduza `max_w`, não o tamanho.
- Rode `python3 kits/<kit>/kit.py`. Cerca de 0,5 s por página; saem o PDF e o `.vectorcraft` em `saida/`.
