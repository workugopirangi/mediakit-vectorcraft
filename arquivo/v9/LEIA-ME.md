---
tags: [MP, skill]
tipo: nota
status: ativo
updated: 2026-10-13
---

# Skill `gerar-mediakit-motion` (v9 em teste): onde ela mora

Esta pasta é a skill inteira (SKILL.md, memória, pipeline, régua, bancada). `~/.agents/skills/gerar-mediakit-motion` aponta para cá, então o Claude Code local roda exatamente o que está aqui.

**Conta do claude.ai:** a v8 subiu em 12/10/2026 pelo Chrome do Ugo, como pacote LEVE (`pipeline/empacotar_skill.py <saida> --leve`: 195 arquivos, 1,7 MB, sem os recortes do repertório e sem as imagens e fontes dos exemplos de regressão, que um kit de cliente não usa). Conferido na conta depois do envio: "v8 · updated just now", 195 arquivos, árvore com `references/09-composicao.md` e `repertorio/`; a versão anterior (SKILL.md de 230 linhas, a v7) ficou no histórico. Por que leve: a ferramenta de envio do Chrome só aceita arquivo abaixo de 10 MB, e o pacote completo (`gerar-mediakit-motion-v8.skill`, 17,8 MB, 365 arquivos) foi gerado em 09/10 às 19:46 mas NUNCA subiu (a pergunta sobre o envio ficou sem resposta; o texto antigo desta linha afirmava o envio sem prova, aprendizado 51). Para pôr a completa na conta, o Ugo envia o arquivo à mão em `claude.ai/customize/skills` (Add, Upload skill). Mesmo risco do carrossel: toda mudança aqui exige reenviar o pacote, senão existem duas versões.

**v9 (13/10/2026): só neste repositório.** O SKILL.md abre com a linha "Versão v9, 13/10/2026"; é por ela que se confere
na conta qual versão está lá. Até um envio conferido nessa linha, a conta tem a v8 leve.

| Pasta | O que é |
|---|---|
| `SKILL.md` | o processo: 12 etapas (0 a 11) mais a 3b, a direção criativa, todas com portão |
| `memoria-mediakit/` | gramática, guia de qualidade, referências das pesquisas, aprendizados (nunca renumerar) |
| `pipeline/` | scripts que o Claude roda; `regressao.sh` antes e depois de toda mudança |
| `regua/` | as páginas de todas as referências (`paginas/`), as folhas de miniaturas (`folhas/`), o que comparar por tipo (`indice.json`) |
| `bancada/corre-por-elas/` | reconstrução do Corre por Elas com fontes, fotos e lettering do PDF. Teste técnico, não entregável |
| `bancada/historico/` | folha de comparação datada de cada rodada da regressão |
| `repertorio/` | 31 padrões de composição com 137 recortes de 72 referências, e os recursos de acabamento do estudo v2 (`recursos/`, em crescimento): o que o Claude consulta antes de compor cada página e antes de escolher o acabamento (`repertorio/LEIA-ME.md`) |
| `repertorio/capturas/` | as páginas capturadas das galerias do estudo (`repertorio.py capturar`): fora do git (`.gitignore`) e fora do pacote da skill; os manifestos rastreados ficam em `repertorio/fontes/` |
| `formatos/` | kits aprovados que viraram ponto de partida reprodutível (`sabado-de-campo`, da Copa AME v2): `formato.py`, references/11-formatos.md |
| `exemplos/acabamento-prova/` | kit fictício mk-2.1, uma página por efeito: a definição de pronto da mecânica do acabamento e o kit da prova do fluxo (`test_direcao_criativa.py`) |

## Estado em 13/10/2026 (v9, em teste)

Escrito: a etapa 3b (Leitura em 4 linhas, consulta gravada com `repertorio.py consultar`, escolha de 5 a 9 recursos de
pelo menos 4 famílias, 2 fios condutores, motivos de momento, estudo A/B), o acabamento por página e a tabela de
continuidade na etapa 4, a rota por recurso e o orçamento de imagens na 5, as pilotos com acabamento, o mock com
recursos e intensidade, a folha de acabamento com as 7 perguntas da seção M e o revisor independente na 9, recursos e
formato no histórico na 11 (`SKILL.md`, `references/10-acabamento.md`, `guia-qualidade.md` seção M).

