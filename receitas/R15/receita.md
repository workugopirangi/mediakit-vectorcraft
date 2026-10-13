# R15. Tabela de cotas com tabulação e líder pontilhado

Status: PARCIAL (tab direita e decimal funcionam; o líder pontilhado NÃO é desenhado, existe plano B)

## Sequência que funciona (R15/teste.py)
A) Tab direita: `text.create {..., text:"Item\tR$ 120.000,00\nItem2\tR$ 75.000,00", area:{width:760, height:200, fit:"none"}}` (o \t da string vira tabulação), `text.setStyle {ids, leading:46}`, `select.set {ids:[t]}` + `text.tabs.set {ids:[t], stops:[{position:760, align:"right"}]}` devolve {stops:1}. Valores terminam todos em 760 pt, alinhados.
C) Tab decimal: `stops:[{position:300, align:"decimal", alignOn:","}]`. Medido com `pdftotext -bbox`: a vírgula de 120.000,00, 75.000,00, 38.500,00, 9.900,00 e 850,5 cai em x = 1260,0 pt nos cinco (todos alinhados, inclusive o valor sem casas de milhar).

## O defeito: líder
`leader` é aceito (devolve {stops:1}, sem erro) com ". ", ".", "..", "-", "· " e "_", mas NENHUM ponto é desenhado no PDF (pdftotext e o PNG não mostram nada). Testei seis valores; confirma o aviso "leader drawing not verified" do plano. NÃO usar.

## Plano B que funciona (bloco B do teste)
Rótulo e valor em objetos de texto separados; obter bounds com `document.inspect {depth:3}`; mover o valor com `object.move {dx}` para terminar na coluna; `shape.line {x1,y1,x2,y2}` do fim do rótulo (+12) ao início do valor (-12) com `paint.setStroke` ouro e depois `stroke.set {weight:2.2, cap:"round", dash:[0,7]}` (dash 0 com cap round desenha pontos). Resultado: linha de pontos limpa e vetorial. Custo: tabela deixa de ser um texto só (3 objetos por linha), mais código.

## Aparência
Qualidade de estúdio nos blocos A (sem líder) e C; o B ficou correto, pontos discretos (2,2 pt a cada 7 pt). Fonte Helvetica Neue embutida, sem rasterização, PDF de 24 KB.
