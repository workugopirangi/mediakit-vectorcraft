# Critérios de aceite · Copa AME 2027 (v3)

> **v3, 13/10/2026: teste da skill v9, só horizontal, 18 páginas.** Gravado ANTES de qualquer render e commitado pelo
> Ugo. Mudar um critério depois do primeiro render exige uma linha nova neste arquivo, com data e motivo, sem apagar a
> anterior. Medido é necessário, não suficiente: as metas medidas não substituem o painel e a escolha às cegas.

## 1. Siglas

| Sigla | Família (nome no schema) |
|---|---|
| OI | `ornamento-identidade` |
| PT | `pattern-textura` |
| SR | `sobreposicao-recorte` |
| 3D | `profundidade-3d` |
| TI | `tratamento-imagem` |
| TE | `tipografia-expressiva` |
| AC | `acabamento-borda` |
| HB | `composicao-hibrida` |

Fios condutores (hipóteses: a consulta ao repertório, na etapa 3b, confirma ou troca):
- **F1**: fita de advertência física em 3D.
- **F2**: linha de cal sobre grama que liga título e número.

Motivo de momento (hipótese, idem):
- **M3**: as 5 estrelas douradas em 3D.

Intensidade (0 a 3, a mesma do repertório): 0 nenhuma; 1 sutil; 2 presente (aparece em 2 s, lida depois do título);
3 marcante (a segunda coisa lida).

## 2. Matriz por página

| # | Página | Famílias exigidas | Fio ou motivo | Intensidade | Defeito da v2 a corrigir |
|---|---|---|---|---|---|
| 1 | capa | SR (goleiro na frente do título por `registro`), TE, 3D (F1), TI | F1 | 3 | |
| 2 | manifesto | TI, TE, AC | | 2 | |
| 3 | público | TE (numeral com atletas recortados na frente), HB | F2 | 2 | |
| 4 | quem já joga | HB (backdrop em perspectiva), PT, AC | F2 | 2 | sai o painel creme chapado |
| 5 | território | HB (mapa sobre terra vermelha), PT, 3D (bandeirinhas como pinos) | F2 | 2 | sai o mapa fraco |
| 6 | alcance | TE, AC | | 1 | |
| 7 | divisor | PT, TE, 3D (F1) | F1 | 3 | |
| 8 | ativo 1 (nome da copa) | HB, AC | | 1 | |
| 9 | ativo 2 (arbitragem) | SR, TI | | 2 | |
| 10 | ativo 3 (beira do campo) | 3D (bola), PT | | 2 | |
| 11 | ativo 4 (transmissão) | HB, AC | | 1 | |
| 12 | ativo 5 (Noite das Estrelas) | 3D (M3), TI | M3 | 3 | |
| 13 | inventário | PT (papel de súmula), AC, TE | | 1 | sai a lista crua |
| 14 | divisor de cotas | TE | F1 | 2 | |
| 15 | cota Master | 3D (troféu + M3), AC | M3 | 3 | |
| 16 | cota Oficial | SR, TI | | 2 | sai o apito sobre as pernas |
| 17 | cota Apoio | 3D, PT | | 2 | |
| 18 | contato | SR, TE | F1, M3 | 3 | |

## 3. Obrigações do conjunto
- Toda página com 2 ou mais famílias.
- Cada família em 3 ou mais páginas.
- F1 e F2, cada um, em 6 ou mais páginas.
- Intensidade 3 em 4 a 7 páginas, nunca 3 seguidas.
- QA com 0 falha.
- `validar_pdf.py` com 0 falha.
- 18 páginas com texto vivo.

## 4. Conferência da própria matriz (13/10/2026, por script)
A matriz acima foi contada contra as obrigações antes de qualquer composição. Resultado:

| Obrigação | Como a matriz está | Situação |
|---|---|---|
| intensidade 3 em 4 a 7 páginas, nunca 3 seguidas | p.1, 7, 12, 15 e 18 (5 páginas); nenhuma vizinha em 3 | cumpre |
| cada família em 3 ou mais páginas | PT 6 (4, 5, 7, 10, 13, 17); SR 4 (1, 9, 16, 18); 3D 7 (1, 5, 7, 10, 12, 15, 17); TI 5 (1, 2, 9, 12, 16); TE 8 (1, 2, 3, 6, 7, 13, 14, 18); AC 7 (2, 4, 6, 8, 11, 13, 15); HB 5 (3, 4, 5, 8, 11); **OI 0** | OI só existe se F1 e M3 forem declarados como recurso de OI |
| toda página com 2 ou mais famílias | a p.14 tem só TE escrita; o segundo é a F1 | só cumpre se F1 contar como família |
| F1 e F2 em 6 ou mais páginas | F1 em 4 (1, 7, 14, 18); F2 em 3 (3, 4, 5) | faltam pelo menos 2 páginas de F1 e 3 de F2 |

