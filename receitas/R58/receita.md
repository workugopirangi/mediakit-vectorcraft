# R58. PDF leve para e-mail

Status: FUNCIONA

## Teste
Página 1440x810 com 4 fotos 720x405 (JPEG tratado de 1936x1081 px, 194 ppi na página) mais texto. Mesma página exportada 5 vezes.

| Arquivo | Opções | Tamanho | Fotos no PDF |
|---|---|---|---|
| A-padrao.pdf | preset padrão (`preserveEditing` ligado) | 3.527.333 B | 1936x1081, 194 ppi, JPEG original |
| B-sem-embutir.pdf | `preserveEditing:false` | 1.768.739 B | idem |
| C-leve.pdf | + ppi 150, abovePpi 225, jpeg high, fastWebView | 1.769.113 B | idem (194 < 225, não reamostra) |
| C2-150ppi.pdf | ppi 150, abovePpi 160 | 1.151.542 B | 1500x844, 150 ppi, JPEG |
| D-minimo.pdf | ppi 110, abovePpi 165, jpeg medium | 446.541 B | 1100x619, 110 ppi, JPEG |

Fontes embutidas e vetoriais em todos (`pdffonts`). `pdfinfo` mostra `Optimized: yes` quando `fastWebView:true`.

## Comandos que funcionaram
```
document.exportPdf {path, preserveEditing:false, thumbnails:false, fastWebView:true,
  compression:{color:{downsample:"bicubic", ppi:150, abovePpi:160, compression:"jpeg", quality:"high"}}}
```

## Achados
1. `preserveEditing` ligado no preset padrão DOBRA o arquivo (3,53 MB contra 1,77 MB): o documento nativo vai embutido. Desligar é o maior ganho e é grátis. Confirmado.
2. `abovePpi` é limiar de verdade: com 194 ppi e limiar 225 nada é reamostrado e o JPEG original passa direto (sem recompressão, sem perda). Para reduzir foto de 194 ppi, baixar `abovePpi` (ex.: 160 para ppi 150).
3. Com 150 ppi o arquivo caiu a 1,15 MB por página de 4 fotos; com 110 ppi, 0,45 MB. O preview a 50 ppi não diferencia; a 150 ppi de render o 110 ppi já mostra suavidade perceptível; 150 é o piso que recomendo para tela cheia.
4. Tamanho por página varia com a quantidade de fotos; "kit abaixo de 10 MB" depende do nº de páginas e fotos por página. Não medi um kit inteiro (extrapolar 1,15 MB x 19 páginas seria especulação de pior caso; páginas só de texto custam bem menos).
5. `thumbnails:false` não mudou perceptivelmente (1 página).

## Veredito
Estúdio para e-mail: usar `preserveEditing:false`, `fastWebView:true`, `ppi:150, abovePpi:160, jpeg high`. Texto vetorial intacto.

## O que rasteriza
Nada (sem efeitos). Fotos são reamostradas só se acima de `abovePpi`.
