# Assets e cenas: de onde vem cada imagem e como ela entra no layout

Herdado da skill de carrossel (níveis de origem, anti-repetição, contact sheet com ≤ 2 Reads, objeto gerado pelo Codex em fundo chapado + recorte local, nunca Recraft, nunca Freepik pirata; o plano B do Higgsfield saiu em 09/10/2026: se o Codex falhar, repete no Codex) e ampliado com o que a pesquisa trouxe: cena sem texto + composição por perspectiva, bloco de estilo fixo, resolução efetiva e tratamento consistente.

## 1. As cinco origens, em ordem de preferência por tipo de página

| Página | 1ª escolha | 2ª | 3ª | Nunca |
|---|---|---|---|---|
| Capa | foto real da edição anterior com pessoa nítida olhando para a câmera (cliente) | cena gerada (`capa`) com lettering composto | foto de biblioteca pública do local com véu, sem pessoas identificáveis | foto com texto em outro idioma; foto de outro cliente |
| Manifesto | foto real de emoção (abraço, chegada) | cena gerada (`manifesto`) | banco licenciado | rosto de pessoa famosa |
| Projeção do evento | cena gerada (`projecao`) com placeholders compostos | foto real da arena com placeholders compostos sobre painéis existentes | nenhum | foto real apresentada como projeção sem aviso |
| Público, contato | foto real do público | cena gerada | banco licenciado | nenhum |
| Ativo em uso (01 a 05) | cena gerada por ativo (`ativo --ativo "<nome>"`) com lettering e placeholders compostos | foto real do ativo com placeholders compostos | nenhum | cena com texto gerado pelo modelo |
| Cota | foto real íntima (close) para a principal; abertas para as seguintes | cena gerada (`cota`) | nenhum | a mesma foto em duas cotas |
| Prova (alcance) | prints reais de insights (como prova, não como arte) | nenhum | nenhum | gráfico inventado |
| Kit atleta | mockups reais (fotos de produto) ou gerados por `ativo --ativo kit` | nenhum | nenhum | render 3D limpo |

**Fotos, vídeos e identidade do cliente** entram sempre que existirem com direito de uso. Lettering e logo nunca são regenerados: entram como arquivo (`funcao: lettering/logo`, `gerada: false`); frame de vídeo serve como foto se tiver 1920 px.

**Sites e redes do projeto** (pesquisa do Motion Hub, `og:image`, posts): servem para entender identidade, pontos de logo e público, e como foto só com autorização explícita do cliente registrada no onboarding (`direito_uso`).

**Bibliotecas públicas gratuitas, a mesma rota do carrossel** (Unsplash e Pexels por ID, busca na web com termo específico e folha de miniaturas): para lugar (`funcao: local`), atmosfera e público genérico; autor, URL e data em `acervo[]`; ID registrado em `BIBLIOTECA DE IDS UNSPLASH.md` e `historico-kits.json`, nunca reutilizado entre kits; ≥ 1920 px; sem texto legível em outro idioma; sem rosto famoso; sem logo de marca não parceira. Sem banco pago.

**Geração por IA, só pelo Codex** (ordem do Ugo, 09/10/2026; o Higgsfield saiu da skill): `cena_prompt.py` (com `--composicao --pagina <rótulo>`, o prompt leva a área, a proporção, o lado que a página corta e a luz da página) → `cena.sh` (Codex, GPT Image; repete até 3 vezes em erro passageiro e para em cota ou login, sem trocar de fornecedor). A cena nasce SEM texto, com painéis lisos; o bloco de estilo (`marca.estilo_cena`) fixa luz, hora e lente para todas as cenas do kit.

