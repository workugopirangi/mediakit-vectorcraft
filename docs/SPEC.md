# SPEC: skill gerar-mediakit-motion v10 (rota VectorCraft)

Status: rascunho para revisão do Ugo. Escrito em 13/10/2026.
Base: o desenho aprovado em 5 partes na conversa de 13/10, os 2 testes visuais (Copa AME estilo Nike, Sprint estilo Spotify × Garmin), o livro de 65 receitas e o teste ponta a ponta Sprint × World Tennis (aprovado pelo Ugo em 13/10).

## 1. O que a skill faz

Recebe um evento (e, se for o caso, uma marca e as cotas a oferecer) e entrega um mídia kit em PDF horizontal 16:9, mais o arquivo editável `.vectorcraft`. O visual de cada kit é dirigido por UMA referência do repertório, traduzida para as cores, fotos e fatos do cliente. A qualidade é julgada pelo resultado (comparação com a referência, revisor independente), nunca por lista fixa de técnicas.

Fora do escopo: a rota HTML (sai), PPTX, versão vertical, rodar fora do Mac.

## 2. Fluxo em 6 passos, com 2 aprovações do Ugo

1. **Entender.** Lê o briefing, as fotos e o kit antigo do cliente. Separa fato informado de meta. Nenhum número entra sem fonte.
2. **Dirigir.** Pergunta se o kit é genérico ou para uma marca; se for marca, quais cotas. Propõe 3 referências do repertório (ou usa a do Ugo). Escreve a ficha: uma linha por página com papel, copy e imagem. **Aprovação 1: referência + ficha.**
3. **Produzir.** Gera as imagens que a ficha pede (seção 4) e trata as fotos reais.
4. **Montar.** Um script por kit monta as páginas no VectorCraft sem tela (cerca de 0,5 s por página) e exporta PDF + `.vectorcraft`.
5. **Checar.** As 4 camadas da seção 5, corrigindo sozinho até 3 voltas. **Aprovação 2: kit final**, com o que depende do Ugo marcado.
6. **Aprender.** Grava o que o kit ensinou: referência nova no repertório, receita nova, peça de patrocínio reaproveitável, falha nova.

A ficha é atualizada quando o kit diverge dela com o OK do Ugo (exemplo: Sprint × World Tennis, página 3 ficou com a medalha).

## 3. As quatro bibliotecas

| Biblioteca | O que guarda | Como cresce |
|---|---|---|
| Repertório | referências visuais (capturas de decks e sites) com o que cada uma ensina | toda referência que o Ugo mandar entra sozinha |
| Livro de receitas | técnicas do VectorCraft provadas (hoje 65: 49 funcionam, 15 parciais, 1 não) | receita nova só entra com `teste.py` + PDF de prova |
| Peças de patrocínio | cena-base "SEU LOGO AQUI" e versão com marca, por peça (camisa, celular com post, cartaz, kit, copo, backdrop, notebook, outdoor, credencial, pórtico, boné, wind banner, tenda...) | cada kit com marca deixa as cenas aprovadas como base reaproveitável |
| Formatos | o que trava num kit aprovado (estrutura, ritmo) e o que troca por cliente | Sprint × World Tennis vira o primeiro formato "naming para marca" |

Ordem das peças segue o ranking medido nos 87 decks do repertório (camisa 38, celular com post 21, cartaz 21...).

## 4. Imagens: a IA desenha, o VectorCraft monta

- **Cenas com a marca** (pórtico, estande, camisa e as demais peças): geradas pelo GPT Image via Codex, já com o logo da marca anexado. Regra nova saída do teste World Tennis: **gerar primeiro; compor (colar o logo sobre cena limpa) só quando a geração errar o logo.** Nas 3 cenas do teste a gerada ganhou: logo fiel e integrado à luz da cena.
- Cada cena gerada passa por conferência de logo (fiel ao arquivo oficial) e de **logo fantasma** (letra ou marca inventada em placa, camisa, banner). O que a conferência achar e for aceitável vai para o Ugo com o selo "projeção ilustrativa".
- Cada geração gasta cota do ChatGPT: a skill registra quantas usou por kit e não regera sozinha.
- O gerador entrega no máximo 1672 px de largura (84 ppi numa página cheia). Aceito para cena de página inteira; não serve para recorte ampliado.
- **Fotos reais do cliente:** nunca esticar além do que a resolução aguenta (régua: 96 ppi na página). Foto pequena vai em painel, não em página cheia. Antes de usar, procurar e recortar marca concorrente (ex.: "NIKE" num short) e resíduo de captura (selo do Instagram).
- **Elementos decorativos** (vetor, texto, pattern, faixas, raias): feitos no VectorCraft pelas receitas, sempre novos por kit.

