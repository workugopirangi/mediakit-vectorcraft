# R59. Camadas, nomes de objeto e organização

Status: FUNCIONA

## Comandos que funcionaram
- Renomear a camada inicial: `layer.setProps {name:"Fundo"}` (sem id = camada atual).
- Nova camada acima da atual, que passa a ser a atual (o que for criado depois cai nela): `layer.new {name:"Fotos"}`; com opções: `layer.new {name:"Guias (nao imprime)", printable:false}`.
- Nome de objeto: `object.setProps {ids:[id], name:"titulo"}` (também em grupo de máscara de corte).
- Juntar objetos selecionados numa nova camada: `select.set {ids:[a,b]}`, `layer.collectInNew {}` (aceita só `ids`; NÃO aceita `name`, falha com erro; renomear depois com `layer.setProps {id:<retornado>, name}`). Quando os objetos já estão numa camada, a nova nasce como SUBCAMADA dela.
- PDF com camadas: `document.exportPdf {path, createLayers:true, preserveEditing:false}`.
- Conferir estrutura: `document.inspect {depth:3}` lista camadas e filhos com nomes.

## Prova
- Árvore (inspect): Selo [selo-ouro], Guias (nao imprime) [guia-margem], Texto [subtitulo, titulo], Fotos [foto-capa], Fundo [fundo-cor].
- PDF `teste.pdf` (PDF 1.7, 547 KB): `/OCProperties` com 5 grupos de conteúdo opcional nomeados Fundo, Fotos, Texto, Guias (nao imprime), Selo, na ordem do painel (`/Order`), todos ON na visualização; a camada "Guias" com `/Print /PrintState /OFF` (não imprime, mas aparece na tela). `teste-planas.pdf` (sem `createLayers`) não tem OCProperties.
- Diferença de tamanho com e sem camadas: 547.404 contra 544.908 B (desprezível).

## Gotchas
- A ordem de criação define o empilhamento: cada `layer.new` fica ACIMA. O inspect lista de cima para baixo.
- Camada "não imprime" continua visível no PDF em tela (poppler mostrou a linha coral da guia). Se o PDF vai para e-mail/prospect, a guia aparece. Para escondê-la use `layer.setProps {visible:false}` (camada oculta sai OFF; não testei) ou nem exporte a camada.
- Nomes com acento e espaço funcionaram nas camadas ("Guias (nao imprime)" por segurança sem til).
- Reabrir o PDF de volta como camadas (document.open) não foi testado.

## Veredito
Estúdio. Dá para entregar template organizado e PDF com camadas opcionais para o time editar.

## O que rasteriza
Nada.
