# R12. Recursos OpenType (tnum, smcp, onum, ss01...)

Status: PARCIAL (os recursos passam para o PDF; mas tnum não é demonstrável nas fontes testadas, e há limites de lista e de fonte)

## Sequência (R12/teste.py)
1. `text.create {...}` e `text.setStyle {ids:[t], features:["onum"]}` (lista aceita: liga, calt, dlig, smcp, frac, onum, tnum, ordn, swsh, ss01 a ss20, salt, titl, pnum, lnum, sups, subs; prefixo "-" desliga). `c2sc` e `zero` são REJEITADOS com erro explícito.
2. Para small caps também existe `text.setRangeStyle {id, smallCaps:true}`.
3. Fonte Arboria (instalada em ~/Library/Fonts): o nome da família é o nome do arquivo e o estilo é o símbolo "☞". Usar `font:"Arboria-Bold", style:"☞"`. Com `font:"Arboria"` o texto cai em Source Sans 3 em silêncio (`text.fonts` mostra status missing). Confirme sempre com `text.fonts` e `pdffonts`.

## Resultado por recurso (medido com `pdftotext -bbox` e diferença de pixels)
- `pnum` (Arboria): FUNCIONA. "11.111" fica com 143,5 pt contra 171,7 pt do padrão: largura proporcional de verdade.
- `tnum`: aceito, mas SEM efeito visível porque os numerais padrão de Helvetica Neue e de Arboria já são tabulares (11.111 e 88.888 têm a mesma largura, 165,1 pt em Helvetica e 171,7 em Arboria, com ou sem tnum). Não consegui provar o recurso em fonte de numeral proporcional por padrão. Para colunas alinhadas, as duas fontes já servem sem fazer nada.
- `onum` (Arboria): FUNCIONA (numerais antigos; largura muda de 172,5 para 166,8).
- `ss01` e `salt` (Arboria): FUNCIONAM (diferença de pixels confirmada; mudança sutil em P, Q, R). `dlig`, `swsh`: aceitos, sem glifos na fonte (sem diferença).
- `smcp`: FUNCIONA em Avenir Next e Source Sans 3 (minúsculas viram versaletes verdadeiros). Em Arboria-Medium, `smcp` por features só encolheu a maiúscula inicial, comportamento estranho: evitar. Em Helvetica Neue (sem smcp) o `features` não faz nada, mas `text.setRangeStyle {smallCaps:true}` gera versaletes sintéticos (letras reduzidas, traço um pouco mais fino que o ideal).
- `lnum`: aceito; sem diferença visível (já é o padrão).

## Aparência e cuidados
Texto limpo, fontes embutidas e conferidas no pdffonts (Arboria como CID Type 0C, Avenir Next TrueType). Nada rasteriza; PDF de 22 KB.
Recomendação para kit: rótulos em versaletes com Avenir Next + smcp ou `smallCaps:true`; números com Arboria (onum só se o design pedir); não depender de tnum.
