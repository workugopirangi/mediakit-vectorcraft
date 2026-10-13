# R44. Largura variável (swoosh)

Status: FUNCIONA (presets perfeitos; perfil por pontos com cantos)

## Comandos que funcionaram
```
path.create {d:"M 80 300 C 400 100 700 500 1000 200"} + paint.setFill {none:true} + paint.setStroke {color}
stroke.set {weight:40, cap:"round", profile:"taperEnd"}      # também "lens", "taperStart", "pinch", "teardrop", "wave"
stroke.widthProfile.set {ids:[id], points:[[0,0.05,0.05],[0.3,1,1],[0.6,0.4,0.4],[1,0.02,0.02]]}   # [t, esquerda, direita] como fator do weight
stroke.widthPoint.set {id, t:0.5, left:30, right:4}          # pontos em pt, assimétrico; -> {index}
```

## Veredito
- Presets (taperEnd, lens, taperStart, wave) saem com curva lisa, sem degraus, ponta afiada limpa, em 200 ppi. Vetor puro: o PDF não tem imagem, o traço vira contorno preenchido. Qualidade de estúdio para rotas, grifos e swooshes.
- Perfil personalizado: o `widthProfile.set` com 4 pontos fez CANTOS visíveis nos pontos (largura máxima em t=0.3 virou ponta angular, e t=0.6 uma quebra). O `widthPoint.set` com 3 pontos (t 0, 0.5, 1) saiu liso e assimétrico. Para suavidade: usar preset ou colocar pontos mais próximos e variações menores; não usar muitos saltos de fator.

## Gotchas
- `widthProfile.set` retorna vazio mas aplica.
- Com cap round e perfil taperStart, a ponta fina do início perde o arredondamento (correto), e o fim largo mantém o cap redondo.
- Dois traços de cores diferentes que se cruzam (ouro e creme) não geram emenda.
- Perfil é "preservado no PDF" apenas como geometria final: depois de exportar não há mais traço editável (o `preserveEditing:false` já era o caso).