Como os scripts do Codex se comportam (`codex_gerar.sh`, usado por `cena.sh`, `cena_limpar.sh` e `elementos.sh`): uma chamada por vez por kit (trava em `acervo/.codex.lock`); até `MEDIAKIT_CODEX_TENTATIVAS` (3) tentativas com espera crescente a partir de `MEDIAKIT_CODEX_ESPERA` (10 s) quando o Codex sai sem imagem ou entrega PNG truncado; quem encontra a trava ocupada espera até `MEDIAKIT_CODEX_ESPERA_TRAVA` (900 s). O Codex roda no sandbox `workspace-write` sem rede. Saídas: 0 ok, 1 o Codex não entregou, 2 Codex não instalado, 3 cota ou login (pare e espere), 4 trava ocupada, 5 Python sem PIL, 64 uso ou id inválido, 65 pedido mudou com o bruto já gerado, 66 prompt ausente. O prompt da cena nunca vai na linha de comando: o `cena.sh` lê `acervo/<id>.prompt.txt`. Ids de arquivo: a-z, 0-9 e hífen. Na cena de cada página, o `--cena` traz o que a direção de arte decidiu (lugar, gente, momento) e o `--composicao --pagina --elemento` diz onde o texto corrido, o escudo e o herói vão cobrir a foto.

**Descrição sempre por arquivo** (12/10/2026): a descrição do `elementos.sh` e a instrução extra do `cena_limpar.sh`
trazem campos do evento, e um `$(...)` ou uma crase dentro de aspas duplas rodaria no shell de quem chama antes de chegar
ao script. Por isso vão em arquivo, `--descricao-de <arquivo>`, ou pela entrada padrão com `--descricao-de -` e um heredoc
de aspas simples (`<<'EOT'`, nada dentro é expandido). A forma antiga, com a descrição entre aspas como argumento, ainda
roda, com aviso no stderr. Arquivo ausente ou vazio sai com 66 sem chamar o Codex; descrição dada duas vezes (argumento e
arquivo) sai com 64.

**Edição por IA e local**: remoção de fundo (`cutout.py` do carrossel por flood fill sobre fundo chapado, ou `recortar.py` com o rembg local), proporção certa pedida já no prompt (o bloco Composition diz a área real), upscale só quando a resolução efetiva ficar abaixo de 1, variações de uma cena aprovada (mesmo prompt, seed diferente), e **composição** (`compor.py`) para lettering, logo e "SEU LOGO AQUI" em perspectiva com luz herdada.

## 2. Como escolher a origem (decisão por página, registrada em `briefing.md`)

1. Existe foto real com direito de uso que mostra o que a página promete? Use. Trate (passo 4).
2. Não existe, mas a página é de ativo em uso ou projeção? Gere a cena sem texto e componha.
3. A página é de lugar ou atmosfera e não há foto? Banco licenciado, com `funcao: local` e legenda honesta.
4. Nada serve? A página não entra; registre em `pendencias.md`. Página sem imagem só se for divisor tipográfico.

## 3. Prompt de cena (ordem fixa)

`Photorealistic editorial sports photography.` → **Scene** (cena-herói da modalidade, painéis lisos) → **Subject** (pessoas do público, camisa lisa na cor) → **Camera** (35 mm f/2.8, nível do olho) → **Light** (bloco de estilo do kit) → **Location** (cidade real) → **Constraints** ("a real photograph someone could have taken, not a movie poster"; sem texto, sem logos, sem números; mãos corretas; horizonte nivelado).

Rodada de geração: projeção → capa → um ativo por cota → cotas → manifesto → contato. Contact sheet único com todas; ≤ 2 Reads individuais. Reprovada (mãos, multidão clonada, luz incoerente, painel sujo) volta com o defeito nomeado no prompt. Cena aprovada ganha `.prompt.txt` ao lado.

## 4. Tratamento (o que harmoniza origens diferentes)

- Toda imagem passa pelo mesmo tratamento do tema: véu (`tingido`, `escuro`, `base` ou `leve`), grão de 2% e corte por `foco`. Foto real e cena gerada ficam na mesma família de luz.
- Direção `causa`: véu multiply na cor da marca na capa; `performance`: véu escuro e contraste alto; `territorio`: véu na cor escura do bioma.
- Nunca: filtro de cor diferente por página, HDR, saturação acima do bloco de estilo, imagem esticada (`object-fit: cover` sempre).
- Resolução: fonte ≥ 1920 px de largura para full-bleed; ≥ 1000 px para painel; abaixo disso, `upscale_image` ou troca.

## 5. Composição de lettering e placeholders (`compor.py`)

