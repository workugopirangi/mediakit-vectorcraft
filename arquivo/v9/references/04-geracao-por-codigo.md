# Geração por código: alternativas, amostra e fluxo recomendado

## 1. O que foi comparado

| Rota | Controle de composição | Consistência entre páginas | Qualidade do PDF | Edição posterior | Manutenção | Veredito |
|---|---|---|---|---|---|---|
| **HTML/CSS → Chromium (Playwright) → PDF** (atual) | total: grid, tokens, véus em oklab, `color-mix`, `mix-blend-mode`, `object-position`, grão em SVG, `text-wrap: balance` | alta: um `tema.css`, arquétipos Jinja, sequência derivada do JSON | alta: `preferCSSPageSize`, `printBackground`, `print-color-adjust`, fontes embutidas, 1920×1080 exato | PDF não editável; HTML editável só por quem sabe | baixa: 1 CSS + 1 arquivo de macros + 2 scripts | **motor principal** |
| **SVG programático** (Python gerando SVG → cairosvg/Chromium) | total e preciso em vetor; bom para gráficos e diagramas (percurso, matriz) | alta se gerado de tokens | alta | SVG abre no Figma e no Illustrator como vetor editável | média: layout de texto (quebra, balance) é manual | **complemento**: gráficos da página de prova, mapa de percurso, diagramas de inventário, e exportação vetorial para o Figma |
| **python-pptx (nativo)** | limitado: sem `mix-blend-mode`, sem `color-mix`, sem grão, sem máscara de foto fina; gradientes e véus pobres | média: precisa reimplementar o tema em EMU | média: o PowerPoint renderiza diferente do Chromium (fontes, kerning) | total: tudo editável | alta: duas implementações do mesmo design | **só quando o cliente exige editar tudo**; não atinge a régua visual |
| **Híbrido: Chromium gera fundo sem texto + python-pptx põe caixas de texto nativas nas mesmas posições** (`exportar_pptx.py`) | o do HTML | a do HTML | fundo idêntico ao PDF; texto renderizado pelo PowerPoint | texto editável; visual protegido; placeholders dentro das cenas não editáveis | baixa: reaproveita o render-report | **rota de editável** |
| Slidev / Marp / reveal.js | layouts nomeados + CSS, export via Chromium | alta | igual ao HTML (mesmo motor) | Markdown editável, mas não pelo cliente | média: tema próprio da ferramenta por cima do nosso | não acrescenta ao que já temos; útil só se o Ugo quiser apresentar ao vivo com navegação |
| Canva / Figma Slides / Gamma / Pitch | editores; MCP do Canva inventou dados e importação de PPTX quebrou linhas e cortes (v7) | média | boa, mas inspeção manual a cada export | total | alta: composição à mão | **entrada de editável só sob demanda**, importando o PPTX híbrido |

## 2. A amostra

Mesmo `mediakit.json` do exemplo (15 páginas): (a) PDF pelo Chromium, (b) PPTX híbrido reaberto no LibreOffice e convertido a PDF para comparar. A página de cota ficou idêntica no fundo (cena, véu, caixas, trilho de ícones, assinatura) e com os textos editáveis nas mesmas posições; diferenças observadas: fonte de fallback mais larga quebra títulos de uma linha (corrigido com caixa 14% mais larga e sem quebra), e o pill "COTA" precisava manter o fundo (corrigido no modo `sem-texto`). Com as fontes instaladas na máquina de quem abre, o PPTX fica no nível do PDF.

## 3. PDF versus slides editáveis (diferença que vai para o cliente)

- **PDF** (`kit-<direcao>.pdf`): a entrega padrão. Fiel ao design, pesa pouco, abre em qualquer lugar, não muda. É o que a marca recebe.
- **PPTX híbrido** (`kit-<direcao>-editavel.pptx`): só quando o cliente pedir para trocar texto, preço ou contato sozinho. Ele edita o texto; não move cena, véu nem caixa. Precisa das fontes instaladas; sem elas o PowerPoint substitui e a tipografia muda. Placeholders dentro das cenas e lettering composto não são editáveis (são imagem).
- **PPTX nativo** (tudo em formas): não é oferecido. Perde o que faz o kit parecer de estúdio.
- **Canva editável**: só importando o PPTX híbrido e conferindo página a página (a v7 provou que a importação altera cortes e quebra linhas).

## 4. Fluxo recomendado

