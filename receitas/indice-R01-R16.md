| R01 | Duotone de foto | FUNCIONA | toGrayscale na foto + retângulo amarelo em Multiply + máscara: duotone limpo, foto fica foto (blend vivo no PDF) |
| R02 | Foto em máscara de forma livre | FUNCIONA | círculo, losango, Bézier e donut com furo recortam limpo a 400%; só lembrar de trazer a forma para a frente antes da máscara |
| R03 | Foto dentro de letras gigantes | FUNCIONA | clippingMask aceita texto vivo direto; letras viram máscara vetorial limpa (escolher foto clara) |
| R04 | Tipografia gigante sangrando | FUNCIONA | texto 560 pt em um objeto, grupo + máscara do tamanho da página: corte limpo e PDF de 10 KB (multi-artboard não testado) |
| R05 | Foto com fade por opacity mask | FUNCIONA | gradiente preto-branco + makeOpacityMask {clip:true}: fade sem degrau (soft mask no PDF, JPEG intacto) |
| R06 | Foto com sobreposição de cor | FUNCIONA | opacidade e Multiply ok; contraste medido: azul 9-12:1, preto 7-9:1, coral só 3,8-4,4:1 (não vale para corpo) |
| R07 | Cutout com contorno de adesivo e sombra dura | FUNCIONA | trace do alfa (threshold 254) + unite + offsetPath round: contorno vetorial limpo, sombra vetor; threshold 128 erra |
| R08 | Grão/ruído sobre blocos de cor | PARCIAL | filmGrain mono a 300 ppi fica bom mas página cheia = 24 MB (medido); texture.grain tem ruído colorido; recomendo 150 ppi |
| R09 | Foto desfocada de fundo | FUNCIONA | blur.gaussian r=14 com foto maior que a página + máscara: sem halo; sem a sangria as bordas esmaecem (testado) |
| R10 | Borda irregular tipo papel rasgado | FUNCIONA | distort.roughen smooth + object.expand + máscara: borda ondulada orgânica em vetor (corner dá dente de serra feio); não é rasgo fibroso |
| R11 | Hierarquia com estilos nomeados | FUNCIONA | precisa paraStyle + charStyle (parágrafo não guarda fonte/corpo); setAttrs mudou os 2 títulos de uma vez |
| R12 | Recursos OpenType | PARCIAL | pnum, onum, ss01, salt, smcp (Avenir/Source Sans) funcionam; tnum sem efeito visível (numerais já tabulares); c2sc/zero rejeitados; Arboria exige família "Arboria-Bold" + estilo ☞ |
| R13 | Fonte variável (instâncias nomeadas) | FUNCIONA | Inter Regular/Medium/SemiBold exatas; Bold/ExtraBold pedidos viram SemiBold em silêncio (checar text.fonts); sem eixos livres |
| R14 | Colunas e quadros de texto | FUNCIONA | text.areaOptions columns/gutter fluem sem perda; overflow:true é confiável (testei e o texto some); sem balanceamento nem órfã; thread não testado |
| R15 | Tabela com tabulação e líder | PARCIAL | tab direita e decimal alinham (medido); leader aceito mas NÃO desenhado (6 variantes); plano B com linha pontilhada stroke dash [0,7] round funciona |
| R16 | Texto com contorno, vazado e gradiente | FUNCIONA | setRangeStyle fill none + stroke + join round: contorno limpo; paint.setFill gradient em texto cobre o bloco todo; texto segue vivo |
