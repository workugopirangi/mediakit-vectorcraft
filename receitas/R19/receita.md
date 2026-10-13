# R19. Auditoria de glifos ausentes

Status: FUNCIONA (com um contorno: o relatório é por fonte, não por caractere)

## O que o comando entrega de verdade
`text.fonts {selectionOnly:false}` devolve uma linha por fonte+estilo com `missingGlyphs` (CONTAGEM de caracteres que a fonte não tem) e `objects`. Não diz qual texto nem qual caractere. Para fechar o relatório foi preciso montar o laço abaixo (todos os comandos reais, rodou).

## Sequência que funcionou (R19/teste.py)
1. `document.find {kind:"Type"}` lista os textos.
2. Para cada um: `select.set {ids:[id]}` e `text.fonts {selectionOnly:true}` somando `missingGlyphs`; `text.getRange {id}` devolve o texto. Se a soma for maior que 0, o texto entra no relatório.
3. Para achar o caractere culpado: criar um texto sonda de 1 caractere na mesma fonte/estilo (fora da página), ler `missingGlyphs`, apagar com `edit.clear {ids}`.
4. Troca: `text.setText` tirando o caractere (deixar 2 espaços), medir a largura do prefixo (texto temporário, `document.inspect` dá `bounds {x,y,width,height}`) e `shape.star {cx,cy,radius1:22,radius2:9,points:5}` pintada de dourado na lacuna.
5. Rodar a auditoria de novo: a estrela some do relatório.

## Prova
Antes: Didot ★ (1), Futura ✓ e → (2), Avenir Next ● (1), Helvetica Neue ✔ (1), cada um com o caractere identificado. Depois da troca: o ★ saiu do relatório e a estrela vetorial ficou no lugar certo (zoom a 100 ppi conferido). Os outros três continuam no relatório de propósito (só a estrela foi trocada).
`pdffonts` confirma o risco: entram fontes reserva sem aviso (`Inter-Regular` no R18, `SourceSans3-Regular` aqui). Essa lista é o jeito mais barato de auditar o PDF final: qualquer fonte que não seja da marca é um glifo ausente.

## Defeitos e armadilhas
- A fonte reserva muda (Inter num teste, SourceSans3 noutro), não é determinística entre documentos.
- Posicionar o shape no lugar do glifo é manual: o bounds do prefixo ignora o espaço final (compensei +14 pt a 52 pt). Quem usar deve conferir a olho.
- Regra de ouro derivada: não escrever símbolos (★ ✓ → ●) em texto; desenhar como shape.
