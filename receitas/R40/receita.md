# R40. Blend entre formas

Status: FUNCIONA

## Comandos que funcionaram
```
object.blend.make {ids:[a,b], steps:20, orientation:"page"} -> {id}
object.blend.replaceSpine {}   # com select.set {ids:[blendId, pathId]}; o path é consumido
object.blend.expand {}         # select.set {ids:[blendId]} -> grupo de chaves e passos
```
Casos testados: (A) dois círculos concêntricos coral dentro de azul-mar, 20 passos; (B) duas curvas com traço 3 pt (ouro e menta), 24 passos, viram "linhas de velocidade"; (C) dois círculos pequenos ao longo de spine curva (path.create com bezier), 14 passos; (D) quadrado para círculo, 6 passos, expandido.

## Veredito
Qualidade de estúdio. Cor interpolada suave, passos regulares, spine respeitada (os pontos seguem a curva), interpolação de forma (quadrado para círculo) sem dobras. Vetor puro, nenhuma imagem, PDF 23 KB.

## Defeitos e armadilhas
- ORDEM DE EMPILHAMENTO: criei primeiro o círculo pequeno e depois o grande; o blend com o grande por cima escondeu todos os passos (só aparecia o círculo grande). Crie o objeto de fundo (maior) primeiro, o menor depois, e passe `ids:[maior, menor]`.
- 20 passos em círculo concêntrico com cores diferentes mostram degraus discretos visíveis (anéis). Para aspecto de gradiente use 60+ passos; não testei `smooth:true`.
- Em `object.blend.replaceSpine` o retorno é vazio mas funcionou; o path da spine é consumido (some), então não precisa deletar nem pintar.
- Passos do blend A com preenchimento chapado não deram fenda nem linha escura visível; na versão com contorno de 1 pt default as formas expandidas mostram fio escuro fino na borda (zoom 200 ppi), porque criei as formas com stroke none, o fio é só antialias entre peças sobrepostas.
