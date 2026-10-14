# Formatos: o kit aprovado vira ponto de partida

Pedido do Ugo (12/10/2026): o melhor kit até hoje (Copa AME v2) tem de ser reproduzível, sem depender de memória de
sessão. Um formato guarda o que funcionou num kit aprovado e separa o que é do cliente. Código em `pipeline/formato.py`
(provas em `pipeline/test_formato.py`); formatos em `formatos/<id>/`.

## 1. O que trava e o que troca

| Trava (`travado`, o kit novo herda) | Troca (`trocar`, vira pendência do kit novo) |
|---|---|
| receita sem id: nome, fontes, fundo, máscara, páginas do pattern, variantes por tipo | cor da marca (`paleta.marca`, `cor_primaria`, `cor_secundaria`) |
| parte fixa da paleta: `escuro`, `papel`, `texto` | cor de apoio (`paleta.apoio`) |
| constantes (`sistema_elementos.constantes`) | motivos de origem `simbolo` e `territorio` |
| motivos de origem `esporte` | `marca.estilo_cena` (vai com o modelo: a luz, a lente e a atmosfera ficam) |
| família modelo: meio, luz, paleta por chave e estilo com `{assunto}` e `{material}` | logo (`marca.logo_id` e o arquivo no acervo) |
| gramática da composição por tipo e variante, com os ids trocados por papéis | os elementos que preenchem cada papel (`papeis`) |
| padrões do repertório usados, `marca.direcao`, `marca.assinatura`, fontes de `marca` | |
| `tema-projeto.css` (sha256) e `direcao_criativa` (intensidade padrão 1, teto 2) | `direcao_criativa.fio_condutor` (veste um motivo do cliente; o `aplicar` copia só quando o kit novo não tem fio, e a pendência pede para confirmar o motivo) |

**Papel** é o lugar de um elemento do cliente na gramática: `{heroi-capa}` (o goleiro na AME), `{objeto-ativo-2}`
(apito e cartões), `{pattern-divisor}`. O nome sai da classe do elemento (`objeto` quando tem família, `pattern`, ou o
papel dele) e da primeira página que o usa; o mesmo elemento em duas páginas é o mesmo papel, e por isso o padrão "um
motivo em vários papéis" sobrevive à troca de cliente. Conteúdo de cliente dentro de grafismo (pontos do mapa, linhas do
placar) vira lacuna `{pontos}`, `{linhas}`.

Fica como referência, sem travar: `exemplos` (composição de página específica, `ativo:N` e `cota:<nome>`), os prompts
(`cena.modelo.txt` e `objeto.modelo.txt` com as lacunas `{assunto}`, `{momento}`, `{lugar}`, `{material}`, `{cores}` e
as que o pipeline escreve; os reais em `prompts/exemplos/`, sem caminho da máquina), `tratamentos` (espelhamentos,
cenas compostas, rótulos), `nao_tem` (calculado contra o que a skill sabe fazer: tipos de página, grafismos, constantes,
variantes, padrões do repertório e o contrato de acabamento da v9 que o kit não usa) e `prova/`.

## 2. Os quatro comandos

```
python3 formato.py exportar <kit> <id> [--nova-versao]     # estado FINAL do kit → formatos/<id>/
python3 formato.py aplicar <id> <kit-novo> [--simular]      # preenche só o ausente e grava formato_base
python3 formato.py conferir <kit> [--formato <id>]          # diferença contra o travado + lacunas abertas (sai 1)
python3 formato.py provar <id> [--kit-origem <pasta>]       # clone do APFS, render e comparação com a assinatura
```

- **exportar** lê `mediakit.json`, `saida/plano-elementos-<receita>.json`, `acervo/**/*.meta.json`, a entrada do kit
  em `historico-kits.json`, `tema-projeto.css`, os `.prompt.txt` e os PNG do render. Nunca lê o `direcao-de-arte.md`:
  ele é o plano de antes da execução, e o formato é o que o kit virou. Monta tudo numa pasta temporária e só então
  move: export que falha não deixa formato pela metade. Recusa sobrescrever.
- **aplicar** escreve no kit só a chave que falta (o kit vence), copia o `tema-projeto.css` se o kit não tiver e as
  fontes da receita de `fontes-livres/` sem sobrescrever arquivo, guarda `mediakit.antes-do-formato.json` e anota em
  `pendencias.md` uma linha por item de `trocar`, por papel a preencher e pela prosa da composição copiada (que entra
  como `{mensagem}`, `{estrutura}`, `{porque}`). Reaplicar não duplica nada. Um kit herda de um formato só.
- **conferir** recalcula o travado do kit com a mesma conta do export e compara. Prosa não conta; rótulos do kit (nome
  da receita, id e âncora da família) não contam; o estilo da família vale quando preenche o modelo. Lacuna `{...}`
  ainda aberta aparece à parte. No kit de origem: 0 diferenças e 0 lacunas.
- **provar** compara cada página com `prova/assinatura.json`: sha256 igual é `igual`; senão a miniatura de 480 px vira
  blocos de 8 px e nenhum bloco pode mudar mais que 6 (0 a 255): é `dentro` ou `diferente`. Página sumida é `falta`.

## 3. Quando um kit vira formato (etapa 11)

Na entrega (etapa 11), o kit aprovado pelo Ugo e com QA 0 falha vira formato: `formato.py exportar <kit> <id>` e a
entrada do kit em `memoria-mediakit/historico-kits.json` ganha `"formato": "<id>"`. Kit que já herdou de um formato e
mudou o que trava gera versão nova (`--nova-versao`), nunca reescreve a anterior. Kit novo de cliente parecido começa
na etapa 0 com `formato.py aplicar` e segue o fluxo inteiro: o formato adianta decisões, não pula etapa.

## 4. Precedência

O kit vence o formato. O formato é COPIADO para o kit (`aplicar`) e o render lê só o `mediakit.json` do kit: nada é
fundido na hora do render, e mudar o formato depois não muda kit nenhum já feito. `formato_base {id, versao, sha256}`
diz de onde o kit partiu; o `conferir` usa esse registro.

## 5. Segurança

Id do formato só `^[a-z0-9][a-z0-9-]{1,40}$`; todo caminho de kit e de formato passa por `caminhos.dentro_do_kit`
(link que sai da pasta é recusado); o `aplicar` confere o sha256 de cada arquivo do formato antes de usar; nenhum
caminho absoluto da máquina entra no formato (o export reprova).
