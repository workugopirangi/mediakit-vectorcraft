# Base técnica escolhida (v5, bancada de 08/10/2026)

Critério: qualidade demonstrada no arquivo final (não na prévia), controle de composição, consistência entre páginas, personalização por projeto, manutenção, e o que sobrevive à exportação. Tudo open source ou já instalado; nada depende de serviço pago para renderizar.

## O que entra, e por quê

| Tecnologia | Necessidade que resolve | Como reproduz a referência | Integração | Limites na exportação | Controle | Veredito |
|---|---|---|---|---|---|---|
| **HTML + CSS (Grid de 12 col, camadas absolutas, clip-path, gradientes em oklab, blend nativo)** | Composição editorial com precisão de pixel; três direções do mesmo conteúdo | Painel 41,7%/50%, numeral fantasma, título em duas cores, caixas de contorno, véus: tudo é CSS e tokens | Jinja2 macros por arquétipo; `tema/` em camadas | O Skia preserva texto, vetor, gradiente e os 12 blend modes nativos; `filter`, `drop-shadow`, `mask-image` com alfa suave rasterizam a região (então saem do CSS) | total | base |
| **Jinja2 (macros = arquétipos; `kit.html` monta pela sequência-mestre)** | Reuso com variação; `paginas[]` para sair da sequência | Cada macro é uma página-régua clonada | lê `mediakit.json` | nenhum | total | base |
| **Design tokens em CSS custom properties, em 4 camadas** (`10-tokens` core, `20-direcoes` expressão por direção, `30-componentes`, `40-projeto` + `tema-projeto.css` do cliente) | Fundamentos fixos, expressão por projeto sem tocar a biblioteca | Escala 230/96/64/36/24/16, espaço 8 pt, raios, divisas | render.py concatena | nenhum | alto | base (Style Dictionary/Tokens Studio dispensáveis: não há multiplataforma) |
| **Chromium headless (Playwright) → PDF** | Layout real, fontes reais, PDF vetorial | `preferCSSPageSize`, `printBackground`, `emulateMedia screen`, 1920×1080 | render.py | ver linha 1; `validar_pdf.py` confere | total | motor |
| **Fontes TrueType locais em `@font-face` com `font-weight: 100 900` e `font-synthesis: none`** | Tipografia da referência; sem Type 3 | RocGrotesk Wide ExtraBold é a letra do Corre por Elas | `--fontes <pasta>` embute em data URI | peso sintético ou CFF reconstruído viram Type 3 (comprovado); TrueType vira CIDFontType2 | total | base |
| **`fontes_do_pdf.py` (pikepdf + fontTools: desubroutinize, cu2qu, merge por GID)** | O cliente quase nunca tem o arquivo da fonte; o kit antigo dele tem | Recupera a tipografia exata da identidade do cliente | roda uma vez por cliente | subset: só os glifos que o PDF usou (fallback por caractere para o resto); licença continua da fundição | alto | novo |
| **Pillow + numpy + OpenCV (`tratar.py`, `compor.py`, `cutout` por fundo liso)** | Efeitos raster fora do CSS: grão, duotone, igualar luz, 2880 px q85, sombra de contato, lettering em perspectiva, recorte de objeto em fundo liso | Cenas de origens diferentes com a mesma luz; "SEU LOGO AQUI" composto | antes do HTML | nenhum | total | base |
| **rembg (BiRefNet/ISNet), local** | Recorte de pessoa e objeto em fundo complexo | Atleta cruzando o painel (p.17) | `recortar.py --classe` | GrabCut do OpenCV não resolve cabelo (comprovado na bancada) | alto | necessário na máquina do Ugo |
| **SVG inline (ícones próprios, fio de assinatura, gráficos)** | Vetor nítido, um peso de traço | Ícones do trilho da cota | macros | texto SVG continua texto | total | base; D3/Observable Plot só quando houver gráfico complexo (altimetria, mapa) |
| **poppler (`pdfinfo`, `pdffonts`, `pdftotext`, `pdfimages`)** | Validar o arquivo entregue | nenhum | `validar_pdf.py` | nenhum | nenhum | base |
| **python-pptx (híbrido: fundo PNG + texto nativo)** | Slides editáveis quando pedido | nenhum | `exportar_pptx.py` | fontes não embutidas; cenas não editáveis | médio | opcional |

## O que foi avaliado e descartado

- **Tailwind, shadcn, MUI, Bootstrap:** escala e componentes de produto digital; produzem a "cara de app". Fora.
- **Slidev, Marp, reveal.js:** mesmo motor (Chromium) com um tema próprio por cima do nosso; não acrescentam ao layout e tiram controle. Fora.
- **Prince, WeasyPrint, Vivliostyle, Paged.js, Typst:** sem JS (auto-fit, medição) ou feitos para documento longo; não ganham nada num kit de 15 a 20 páginas. Fora.
- **Filtros SVG/CSS para duotone, grão e sombra:** rasterizam o PDF e perdem o texto (Skia expande `SkImageFilter`). Substituídos por Python.
- **Lettering e texto gerados pelo modelo de imagem:** dimensão mais fraca de todo gerador; substituídos por composição (`compor.py`), como a própria agência fez (os "SEU LOGO AQUI" do Corre por Elas são texto vetorial sobre a foto, não parte da imagem).
- **GrabCut (OpenCV) para pessoas:** serve só para produto em fundo liso.

## Bancada (como medir a distância da referência)

`fontes_do_pdf.py` + `pdfimages` + `pdftocairo -svg` recuperam fontes, fotos e lettering do kit de referência; o `mediakit.json` reescreve o conteúdo; o render produz as mesmas páginas; o `contact_sheet.py --regua` põe lado a lado. Diferença que sobra é do sistema, não do asset. Resultado de 08/10: capa, projeção, público, ativo em uso, cota principal e contato reconstruídos; a QA apontou e corrigiu quatro divergências (título em 4 linhas, número quebrado no card, preço em duas linhas, degradê raso da cota).