**Como F1 e M3 são declarados decide a cobertura.** Contagem dos três jeitos possíveis (F2 contado como PT, porque a
imagem dele é a textura de cal sobre grama):

| Jeito | OI | 3D | Resultado |
|---|---|---|---|
| A: F1 e M3 como recursos de OI | 6 páginas (1, 7, 12, 14, 15, 18) | 4 páginas (5, 10, 15, 17) | cumpre, com folga nas duas |
| B: F1 como 3D, M3 como OI | 3 páginas (12, 15, 18) | 8 páginas | cumpre no limite: tirar M3 de uma página derruba OI |
| C: F1 e M3 como 3D | 0 páginas | 9 páginas | reprova a cobertura de 8 de 8 |

Recomendação para a 3b: **A**. A tabela de rota da própria skill põe "fita" e "estrelas" em `ornamento-identidade`; a
imagem continua sendo um objeto 3D do Codex (material, sombra de contato), só a família do recurso é OI. O que fica de
fora: na capa e no divisor, o "3D (F1)" da matriz passa a contar como OI, e o 3D dessas duas páginas deixa de contar.

**Fios:** a composição (etapa 4) escolhe onde entram as páginas que faltam: pelo menos 2 de F1 e 3 de F2. O fio só conta
com o mesmo hash de parâmetros em todas as páginas.

**Teto de intensidade:** o formato `sabado-de-campo` trouxe `direcao_criativa.intensidade` com teto 2. A matriz pede 3 em
5 páginas: a 3b sobe o teto para 3 no kit (o kit vence o formato).

**Elementos novos (regra do QA, 60% ou mais e 1 pattern novo):** o `qa_conjunto.py` só conta como novo o elemento com
papel herói, ornamento, apoio ou pattern; papel `acabamento` não entra na conta. Hoje: 0 de 6 novos (os 6 vieram da v2).
Se os 6 ficarem e as 8 imagens novas entrarem com papel que conta, são 8 de 14 (57%), abaixo da regra: é preciso 1
imagem nova a mais (9 de 15) ou 1 elemento da v2 a menos (8 de 13). E pelo menos uma textura nova (cal, terra ou súmula)
entra com papel `pattern`.

## 5. Metas de prova (Parte F)

| Meta | Régua | Como se mede | Resultado |
|---|---|---|---|
| famílias por página | 2 ou mais em toda página que não é respiro (intensidade 0 ou 1 fica isenta; decisão de 13/10, porque 2 recursos já dão intensidade 2) | `pipeline/medir_kit.py` (lê só artefatos) | |
| cobertura | 8 famílias menos as de `nao_usa`, cada uma em 3 ou mais páginas (decisão de 13/10) | `medir_kit.py` | |
| elementos ancorados | 100% | `medir_kit.py` | |
| continuidade | F1 e F2 em 6 ou mais páginas, com o mesmo hash de parâmetros | `medir_kit.py` | |
| variedade | estruturas distintas em número igual ou maior que na v2; nenhum par de vizinhas igual | `medir_kit.py --antes <v2>` | |
| ritmo | intensidade 3 em 4 a 7 páginas, nunca 3 seguidas | `medir_kit.py` e `acabamento.py` | |
| legibilidade | contraste mínimo por página dentro do limite; mediana de 95% ou mais da v2; nenhuma linha sobre textura sem véu | `medir_kit.py --antes <v2>` | |
| PDF | 0 fonte Type 3; títulos e tese como texto em 18 de 18; tamanho só reportado | `validar_pdf.py`, `prova_pdf.py` | |
| QA | 0 falha | `qa.py` | |
| painel adversarial | 15 de 18 ou mais passam nas 3 lentes depois da refutação; 0 "parece IA" sobrevivente | `revisao-painel.md` e `.json` | |
| páginas fracas da v2 | p.4, p.5, p.13 e p.16 passam no painel | `revisao-painel.json` | |
| escolha cega pelo modelo | v3 vence 14 de 18 pares ou mais; nenhuma das 4 fracas perde | `saida/escolha-cega.png` e a chave com sha256 registrada antes do juiz | |
| escolha do Ugo | 6 pares (capa, divisor, Noite das Estrelas, cota Master, p.4, p.13): se ele escolher a v2 em 2 ou mais, a direção volta à 3b | 2 perguntas depois da entrega | |

As 3 lentes do painel: "parece template de IA?", "o efeito valoriza ou enfeita?", "no nível de acabamento, se parece
com a referência?".

## 6. Tabela de inferência: os elementos da v2 por família
A v2 é mk-2.0 e não declara família. A coluna "família de hoje" é inferida pela tabela de rota da skill v9 (SKILL.md,
etapa 5). Fontes: `copa-ame-v2/mediakit.json` (`elementos`, `composicao`, `sistema_elementos`), `assets.json`,
`saida/plano-elementos-r1.json` e os templates do render (o que é do template está marcado).

