# R13. Fonte variável (instâncias nomeadas)

Status: FUNCIONA (como limite documentado: só instâncias nomeadas; eixos livres não existem)

## Sequência (R13/teste.py)
1. Descobrir o que existe: `text.fontList {family:"Inter"}` devolve `styles` (aqui: Regular, Medium, SemiBold). Source Sans 3: Regular, Semibold, Bold, Italic. Helvetica Neue tem 14 estilos (Thin a Bold Italic, mais Condensed Bold e Condensed Black).
2. Aplicar: `text.create {..., font:"Inter", style:"SemiBold"}` ou `text.setStyle {ids, font, style}`.
3. CONFERIR sempre: `text.fonts {}` devolve `status` e `resolved` por estilo usado.

## Resultado
- Inter Regular, Medium e SemiBold: `status:exact`; no PDF aparecem como Inter-Regular, Inter-Medium e Inter-SemiBold (mesmo objeto de fonte embutido, prefixo FJYXYM, subset), pesos visivelmente distintos no PNG (progressão limpa).
- Pedir um estilo que não existe NÃO dá erro: `style:"Bold"` e `"ExtraBold"` em Inter ficam `status:substitute`, resolvidos em SemiBold. No PNG as duas linhas saem idênticas à SemiBold, sem aviso. Isto é a armadilha: peso "preciso" só vale se estiver na lista do `fontList`.
- Source Sans 3 Regular/Semibold/Bold e Helvetica Neue Light/Medium/Bold: exact e com pesos corretos.
- Eixos livres (peso 640, por exemplo): não existem. Registrado como limite, não testado.

## Aparência e cuidados
Qualidade de estúdio nos pesos que existem. Fontes embutidas, nada rasteriza (PDF de 56 KB). Para um peso intermediário entre Medium e Bold, a saída é Helvetica Neue (Medium e Bold) ou Avenir Next (Medium, Demi Bold, Bold, Heavy), famílias com mais instâncias.