```
mediakit.json → render.py --todas --png --fundo → qa.py → contact_sheet.py (revisão) → PDF (entrega)
                                                   └→ exportar_pptx.py (quando pedido)
gráficos e diagramas: SVG gerado em Python dentro dos arquétipos (próximo passo: página de prova e mapa de percurso)
```

Ganho concreto da geração por código, medido na amostra: zero composição manual, três direções do mesmo arquivo, QA geométrica no DOM (colisão, overflow, safe area, densidade, contraste, grid, escala, fontes), e PPTX editável como subproduto do mesmo render. O que o código não resolve: a qualidade da cena e o julgamento de "peça ou slide", que ficam na revisão visual.

## 5. O que a segunda rodada mudou (e está na v4)

- **Efeitos raster saem do CSS.** Duotone, igualar luz, grão, sombra de contato e mockups são feitos pelo `tratar.py`/`compor.py` antes do HTML. Motivo: o SkPDF "expande" filtros (`filter`, `feTurbulence`, `drop-shadow`) em bitmap e o texto dentro deixa de ser texto. No HTML ficam tipo, forma, clip-path, gradientes e os blend modes nativos (multiply, soft-light, overlay...), que o PDF preserva. Comprovado no exemplo: grão em PNG com soft-light sobrevive (std 2,3 no PDF) e `pdfimages` não mostra raster de página.
- **Validação do arquivo entregue** (`validar_pdf.py`): `pdfinfo` (1440×810 pt), `pdffonts` (emb/sub/uni = yes; sem Type 3; sem família de fallback quando `marca.fonte_*` está declarada), `pdftotext` (títulos como texto), `pdfimages -list` (imagens de página inteira = cenas; ppi); o tamanho é só informado (sem teto de peso por ordem do Ugo (12/10/2026)). O `qa.py` chama este script.
- **Fontes variáveis viram Type 3** em pelo menos um caso documentado: usar instâncias estáticas (fontTools `instancer`).
- **Tamanho**: sem teto, por ordem do Ugo (12/10/2026). O `validar_pdf.py` informa o peso e não reprova; a resolução das cenas segue a régua de ppi (2x como meta, 1x como aviso). Se o peso trouxer risco prático (e-mail, WhatsApp no 4G), registrar uma vez em `pendencias.md`, sem regra. Cenas por `tratar.py preparar`, PNG só com alfa, sempre enviado como Documento.
- **PPTX híbrido**: fundo = PNG da página sem texto; texto nativo nas caixas medidas; fontes não vão embutidas (quem abre precisa tê-las). Importação no Figma/Canva: não verificada, conferir página a página.
- **Motores alternativos**: Prince/WeasyPrint não executam JS e só compensam para documento longo; Paged.js/Vivliostyle só com sumário e cabeçalhos correntes. O kit continua no Chromium.
- **Tailwind e kits de UI**: não entram. A escala de produto digital e os cards com sombra suave produzem exatamente a "cara de app".

## 6. O que a terceira rodada mudou (v9, 12/10/2026): lista branca provada e vertical

A regra da v4 ("no HTML ficam tipo, forma, clip, gradiente e blend nativo") ficou mais estreita: no HTML do kit só entra o
efeito que o `prova_pdf.py` provou no PDF do Chromium (`test_prova_pdf.py`). Cada efeito roda numa página mínima em três
versões (base sem o efeito, o efeito e um mutante com `filter: saturate(1.4)` no mesmo nó) e passa por cinco checagens:
`pdffonts` sem Type 3, `pdfimages` com os mesmos objetos de imagem da base (pelo conteúdo), `pdftotext`, raster do
`pdftoppm` contra o PNG do Chromium (diferença média até 3 por canal) e bytes acrescentados. Rodado de novo em 13/10/2026
com os mesmos números de 12/10: os 9 permitidos passam nas cinco e o mutante de cada um é acusado; os 7 proibidos são
acusados (saída 0). A tabela com os bytes de cada um e como o render escreve cada efeito está em references/10.