Entrada: cena sem texto + quadrilátero do painel (4 cantos em px) + conteúdo (lettering PNG, logo, ou texto "SEU|LOGO|AQUI"). O script mapeia o retângulo para o quad (perspectiva), multiplica pela luminância local (sombras e dobras passam para o lettering) e mistura com opacidade. Vários painéis por cena via `--lote`. Registre `composta: true` no `acervo[]`; o QA avisa quando uma cena de ativo gerada não foi composta.

Tecido ondulado (camiseta): pendente (`MESH`); até lá, use quad em área plana do peito e opacidade .9.

## 6. Fidelidade

- Logo e produto reais: arquivo original, nunca regenerado, nunca distorcido (`object-fit: contain`).
- Registro real nunca apresentado como projeção, e projeção nunca como registro: `gerada` e `rotulo` no JSON; o QA barra `historico` gerado.
- Patrocinador antigo só com `pode_citar: true`; logo de patrocinador só com arquivo fornecido.

## 7. Objetos recortados (hero objects): planejar antes de buscar

Todo objeto nasce de um brief em `objetos[]` do JSON (o QA reprova campo faltando): `id`, `pagina` ("cota:Apresenta", "capa", "divisor"), `classe` (atleta | produto | equipamento), `funcao` (o que prova na narrativa), `arquivo`, `sombra`, `x`/`y`/`w` (âncora e largura em px da página 1920), `modo` (atras = cruza a divisa com oclusão; frente), `divisa_px`, `direcao` (aponta para o texto), `luz` (igual à da cena), `partes_cortadas` (o que sai pela borda; nunca cortar em punho, tornozelo ou joelho), `resolucao_min` (2× o uso), `temperatura_igualada` (true depois do `tratar.py igualar`).

O brief de cada imagem nova vai também em `assets.json` antes de gerar (orçamento de imagens, references/10). Objeto
gerado pelo Codex para um recurso da camada de acabamento ganha ali `recurso` (o id em `direcao_criativa.recursos`),
`material` (um dos 10 abaixo; vai ao `elementos.sh --material` e a `elementos[].material` no JSON) e o caminho do arquivo
da descrição. O `objetos[]` do JSON não tem campo de material: quem leva o material é `elementos[]`.

Origem, em ordem: `BIBLIOTECA DE OBJETOS/INDICE.md` → foto de produto do cliente ou do patrocinador → foto do próprio evento → geração pelo Codex em fundo cinza 50% (`asset.sh` do carrossel; objeto usado: gasto, riscado, com marca de grama) e recorte (`cutout.py`). PNG de bibliotecas públicas só se a licença for clara.

Recorte por classe (`recortar.py`): atleta → `birefnet-portrait` + `-dc` (não instalado: cai para `isnet-general-use` com aviso; o script nunca baixa modelo, e modelo ausente sai com código 2); pessoa-livre → `u2net_human_seg`, só pessoa de mãos vazias (ele come o que a pessoa segura, aprendizado 24); produto e equipamento → `isnet-general-use`; vidro e garrafa nascem em fundo neutro. `bria-rmbg` (padrão do rembg) exige licença paga para uso comercial: não usar. Depois: `tratar.py recortar-borda` (erosão 1 px + feather .8) e conferir halo compondo sobre preto e sobre branco.

Pessoa recortada da própria cena para passar na frente do título (relação `registro`): `recortar.py <cena-tratada> <saida.png> --classe pessoa-livre --da-cena --comparar isnet`. A saída tem o tamanho da cena e guarda os fragmentos; o IoU contra o isnet vai para a `<saida>.meta.json` e, abaixo de .90, o aviso diz que o objeto na mão pode ter sido comido (e onde).

**Objeto gerado com material** (só tipo objeto): `elementos[].material` no JSON e `elementos.sh <pasta> <id> objeto
--descricao-de <arquivo> --material <m>` na geração. O `elementos_prompt.montar_prompt` acrescenta UMA linha,
"Material/render: studio product render, physically based <material>, key light from the <LUZ> at 35 degrees, soft fill,
thin rim light, transparent background". Sem material, o prompt sai igual ao de antes, caractere por caractere; material
fora da lista, ou em outro tipo, é erro antes de chamar o Codex.

