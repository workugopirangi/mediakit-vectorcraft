# R09. Foto desfocada de fundo (profundidade)

Status: FUNCIONA

## Sequência (R09/teste.py)
1. `document.rasterEffectsSettings {resolution:150}` (300 se for gráfica; ver tamanho abaixo).
2. Fundo de segurança (cor chapada) e foto com SANGRIA: `file.place {link:false}` + `object.setBounds {x:-80,y:-45,width:1600,height:900,reference:0}` (maior que a página 1440x810).
3. `select.set {ids:[foto]}` + `effect.apply {effect:"blur.gaussian", params:{radius:14}}`.
4. Retângulo da página (1440x810), `object.arrange.bringToFront {}`, `select.set {ids:[foto, ret]}` + `object.clippingMask.make {}`.
5. Retângulo preto com `transparency.set {opacity:45}` para escurecer; texto nítido por cima.

## Aparência
Desfoque suave e uniforme, sem halo escuro nas bordas da página (a sangria e a máscara resolvem). Texto nítido, leitura boa. Qualidade de estúdio.

## O controle (foto sem sangria) mostra o defeito previsto
Controle: foto do tamanho exato desfocada. As bordas ficam translúcidas e esmaecem (halo), a imagem rasterizada é maior que o objeto (930x565 px para 400x225 pt, margem de efeito) e a borda perde nitidez. Por isso a regra: foto maior que a área visível + máscara.

## O que rasteriza e a quanto
Foto desfocada vira imagem RGB com soft mask: 3430x1971 px a 150 ppi (aprox. 1600x900 pt). A imagem pesa 7,8 MB e o PDF final 8,6 MB (medido). A 300 ppi seria cerca de 4x isso (não medido); como é desfoque, 150 ppi ou menos basta, não há detalhe a perder. Mesmo assim, é pesado para um fundo: considere resolution 100.