## 5. Checagem em 4 camadas

1. **Conteúdo:** cada número e fato do PDF bate com a ficha; nada fora dela; sem travessão; pendências da ficha listadas.
2. **Arquivo:** `validar_pdf` (fontes, páginas, imagens abaixo de 96 ppi com explicação de cada uma).
3. **Olho de máquina:** sobreposição medida pela **tinta da letra**, não pela caixa da fonte (a caixa acusa falso positivo em toda manchete de entrelinha apertada, medido em 13/10); contraste; "SEU LOGO AQUI" coberto; palavra sozinha na linha.
4. **Revisor independente:** outro modelo abre as páginas, a ficha e a referência e aponta, página por página, o que está errado e onde o kit ficou genérico. Eu confiro cada achado grave antes de agir (no teste, os graves eram reais).

Até 3 voltas de correção. O que for decisão do Ugo (cota, uso de imagem de terceiro, cenário inventado pela IA) sai da volta e chega marcado na aprovação 2.

## 6. Onde mora

- **Código:** `~/Developer/vectorcraft-mediakit/`, que vira um repositório GitHub **privado** com a skill, o código, as receitas e as fotos (decisão do Ugo; o risco de LGPD das fotos de crianças da AME foi registrado uma vez). Organização no padrão: `src/`, `docs/`, testes ao lado do código.
- **VectorCraft:** travado numa versão testada (commit fixo), montado a partir do repositório. Atualizar só depois de rodar as 65 receitas de novo.
- **Conhecimento:** no cofre, em `SISTEMAS/GERAR MEDIAKIT/` (repertório, formatos, aprendizados). Os kits de cada cliente continuam em `CLIENTES/<CLIENTE>/MEDIAKIT/`.
- **Skill:** `SKILL.md` curto, um arquivo por passo, carregado só quando o passo chega.
- Fontes: qualquer fonte instalada no Mac (risco de licença registrado uma vez).

## 7. Junção com a v9 (feita em 14/10/2026)

A sessão v9 terminou em 14/10 e o estudo v2 dela foi gravado no cofre. O Ugo decidiu enxugar: entra só o que os três kits bons mostraram que faltava; o resto fica na v9 e só entra se um kit real pedir.

| Da v9 | Na v10 | Por quê |
|---|---|---|
| Repertório (87 referências, padrões, recursos, análises v1 e v2, recortes) | Biblioteca de referências, lida no cofre, sem cópia | Uma biblioteca só; referência nova entra direto no cofre |
| `recortar.py` (tirar fundo) | Entrou (`src/mediakit/ferramentas/`) | O VectorCraft não tira fundo |
| `cena_limpar.sh` (tirar letra inventada) | Entrou, com uma tentativa e cota registrada | Ataca o logo fantasma |
| `contact_sheet.py` (folha cega, antes e depois) | Entrou, reescrita sobre PDF | Teste cego e comparação de versões |
| `codex_gerar.sh` | Entrou na Tarefa 10 | Base de toda geração |
| `validar_pdf.py` | Usado no lugar, pelo `config` | Checagem do arquivo |
| Efeitos de foto, patterns, colar logo, objetos, paleta, fontes, fotos de banco, formatos, busca do repertório, régua | Ficam na v9 | Equivalentes na v10 (tratamento de foto, receitas do VectorCraft, gerador de cena) ou raros |
| Rota HTML (render, camadas, encaixes, composição, prova de CSS, PPTX) | Sai | A v10 monta no VectorCraft |

Biblioteca de objetos da Motion (`MARKETING/BIBLIOTECA DE OBJETOS`): o Ugo quer que seja a mesma do carrossel; a ligação fica para quando a v10 gerar o primeiro objeto.

## 8. Como a v10 prova que é melhor (antes de substituir a v9)

1. Mesmo briefing, dois kits: um pela v9, um pela v10.
2. Comparação cega: o Ugo vê os dois sem saber qual é qual e escolhe.
3. A v10 só substitui a v9 se ganhar. Até lá as duas convivem; nada da v9 é apagado.

## 9. Pendências conhecidas

- Validar a v10 num kit genérico (sem marca), já que o teste foi com marca.
- Checagem de sobreposição pela tinta: não existe ainda, precisa ser construída.
- Falha de segurança na trava `barrar-perigoso.mjs` fica com a sessão dona (registrado em `~/.claude/DEPOIS.md`).