| `material` | Nome no prompt |
|---|---|
| `metal-escovado` | brushed metal |
| `ouro` | polished gold |
| `couro` | leather |
| `borracha` | rubber |
| `tecido` | woven fabric |
| `vidro-fosco` | frosted glass |
| `plastico-fosco` | matte plastic |
| `madeira` | wood |
| `papel` | paper |
| `grama` | grass |

A linha de luz é a mesma para os 10: o prompt não muda a luz por material, só o nome. A direção é a que o prompt já tem:
`--luz`; senão, com `--pagina`, a luz da foto da página; espelhada quando a página espelha o elemento; sem nenhuma, a
esquerda (a mesma padrão do `tratar.py sombra`, para a sombra cair do lado certo). Luz dura, especular ou de cima, quando a
Leitura do kit pede, vai na descrição; bronze, prata, cromo e gema não estão no vocabulário e entram pela descrição, com o
material mais perto (o recurso `material-do-objeto-diz-o-nivel-da-cota` faz assim). Se a luz e o material chegaram, a
folha diz: é a pergunta 2 da seção M do guia (integração).

**Sombra e reflexo como itens derivados** (kit com a camada de acabamento): `efeito.sombra: contato` e
`efeito.reflexo: piso`, na composição, num PNG de rota de imagem de `elementos[]`, fazem o render gerar `<id>-sombra` e
`<id>-reflexo` pelo `tratar.py` (cache por sha256, na escala do pai; a sombra com a luz da família, senão a da página; o
reflexo com altura .35, opacidade .32 e achatar .9). Saem com papel acabamento e `derivado_de`, pintam logo antes do pai,
na camada dele, e ficam fora da conta de herói, apoio e pattern, da sobreposição com o pai e do 3º acabamento da página.
Objeto girado não ganha derivado (erro da âncora). Fora da camada, o `objetos[]` continua com o PNG de sombra feito à mão.
À mão, os mesmos tratamentos: reflexo de piso, só sobre fundo liso, `tratar.py reflexo <objeto.png> <id>-reflexo.png`
(espelho achatado em .9, .35 da altura, rampa de .32 a 0 gravada no alfa; o topo encosta na base da tinta do objeto);
esmaecer em degraus gravado no alfa, `tratar.py alfa-degraus <png> <saida.png> --direcao dir --passos 5 --minimo .12`
(nunca `mask-image` com gradiente, que rasteriza o PDF).

**Textura única × pattern por código** (aprendizado 31: 2 de 2 patterns pedidos como seamless saíram com costura).
Textura é matéria sem ladrilho visível (papel, terra, cal sobre grama): uma imagem por área, `tratar.py textura <entrada>
<saida.jpg>` (1x, JPEG q80, sem alfa; recusa PNG com alfa real e saída que não seja .jpg), nunca repetida, cortada em
ladrilho nem espelhada. No render entra como acabamento sem alfa, com blend multiply no papel, screen no escuro e
soft-light sobre foto (references/10). Textura com alfa real vai pelo `tratar.py preparar <entrada> <saida.png>`. Pattern
é repetição regular e sai por código (`pattern-simbolo` com a silhueta de um objeto, `hachura`, `malha`, `ondas`,
`curvas-nivel`, `pontos-radiais`, `meio-tom-foto`; references/05); pattern do Codex só ladrilha depois de `padrao.py
checar` e `tornar-seamless` com índice até .5 (references/07).

Integração (portão da etapa 7, antes do render): temperatura igualada à cena (`tratar.py igualar`, 30 a 50%); direção da luz igual à declarada na cena (se não bater, espelhar quando não houver texto, ou trocar a cena); escala plausível (um tênis não é maior que um atleta no mesmo plano, salvo conceito declarado); sombra de contato e oclusão (`tratar.py sombra`, ou o derivado do `efeito.sombra: contato`); oclusão de camadas (a parte sobre o painel fica atrás do véu, a parte sobre a cena fica na frente); no máximo 1 objeto por página e 3 por kit; o objeto nunca cobre as letras-chave do título.
