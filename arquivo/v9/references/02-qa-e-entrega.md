# QA e entrega

## O que o `qa.py` barra (código 1)

| Regra | Por quê |
|---|---|
| Prova sem edição, tipo ou fonte; tipo fora da lista | Número sem estado engana a marca |
| `realizado` com fonte organizador; `proxy` sem nota visível | Regras 8 e 12 da gramática |
| Número com 3+ dígitos em texto livre sem prova | Todo número tem origem |
| Mais de 3 provas em destaque | A página de público tem 3 cards |
| Inventário com cena mas sem título, texto ou aplicações; cena_id inexistente | A página de ativo tem 4 elementos obrigatórios |
| Nenhum ativo com cena | Regra 7: o kit mostra a marca em uso |
| Cota sem preço, quantidade ou entregáveis; exclusividade sem categoria ou prazo; entregável prometendo resultado | Cota incompleta não é oferta |
| Imagem gerada como `historico`; nenhuma imagem usável; arquivo não encontrado | Gerada nunca prova passado |
| Marca vetada em qualquer texto | Pedido do cliente |
| Travessão, meia-risca, palavra comum sem acento | Credibilidade |
| Texto fora da página ou estourando após ajuste; capa não é a primeira; contato não é a última; cota antes do divisor | Defeito visível ou ordem quebrada |

## O que a v9 acrescenta: camada de acabamento e arquivo entregue (12/10/2026)

As regras da camada só disparam em kit que declara a camada (direção criativa, papel `acabamento`, `efeito`,
`formato_base`) ou diz `mk-2.1`; kit mk-2.0 sem campo novo sai com as mesmas linhas de antes (conferido contra o golden
de 12/10/2026). A tabela completa, com o script de cada regra, está em references/10 (seção QA).

| Barra (código 1) | Por quê |
|---|---|
| mk-2.1 sem `consulta-repertorio.json`, ou com o arquivo ilegível | recurso escolhido sem a consulta gravada é escolha de cabeça |
| mk-2.1: recurso da página fora de `direcao_criativa.recursos`, ou com `referencia` fora do índice do repertório | recurso sem origem é recurso inventado |
| mk-2.1: página composta sem `acabamento` ou sem `porque`; menos de 4 famílias em `direcao_criativa.recursos` | toda página diz o que o acabamento faz nela |
| mk-2.1: fio condutor com tratamento diferente entre páginas (desenho, blend, máscara, material) | o fio muda de papel, escala e lugar, nunca de cara |
| intensidade calculada acima de 3; 3 páginas seguidas em 3 | página e ritmo saturados |
| falhas do `acabamento.validar` (mais de 2 acabamentos na página, função ou motivo fora, família de `nao_usa`, `cruza` fora da frente, sombra ou reflexo em quem não pode) | contrato do schema |
| 3º acabamento na página; `registro` com a caixa fora da conta do object-fit (1 px); `cruza` acima de 20% de uma linha do alvo, ou sem contraste 3:1; acabamento translúcido sob corpo, preço, número ou micro com o contraste amostrado no PNG abaixo de 4,5:1 (número 3:1) | geometria (`qa_geometria.py`) |
| página do PDF com mais imagens do que o HTML do render pede (`validar_pdf.py --imagens-esperadas`, em kit com a camada) | raster que ninguém pediu: filtro, blend fora da lista, sombra CSS, máscara com gradiente |
| PDF vertical: folha fora de 1080x1920, fonte de fallback ou Type 3, nome do evento, tese ou texto da página que não saiu como texto | o vertical saía em 6 folhas deitadas e o da direção causa embutia Helvetica; ele vai ao `validar_pdf.py` em todo kit que gera vertical |

- **Vertical só quando gerado.** Kit só horizontal (`paginas` sem página vertical e render com `--sem-vertical`; com
  render-report, o que ele diz vence a declaração): as composições `vertical:*` saem das regras do acabamento, o PDF
  vertical não é cobrado e um aviso lista o que ficou de fora.
- **Peso do PDF: só informação.** Sem teto, por ordem do Ugo (12/10/2026): o `validar_pdf.py` imprime o tamanho e não
  reprova; `--max-mb N` só liga um teto se alguém pedir.

## O que só avisa

Sem manifesto · sem cena de projeção · sem lettering · menos de 3 ativos com cena · entregável sem posição · título de ativo sem `|` · cor da marca em 7 ou 8 papéis · densidade entre 35 e 45% ou abaixo de 3% · blocos fora das colunas do grid · dois elementos disputando domínio · cena de ativo gerada sem `composta` · `estilo_cena` vazio · imagem gerada em capa/público sem rótulo · menos de 60% das páginas com cena.

Na camada de acabamento: consulta gravada sobre outro índice (ou sem o sha256) · recurso citado fora da direção criativa (kit sem mk-2.1) · intensidade acima do teto · 4 páginas seguidas sem nenhuma em 0 ou 1 · vizinhas com o mesmo conjunto de recursos · a mesma textura na mesma escala e área em páginas seguidas · página da tabela do fio sem o motivo, o mesmo papel em páginas seguidas ou medida fora do papel · recurso de um dos 3 últimos kits de outro cliente sem `porque_repete` · acabamento sem motivo · textura sob texto corrido · acabamento na cor da marca com opacidade ≥ .46 · `cruza` dentro do limite (aviso fixo) · `formato_base` diferente do travado do formato, ou com lacuna `{...}` aberta.

## Loop

```
mediakit.json → render.py --todas --png → qa.py → comparação lado a lado → corrigir JSON → repetir até 0 falhas e página por página no nível da origem
```

Correção é no JSON (texto, foco, qual cena) ou proposta de mudança no `tema.css`/arquétipo (visual de todas as páginas daquele tipo). Nunca no PDF. Defeito que se repete em dois clientes é defeito de arquétipo.

Em kit mk-2.1, depois do QA zero: folha de acabamento (`contact_sheet.py <pasta> --acabamento`, e `--pdf` sobre o raster do PDF entregue), `qa_conjunto.py <pasta> --continuidade` e as 7 perguntas da seção M do guia, com o revisor independente (references/10, Revisão).

## Comparação lado a lado

Para cada página, a origem na gramática §2 e as perguntas: tem um elemento dominante? tem microlabel? a cena mostra o ativo em uso? a cor da marca está em usos contados? parece peça ou slide? Resposta "slide" em qualquer página bloqueia a entrega, mesmo com QA zero.

## Artefatos

PDFs das três direções (ou das receitas) e os verticais quando o kit gera vertical · `png/` · `fontes.md` · `pendencias.md` · `briefing.md` · `cotas-proposta.md` quando houver · em kit mk-2.1, `direcao-criativa.md`, `consulta-repertorio.json` e `estudos/`.

## Aprovação

Cinco linhas ao Ugo. Aprovação registra data; devolução volta ao loop. Depois: cliente pelo chat do Motion Events. Fase 2: `entrega`/`entrega_versao`/`aprovacao` no Motion Hub.
