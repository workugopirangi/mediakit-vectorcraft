# R32. Image Trace: foto posterizada e logo vetorizado

Status: PARCIAL (logo: funciona bem; foto posterizada: funciona mas fica abaixo de nível de estúdio)

## Sequência que funcionou (R32/teste.py)
Logo (logo-ame-320-x3.png, 960x657, RGBA):
1. `file.place {path, link:false}` + `object.setBounds {reference:0}`.
2. `imageTrace.makeAndExpand {id, params:{mode:"color", palette:"limited", colors:2, ignoreWhite:true, noise:30, paths:90, corners:90, method:"abutting"}}` devolve `{id, paths:37, anchors:5652, colors:2}` em 0,19 s. (`makeAndExpand` junta `imageTrace.make` + `imageTrace.expand`.)
Foto (f4.jpg, 739x980):
1. mesma colocação; `imageTrace.makeAndExpand {id, params:{mode:"color", palette:"limited", colors:4, paths:60, corners:50, noise:8, method:"abutting"}}` devolve 1.868 caminhos e 40.823 âncoras em 0,67 s; com `colors:3, paths:80, corners:60, noise:15`: 744 caminhos, 33.083 âncoras, 0,74 s.

## Achados sobre o logo
- `mode:"logo"` sem parâmetros é aceito, mas dá 1.803 caminhos e 12.190 âncoras (5 cores): o logo da AME tem sombreado (não é chapado) e o modo "logo" tenta reproduzir cada tom. Inútil para vetor limpo.
- `mode:"logo"` com `logoColors:["#F5D80A","#0B0B0C"]` é RECUSADO: "this isn't a flat-colour logo (61% of its solid areas match a few flat colours)... use Color mode instead". Mensagem clara, o comando não gera lixo.
- `mode:"color", colors:2` com `noise:30, corners:90, paths:90` é o que deu o resultado limpo: 37 caminhos, curvas lisas (elipse, estrelas), letras A.M.E. legíveis a 300 ppi, textura "gasta" original do logo mantida nas bordas.
- Cor: a tinta resultante sai amarelo-limão aproximado (cor média da imagem), NÃO #F5D80A. Recolorir depois (`select.set` + `paint.setFill`) se a cor da marca importar.
- Critério "poucos nós": 5,6 mil âncoras para um logo é MUITO (a textura gasta custa nós). Para logo de parede de patrocinadores com pouco nó, o ideal é o logo vir em vetor do cliente.

## Achados sobre a foto posterizada
Resultado legível como pôster, mas: bordas em degrau (a foto tem só 739x980 px, o trace vira escadinha retangular em zoom 200 ppi), céu e pele ficam na mesma cor azul-acinzentada (paleta "limited" escolhe os tons dominantes, não os da marca), 744 a 1.868 caminhos e 33 a 41 mil âncoras. Não passa no critério "poucos nós, curvas suaves, sem manchas de ruído". `colors:3` é mais limpo que `colors:4`.
Como melhorar (não testado): subir `paths`/`corners`, escolher `palette:"documentLibrary"` com as cores da marca (library "document"), ou usar uma foto de maior resolução.

## Veredito visual
Logo: bom para uso interno e ampliação moderada (não tem o rigor de logo oficial). Foto: efeito gráfico aceitável em tamanho pequeno, mas abaixo de estúdio.

## Armadilhas
- PDF do teste: 2,3 MB, dominado pela foto 4 cores vetorizada.
- O tempo é baixo (< 3 s), então dá para iterar parâmetros.
- Fundo preto da página: o preto da logo some, é preciso conferir `ignoreWhite` e a tinta.
