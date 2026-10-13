# R27. Símbolos e confete (spray)

Status: PARCIAL (o `symbol.spray` sozinho NÃO espalha nem varia; o confete natural sai com `symbol.place` + rotação e escala por instância)

## Sequência que funcionou (R27/teste.py)
1. Desenhar 3 peças vetoriais (estrela `shape.star`, bola `shape.ellipse`, fita `shape.rectangle`), pintar, e transformar cada uma em símbolo: `select.set {ids}` + `symbol.new {name:"estrela"}` (devolve `{id, name}`; a peça vira instância).
2. Confete natural (o que funcionou): para cada instância,
   `symbol.place {name, x, y}` devolve `{id}`;
   `select.set {ids:[id]}`; `object.rotate {angle: aleatório 0 a 360}`; `object.scale {sx: aleatório 70 a 220}`.
   102 instâncias em 1,87 s.
3. `document.exportPdf {path, preserveEditing:false}`.

## O que o spray faz de verdade (medido)
`symbol.spray {points:[[x,y]…], name, radius, density, scale}` coloca UMA instância por ponto. Teste: 1 ponto com `radius:150, density:10` gera `count:1`; 30 pontos em linha com `density:8` geram `count:27` (a densidade só descarta pontos muito próximos num arrasto). `radius` e `density` NÃO espalham instâncias em volta do ponto, e `scale` é constante. Ou seja: a "distribuição natural" tem que vir dos pontos que o script passa (aleatórios, dentro da página: nenhum ponto saiu da artboard porque o script sorteia dentro dela).
`symbol.adjust {tool:"spin"|"size", points, radius, intensity}` funciona, mas só mexe nas instâncias perto dos pontos e dá variação fraca (rotação e tamanho levemente diferentes), insuficiente para confete.

## Veredito visual
Com `symbol.place` + rotação/escala: estúdio, confete vivo, três tamanhos e rotações. Sem isso (só spray): estrelas todas na mesma posição, tamanho e ângulo, cara de carimbo.

## Armadilhas
- Todas as chamadas do spray devolvem o mesmo `id` de conjunto; instâncias do spray ficam em um conjunto (symbol set), as do `place` são objetos soltos editáveis.
- Meu spray de arrasto cruzou o título (composição ruim): o spray não evita texto, tem que desenhar o confete antes e pôr o texto depois, ou evitar a zona.
- Cada instância é uma chamada (3 comandos): 100 peças, 2 s; 1.000 peças, ~20 s.
- Peso do PDF: 557 KB, quase tudo a foto de fundo (não medi só os símbolos).
