# R37. Malha de gradiente (mesh)

Status: NAO FUNCIONA para qualidade de estúdio (defeito confirmado em 3 leitores)

## Comandos executados (todos rodam sem erro)
```
shape.ellipse + paint.setFill {color}
object.mesh.create {ids:[id], rows:4, cols:4, appearance:"flat"}  -> {ids:[meshId]}
object.mesh.setPointColor {id:meshId, index:i, color:"#E9603A"}   (índices 0..(rows+1)*(cols+1)-1)
object.mesh.expand {}   (com a malha selecionada) -> grupo de peças de cor chapada
```
Testei elipse 4x4, elipse 2x2, elipse 4x4 expandida e retângulo 3x8 (1200x120 pt).

## Veredito visual
- A malha NÃO sai como shading suave no PDF: sai como centenas de pequenos retângulos/quadriláteros de cor chapada (degraus visíveis, aspecto de pixel grande), arquivo da página de teste 85 KB, 0 imagens (é vetor, mas em blocos).
- pdftoppm (poppler): emendas e cruzes finas claras entre as peças, mais evidentes na malha 4x4.
- sips e qlmanage (CoreGraphics do macOS): linhas escuras de grade bem visíveis sobre toda a forma, inclusive na 2x2 (a de 2x2 também mostra grade e degraus). Pior que no poppler.
- Conclusão: o defeito é do PDF gerado pelo VectorCraft (peças adjacentes sem sobreposição, antialiasing do leitor deixa fresta), não de um leitor específico: apareceu nos 3 leitores, com aparência diferente em cada um.
- `object.mesh.expand` dá o mesmo resultado (peças planas); não resolve.

## Regra de uso decidida
NÃO usar mesh em kit. Plano B: R36 (freeform, liso) para fundos orgânicos, ou gradientes linear/radial (R34/R35) combinados; para ornamento esférico, radial com focal deslocado (R35).

## Gotchas
- O índice de pontos é por linha: com cols=4 há 5 pontos por linha. Mapear cor por `i%n` gera listras verticais (foi o que fiz na elipse 4x4), use (linha, coluna).
- `appearance:"flat"` mantém a cor base; "center"/"edge" clareiam, não testei.
- Não testei `object.mesh.movePoint`; sem sentido refinar um recurso cujo export tem emenda.
