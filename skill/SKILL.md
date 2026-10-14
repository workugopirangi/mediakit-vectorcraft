---
name: gerar-mediakit-motion
description: Gera mídia kit de patrocínio da Motion Perform em PDF 16:9 montado no VectorCraft (v10), dirigido por uma referência do repertório. Use quando o Ugo pedir mídia kit, deck de patrocínio ou proposta de cota para um evento ou para uma marca. Só roda no Mac do Ugo.
---

# Gerar mídia kit (rota VectorCraft)

Projeto: `~/Developer/vectorcraft-mediakit` (código, receitas, bibliotecas). Especificação: `docs/SPEC.md`.
Saída de cada kit: `CLIENTES/<CLIENTE>/MEDIAKIT/<kit>/` no cofre, com `ficha.md`, `acervo/`, `saida/kit-<nome>.pdf` e `.vectorcraft`.
Comandos rodam de dentro do projeto com `scripts/py` (o Python da v10, já com o pacote).

## A régua
- Um estilo por kit, dirigido por UMA referência. Qualidade se julga pelo resultado (referência, revisor), nunca por lista de técnicas.
- Nenhum número sem fonte. Fato informado e meta ficam separados.
- Sem travessão em nada. Toda pergunta ao Ugo vai por AskUserQuestion, com recomendação.
- Cada imagem gerada gasta cota: nunca regerar sozinho.
- **Toda referência que o Ugo mandar, em qualquer momento, entra na biblioteca na hora:** `python3 -m mediakit.referencias adicionar <id> "<de onde veio>" <arquivos>`.

## As quatro bibliotecas
- Referências: o repertório do cofre (`python3 -m mediakit.referencias listar`).
- Receitas: técnicas do VectorCraft provadas (`receitas/indice-*.md`).
- Peças de patrocínio: cenas aprovadas reaproveitáveis (`mediakit.pecas`).
- Formatos: kits aprovados que viram molde (`COFRE_MEDIAKIT/formatos/`).

## Os 6 passos (leia o arquivo do passo só quando chegar nele)
1. Entender: `passos/1 ENTENDER.md`
2. Dirigir, com a **aprovação 1** (referência + ficha): `passos/2 DIRIGIR.md`
3. Produzir as imagens: `passos/3 PRODUZIR.md`
4. Montar no VectorCraft sem tela: `passos/4 MONTAR.md`
5. Checar, até 3 voltas, e a **aprovação 2** (kit final): `passos/5 CHECAR.md`
6. Aprender: `passos/6 APRENDER.md`

## Antes de começar
- `cd ~/Developer/vectorcraft-mediakit && scripts/py -m pytest -m "not vectorcraft" -q` tem de passar.
- O VectorCraft precisa estar na versão travada (a montagem para sozinha se não estiver; o remédio é `scripts/montar_vectorcraft.sh`).
