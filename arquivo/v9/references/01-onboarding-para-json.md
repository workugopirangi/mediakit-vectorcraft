# Do onboarding ao `mediakit.json` (mk-2.0)

O chat do Motion Events devolve `onboarding.json` (schema do prompt de onboarding). Este arquivo diz como cada parte vira o `mediakit.json`. Schema completo: `schema/mediakit.schema.json`. Regras de rótulo: `memoria-mediakit/gramatica.md` §4 regra 8 e 12.

## Mapa de campos

| De `onboarding.json` | Para `mediakit.json` | Regra |
|---|---|---|
| `cliente` | `cliente` | Nome fantasia; sem ele, razão social e pendência |
| `evento` | `evento` + `evento.modalidade_sistema` | `modalidade_sistema` é um de: corrida de rua, trail, ciclismo, triathlon, arena (gramática §7). `primeira_edicao: true` quando não há edição anterior |
| `numeros[]` | `provas[]` | `id` p1, p2…; `rotulo` curto em minúsculas; `edicao`, `tipo`, `fonte` conforme a tabela abaixo; `icone` (seta, pessoas, mais, alvo, olho, pessoa, cursor, coracao); `destaque: true` nos 3 que vão para os cards de público |
| `historico[]` | `historico[]` | `pode_citar` vem de `marcas.antigas_nao_citar` |
| `publico` | `publico.descricao`, `publico.genero[]`, `publico.titulo` | gênero como `[{rotulo, pct}]`; título padrão "Perfil de|público" |
| `esta_edicao.meta_inscritos` | prova `tipo: meta`, `edicao: "esta edição"` | teto vai para `condicoes.observacoes` |
| `inventario.*` marcados "tem" | `inventario[]` | um item por ativo: `ativo`, `onde`, `capacidade`, `grupo`. Os que ganham página recebem `titulo` ("Sua marca na|largada"), `texto` (4 a 6 linhas, até 380 caracteres), `aplicacoes[]`, `cena_id`, opcional `layout: "topo"` + `mini_id`. Os demais vão para o inventário em colunas automaticamente |
| `cotas.itens[]` | `cotas[]` | `principal: true` na mais cara; `frase` (uma linha, o que a marca ganha); `icones[]` (camisa, megafone, balao, tenis); `cena_id`; `exclusividade` só com categoria e prazo; `aprovada_por`, `aprovada_em` |
| `acervo` | `acervo[]` | `funcao` por página: lettering, simbolo, capa, manifesto, projecao, publico, historico, ativo, cota, cotas, contato. Cena gerada: `gerada: true` + `rotulo` quando a página fala de futuro |
| `acervo.cores`, `fontes` | `marca` | `cor_primaria` hex; `direcao` por gramática §7 (tom); `fonte_display` só se instalada |
| `acao` | `acao.pessoas[]`, `acao.email`, `acao.proximo_passo` | pessoas com nome e telefone, como no Corre por Elas |
| texto livre do onboarding | `manifesto`, `tese`, `cotas_intro`, `divisor_inventario`, `prova.nota/rodape` | escritos pelo Claude no gate de copy |

## Fonte de cada prova

| Origem | `fonte` | `tipo` |
|---|---|---|
| Resultados, planilha, print de plataforma | `documento:<arquivo>` | realizado |
| Pesquisa do Motion Hub | `pesquisa:<url>` | realizado |
| Fala do organizador sem documento | `organizador` | informado, meta, projecao |
| Dado de outro evento da equipe ou do organizador | `documento:<arquivo>` + `prova.nota` visível | proxy |

## Como escrever

- `tese.frase`: até 12 palavras, o que acontece e onde a marca entra. "A cidade muda de ritmo. Sua marca está no centro dela."
- `manifesto.titulo`: duas linhas com `|`, caixa alta, sem a cor ("Corremos por|muito mais"); `subtitulo` em caixa alta regular; `frase` com `<b>` no nome do evento.
- `inventario[].titulo`: "Sua marca na|largada", "Sua marca em pontos de|ativação", "Sua marca na|camisa oficial". A parte depois do `|` fica na cor.
- `inventario[].texto`: por que aquele ponto vale (volume, imprensa, foto compartilhada, circulação depois do evento). Sem adjetivo vazio.
- `cotas[].entregaveis`: posição em cada um: "Presença no pórtico de largada/chegada (lateral superior)".
- `cotas_intro`: uma frase de 3 a 4 linhas com `<b>` no que importa.
- Sem travessão. Ponto, vírgula ou dois-pontos.
