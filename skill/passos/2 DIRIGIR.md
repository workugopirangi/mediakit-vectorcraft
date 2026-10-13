# 2. Dirigir (aprovação 1)
- Pergunte: kit genérico ou para uma marca? Se marca, quais cotas mostrar.
- Referência: a que o Ugo mandar, ou 3 propostas do repertório (`python3 -m mediakit.referencias listar`, com as análises em `COFRE_MEDIAKIT/repertorio/referencias/` e os padrões em `padroes/`), cada uma com uma frase do que ela traria para este cliente.
- **Toda referência que o Ugo mandar entra na hora:** `python3 -m mediakit.referencias adicionar <id> "<de onde veio>" <arquivos>`, e depois uma análise curta em `repertorio/referencias/<id>.md` no formato das que já existem (grid, hierarquia, elementos, o que não copiar).
- Escreva `ficha.md` (modelo: `CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-world-tennis/ficha.md`): fontes dos fatos e uma linha por página com papel, copy exata e imagem. Pendências no fim.
- Peça a aprovação 1 por AskUserQuestion: referência + ficha. Nada é gerado antes dela.