| Elemento (id) | Página(s) | Família de hoje | O que a v3 muda |
|---|---|---|---|
| `constante-listras` (faixa de advertência plana, 248 × 16 px, canto de cima) | 2 a 14 e 18 | OI, intensidade 1 | a F1 (fita física em 3D) é a evolução dela; a composição decide onde a listra plana continua |
| grão (`sistema_elementos.constantes`, tipo `grao`) | 1 a 18 | TI, intensidade 1 | continua; TI ganha papel exigido nas p.1, 2, 9, 12 e 16 |
| `faixa-diag` (template da capa c: faixa diagonal com microtexto) | 1 | OI | F1 física em 3D na capa |
| `goleiro` (recorte real, `acervo/real-goleiro-recorte.png`) | 1 e 18 | SR: na capa sai de trás da faixa; no contato, cortado pela base | p.1: na frente do título, âncora `registro`; p.18: SR com TE, F1 e M3 |
| `mascote` (recorte real com árbitros) | 4 | SR | a p.4 passa a HB (backdrop em perspectiva), PT, AC e F2; a composição decide se o mascote fica |
| `cantos-backdrop` (grafismo `colchetes`) | 4 | AC | AC continua; sai o painel creme chapado |
| backdrop real (`acervo/tratado/backdrop-1400.jpg`, mural de logos) | 4 | nenhuma (foto de prova chapada no painel) | HB: o backdrop em perspectiva (homografia) |
| `mapa-sedes` (grafismo `mapa`, 4 sedes e anéis) | 5 | HB, fraco | HB sobre terra vermelha (PT), bandeirinhas como pinos (3D) e F2; sai o mapa fraco |
| numeral herói do público (template público b) | 3 | TE em intensidade baixa (número grande, sem efeito) | TE: numeral com atletas recortados na frente; HB; F2 |
| módulos de número (template prova) | 6 | nenhuma | TE e AC, intensidade 1 |
| `jogo-pattern` (Codex, a 10%) | 7 | PT | PT continua no divisor, com TE e 3D (F1), intensidade 3 |
| `meio-campo` (grafismo `campo`) | 7 | HB plano (linhas do campo) | a composição decide se fica; a matriz pede PT, TE e 3D (F1) |
| tabela real da rodada (`acervo/pdf/app-tabela-rodada.jpg`, miniatura) | 8 | nenhuma (prova real) | HB e AC, intensidade 1 |
| "SEU LOGO AQUI" composto (`compor.py`, `compor-*.json`) | 8, 10, 11, 12, 16 e 17 | HB (lettering composto em perspectiva na cena) | continua; nas cenas de 08/10, com os quads originais de 2752 px |
| `apito-cartoes` (Codex) | 9 e 16 | SR na p.9 (cruza a borda da foto); na p.16, objeto ao lado do nome | p.9: SR e TI; p.16: SR e TI, sai o apito sobre as pernas |
| `bola-jogo` (Codex) | 10 e 17 | 3D sem sombra declarada (peça em estúdio) | 3D com material e sombra de contato; PT nas duas páginas |
| `placar-tv` (grafismo `placar`) | 11 | HB | HB e AC, intensidade 1 |
| `borda-diag` (template do ativo diagonal: corte de 12° com fio) | 11 | AC | continua como AC, se a composição mantiver a variante |
| `trofeu-dourado` (Codex) | 12 e 15 | 3D sem sombra declarada (peça em estúdio) | p.12: 3D com M3 e TI; p.15: troféu e M3 em 3D, com AC |
| `estrelas-titulo` (grafismo `estrelas`, 5, cor de apoio) | 12 | OI, plano e pequeno | vira M3: as 5 estrelas douradas em 3D, nas p.12, 15 e 18 |
| `divisorias` (grafismo `fio`) | 13 | AC (fio que organiza) | PT (papel de súmula), AC e TE; sai a lista crua |
| véus sobre a foto (template: leve, escuro, painel-fade, sangria-base) | páginas com foto | TI, intensidade 1 | continua; nenhuma linha de texto sobre textura sem véu (meta de legibilidade) |
| fio de progresso no rodapé (`render.injetar_fio`) | 2 a 18 | AC (régua de borda) | a composição decide; não é a F2 |

## 7. Imagens novas previstas (Codex, 8)
1. fita de advertência torcida longa;
2. fita de advertência em curva;
3. estrela dourada metálica;
4. bandeirinha de escanteio;
5. textura de cal sobre grama vista de cima;
6. terra vermelha batida;
7. placa de campo lisa em perspectiva;
8. papel de súmula.

Orçamento, material e páginas previstas em `assets.json`, seção `v3` (8 imagens; a seção da v2 continua). Imagem fora
do orçamento não se gera; regerar conta no orçamento. Cada uma passa por `padrao.py texto`, `padrao.py checar` (as
texturas) e `familia.py pertence`.