| Permitido | Proibido (o que acusou no caso medido) |
|---|---|
| opacidade e `mix-blend-mode` no próprio nó, nunca num contêiner; no kit, só `normal`, `multiply`, `screen`, `soft-light` (`efeito.blend`) | `perspective` (foto: a imagem vira outro raster; texto a 40 graus: raster 4,4) |
| `clip-path` polygon (diagonal, chanfro, arco-base) | `matrix3d` (raster 5,0) |
| `clip-path` circle (círculo) | `text-shadow` (imagem nova, raster 8,9, +15 KB) |
| `clip-path` inset (janela, corte do `cruza`, recorte do `registro`) | stroke em `<text>` (a fonte vira Type 3) |
| véu de luz: gradiente `in oklab` de 4 paradas em `screen` | `background-clip: text`, a foto dentro da letra (raster 5,2) |
| duas cópias do mesmo data URI com corte (o PDF guarda a imagem uma vez) | `mask-image` com gradiente (em texto: raster 5,0 e +10 KB) |
| eco por `<text>` preenchido, com opacidade em degrau | `filter`, qualquer um (imagem nova, texto perdido, raster 7,2, +23 KB) |
| contorno de letra como `<path>` (fontTools) | |
| `mask-image` com PNG de alfa (cor chapada sobre o alfa) | |

Variante de proibido que passou limpa (perspective leve em texto, recorte com rotateX, `mask-image` com gradiente sobre
foto) continua proibida: quem escreve o kit não escolhe a variante que o Chromium vai achar segura. Esmaecer é sempre em
degraus gravados no alfa (`tratar.py alfa-degraus`) ou no svg (`params.esmaecer`), e perspectiva de desenho é homografia
calculada em Python (`malha` e `campo` com `perspectiva`): reta continua reta, vetor continua vetor, sem transform 3D.

**O que rasteriza** (a região vira imagem e o texto dentro deixa de ser texto): `filter` e os filtros de SVG
(`feTurbulence`, `feColorMatrix`, `drop-shadow`, `blur`), `text-shadow`, `perspective` e `matrix3d` sobre foto ou texto,
`background-clip: text`, `mask-image` com gradiente sobre texto. O `validar_pdf.py --imagens-esperadas`, que o `qa.py`
passa em kit com a camada de acabamento, conta as imagens que o HTML do render pede em cada página (`<img>`, `<image>` de
svg, `url()` da seção) e reprova a página do PDF que tem mais: é o sinal da rasterização silenciosa. Calibrado nos 5 kits
do golden de 12/10/2026 (`schema/fixtures/imagens-golden-2026-10-12.json`).

**Três achados medidos** (vale para quem escreve grafismo ou prova nova):
- O PDF do Chromium imprime o conteúdo da página numa escala um pouco menor que a tela: 0,99847 (medido em 13/10/2026 pelas
  provas de PDF do `test_grafismos.py`, cerca de 3 px a menos em 1920). Toda comparação de raster PDF × tela reamostra o
  PDF nessa escala; sem isso, letra grande desloca 2 px na ponta e a comparação acusa deslocamento como desenho diferente.
- Traço fino com `stroke` e opacidade: no cruzamento de duas linhas, a tela do Chromium soma a opacidade (vira hairline) e
  o PDF não, e as duas saídas destoam. Por isso `hachura` e `malha` desenham cada traço como o retângulo dele, preenchido,
  e os traços do mesmo degrau de opacidade vão num `<path>` só: o cruzamento sai igual na tela e no PDF.
- `clip-path` no mesmo nó que tem `transform` gira e espelha junto. No render isso é usado de propósito (a máscara da
  diagonal e do chanfro acompanha o elemento espelhado e cai do lado que a página pede); no SVG, para recortar rente à
  caixa um desenho girado, o recorte fica num grupo de fora, sem o transform (a `fita` cortava o próprio texto antes).

**Vertical.** O PDF vertical saía partido em todo kit: o tema tem `@page { size: 1920px 1080px }` e o Chromium seguia esse
@page, então cada página de 1080x1920 virava duas folhas deitadas (6 de 1440x810 pt no lugar de 3 de 810x1440). O
`vertical.html` ganhou o próprio @page e o tamanho da folha passou a vir do @page de cada template. O vertical da direção
principal também embutia Helvetica, porque o `vertical.html` não repetia o bloco de tipografia da marca do `kit.html`.
Os dois consertos têm prova em `test_render_pdf.py`, que roda o pipeline vivo e o do commit anterior (tem de sair
partido). Desde então o `qa.py` manda o vertical ao `validar_pdf.py` (folha de 1080x1920, fontes, nome do evento, tese e
texto por página) em todo kit que gera vertical; kit só horizontal renderiza com `render.py --sem-vertical` e o QA não
cobra o vertical.

Fluxo do kit mk-2.1, depois do QA: `contact_sheet.py <pasta> --acabamento [--pdf]` e `qa_conjunto.py <pasta>
--continuidade` (references/10, Revisão).
