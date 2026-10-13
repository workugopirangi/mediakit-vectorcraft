# R38. Envelope warp em tipografia

Status: FUNCIONA

## Comandos que funcionaram
```
text.create {x,y,text,font:"Helvetica Neue",style:"Condensed Black",size:130,color:"#D4A64A"} -> id
object.envelope.makeWithWarp {ids:[id], style:"arc"|"flag"|"wave"|"bulge", bend:50, h:0, v:0} -> {id: envelopeId}
object.envelope.expand {}   (com o envelope selecionado: select.set {ids:[envelopeId]}) -> {ids}
```
Testei arc (bend 50), flag (40), wave (40), bulge (35); flag e bulge também expandidos.

## Veredito
Qualidade de estúdio. Curvas limpas em zoom de 200 ppi, sem dobras nem fendas, letras deformadas de forma suave. No PDF o texto deformado vira contorno (nenhuma fonte embutida para o título: pdffonts só lista a fonte dos rótulos pequenos), sem imagem (pdfimages vazio). Arquivo 36 KB. Mesmo texto em live envelope e expandido saem iguais.

## Gotchas
- O id retornado por makeWithWarp é o do envelope, não o do texto: use-o para expandir.
- Título deformado deixa de ser texto: a busca/seleção de texto no PDF some (acessibilidade e copiar). Manter a versão com texto para o SEO/leitor não existe no PDF; avisar quando o título carregar informação essencial.
- Arco e bulge deslocam o bounding box (arc subiu e cresceu para os lados): reposicionar com object.setBounds depois, o `y` do text.create não vale mais.
- Diacríticos (Ç do INCHAÇO) acompanham a deformação, a cedilha ficou solta abaixo por causa do bulge; conferir visualmente.