Provado, no kit fictício: `test_direcao_criativa.py` 5 de 5 (consulta gravada; `qa.py` reprova sem ela e só essa linha
sai depois do `consultar`; `usados`; `contact_sheet.py --estudo` e `--acabamento`), cada prova com mutante, e 4
implementações quebradas de propósito acusadas pela prova. Mecânica: `test_acabamento_prova.py` 10 de 10.

Em teste (ainda não rodou num kit real): o fluxo v9 inteiro, cujo teste é a Copa AME v3; a escolha com o repertório
v2, que hoje tem 1 recurso de acabamento (provisório) no índice, então a origem da maior parte dos recursos ainda é um
padrão de composição ou uma página de referência.

Pendente:
- `formato.py exportar` leva da `direcao_criativa` só a intensidade e os recursos: o `fio_condutor` não viaja no formato.
- O pacote leve sai sem `repertorio/recortes/`: na conta do claude.ai o estudo A/B recusa (sem recorte) e a folha de
  acabamento marca "sem recorte" até o pacote levar os recortes.
- O kit `exemplos/acabamento-prova` dá 24 falhas no `qa.py` por desenho (referências `ficticio:*`, família, novidade):
  ele prova a mecânica, não é kit de entrega.
- `elementos.sh` e `cena_limpar.sh` já leem a descrição de arquivo (`--descricao-de`) e o SKILL.md e a references/09
  ensinam assim; a references/07 ainda mostra a descrição entre aspas.

## Estado em 09/10/2026 (noite)

Provado: regressão verde (régua, todas as provas unitárias, bancada Corre por Elas e exemplo fictício nas 3 direções);
teste completo com a A.M.E (`CLIENTES/AME CRIANCA/MEDIAKIT/copa-ame-v2`): QA 0 falha, PDF de 14 MB, folha de composição
revisada página a página e comparação em 3 colunas com o kit de 08/10 e com o sistema de antes.

Feito hoje: composição por página antes do elemento (âncora, função, escala em degrau, maquete), repertório, QA da
composição, prompts com o bloco Composition, Codex que repete até 3 vezes, revisão de segurança aplicada (caminho
confinado à pasta do kit, marcação e valores de atributo fechados, scripts sem prompt na linha de comando).

Pendente: igualar cor só pelos tons neutros (aprendizado 46); `elementos.sh` e `cena_limpar.sh` ainda recebem a
descrição na linha de comando (chamar com aspas simples até virar arquivo).

## Estado em 08/10/2026 (fim do dia)

Provado: regressão verde no conjunto integrado (régua 0 falhas, bancada 0 falhas, exemplo fictício 0 falhas nas 3 direções); regressão fica vermelha quando falta a fonte de título (testado).

Feito hoje:
- Régua: 131 páginas de 8 PDFs + 20 imagens de links das pesquisas (`regua.py capturar`), índice por tipo de página com o princípio de cada uma.
- Defeitos da primeira folha corrigidos: título do `ativo_topo` em 3 linhas, gráfico de alcance com eixo e legenda, subtítulo do divisor, QA reprova letra que falta na fonte.
- `imagens_web.py`: fotos gratuitas do Unsplash com registro de licença e ID, recusa repetida, paga, pequena e sem autor.
- `fontes_livres.py` + `fontes-livres/`: 25 famílias OFL em pesos estáticos.
- Segurança: crédito e legenda de foto escapados no HTML.
- Skill v5.1 reimportada na conta do claude.ai (a anterior fica no histórico da skill).

Pendente:
1. RocGrotesk licenciada no Mac (Ugo). Até lá a bancada usa o subconjunto recuperado do PDF.
2. Recorte (passo 4): funciona e foi testado (copo da bancada na cota Ouro; atleta recortada com garrafa). Falta atleta em alta resolução sem marca visível dentro de uma página; com mais disco livre, testar o birefnet-portrait (melhor em cabelo).
3. Perfil de público: a linha de estado dos cards estoura e encosta no card vizinho; o QA não detecta texto sobreposto.
4. Subtítulo do divisor sai em WideExtraBold; a referência usa Wide Medium (falta `fonte_titulo` separada na bancada).
5. Tom família continua sem referência forte.
6. Pexels só com chave de API (o site bloqueia acesso direto).
