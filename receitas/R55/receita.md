# R55. Estilos gráficos e cor global (rebrand por patrocinador)

Status: FUNCIONA para vetor (formas, texto, gradientes); NÃO funciona para foto (pixels)

## Comandos que funcionaram
1. Criar swatches globais: `swatch.new {name:"Marca", color:"#F5D80A", global:true}` (idem "Tinta", "Apoio").
2. Aplicar por nome: `select.set {ids:[id]}` e `paint.setFill {swatch:"Marca"}`. Funciona em formas, elipses, retângulos arredondados e em TEXTO (o objeto de texto inteiro com `ids`).
3. Gradiente ligado aos swatches: `paint.setFill {gradient:{kind:"linear", angle:90, stops:[{offset:0, swatch:"Marca"}, {offset:1, swatch:"Tinta"}]}}`.
4. Rebrand: `swatch.edit {name:"Marca", color:"#D4A64A"}` e `swatch.edit {name:"Tinta", color:"#0F3550"}`. Retorno `{relinked: 8}` e `{relinked: 6}`.
5. Exportar o PDF antes e depois: teste-ame.pdf e teste-sprint.pdf (preview-1.png mostra os dois empilhados).

## Prova
Mesmo script, dois PDFs. Fundo, cartões, círculos, textos (inclusive o título com fonte viva) e gradiente trocaram do amarelo/preto da AME para dourado/azul-mar do Sprint com 2 comandos. Fontes continuam embutidas.

## Limitações
- Foto não muda: `recolor.apply {map:{"#F5D80A":"#E9603A"}, includeImages:true}` com a foto selecionada só recolheu o quadrado vetorial; as camisas amarelas da foto ficaram amarelas (`recolor.colors` listou 1 cor, a do quadrado). Para rebrand de foto é preciso tratar a imagem fora (PIL) antes de colocar.
- Texto criado com `color:` direto no `text.create` NÃO fica ligado ao swatch. Tem que passar por `paint.setFill {swatch}` depois (fiz isso em cada texto).
- Só testei `swatch.edit`; `graphicStyle.new/apply/redefine` e `recolor.apply` em vetor não foram exercitados.
- O swatch "Apoio" criado não foi usado na página.

## Veredito
Produtivo: é o ganho real de série. Cada elemento precisa nascer com o swatch (uma chamada extra por objeto). Recomendo embutir isso nas funções de `lib.py` (`rect(..., swatch="Marca")`).

## O que rasteriza
Nada neste teste (foto vem como JPEG nativo).
