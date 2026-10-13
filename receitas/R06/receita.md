# R06. Foto com sobreposição de cor em bloco

Status: FUNCIONA

## Sequência (R06/teste.py), por cartão
1. Foto: `file.place {link:false}` + `object.setBounds {reference:0}` cobrindo o cartão (altura = altura do cartão, largura proporcional, centralizada).
2. Máscara do cartão: `shape.rectangle`, `select.set {ids:[ret]}` + `object.arrange.bringToFront {}`, depois `select.set {ids:[foto, ret]}` + `object.clippingMask.make {}`.
3. Camada de cor: `shape.rectangle` do cartão com `paint.setFill` (SEA, CORAL ou preto) e `transparency.set {ids:[cor], opacity:72}` (cartões 1 e 2) ou `{blend:"Multiply", opacity:60}` (cartão 3).
4. Texto branco por cima (`text.create`), Helvetica Neue Condensed Black 64 pt e Medium 15 pt.

## Aparência
Camadas coloridas uniformes, foto ainda legível por baixo, sem artefato. Qualidade de estúdio.

## Contraste medido (render a 144 dpi, branco sobre o fundo sob o texto de corpo)
- Azul SEA a 72%: 9,1 a 12,4:1 (ok).
- Preto Multiply 60%: 7,4 a 9,3:1 (ok).
- Coral #E9603A a 75%: 3,8 a 4,4:1. NÃO atinge 4,5:1; serve para o título grande (60 pt) mas o corpo de 15 pt precisa de overlay mais escuro (opacidade 90 ou coral mais escuro) ou texto preto.

## Defeitos e cuidados
- Nada rasteriza; opacidade e Multiply saem como transparência viva no PDF. Só verifiquei no poppler.
- Se a foto não cobrir a altura do cartão sobra faixa de fundo (erro de layout que cometi na primeira rodada); calcule a largura pela altura.
