# Direção de arte · Copa AME 2027 (v3)

> **v3, 13/10/2026: teste da skill v9, só horizontal, 18 páginas.** A direção de arte da v2 segue abaixo, sem mudança.

## Estado em 13/10/2026 (preparo)
A direção da v3 ainda não foi escrita: ela sai da etapa 3b da skill v9 (leitura em 4 linhas, consulta gravada ao
repertório, escolha de 5 a 9 recursos de pelo menos 4 famílias, fios condutores, motivos de momento, o que o kit não
terá e estudos A/B). Até lá, valem:
- a receita "Sábado de campo" e o que o kit v2 virou (o formato `sabado-de-campo` v1, gravado em `formato_base`);
- as hipóteses a confirmar na consulta, em `criterios-aceite.md`: F1 fita de advertência física em 3D; F2 linha de cal
  sobre grama que liga título e número; M3 as 5 estrelas douradas em 3D;
- a matriz por página do mesmo arquivo (famílias exigidas, intensidade e o defeito da v2 a corrigir).

O que muda em relação à v2 já decidido pelo Ugo (12/10): só horizontal; sem teto de peso do PDF (as cenas de 08/10 em
2752 px); 3D renderizado pelo Codex com material e luz declarados e montado por código (camadas, sombra, reflexo,
perspectiva por homografia), sem Blender.

---

# Histórico da v2
O `direcao-de-arte.md` da v2 como estava em 12/10/2026, sem mudança.

> Plano de antes da execução (09/10/2026), não reescrito. O que o kit virou está em `briefing.md`, seção "Estado final (12/10/2026)".

# Direção de arte · Copa AME 2027 (v2, processo de composição)

## Ideia central
**A marca entra em campo junto com a família.** O kit é desenhado como o próprio jogo: o campo é a estrutura, a tabela da rodada é a voz dos números, e a faixa preta e amarela da A.M.E é a assinatura.

Palavras proibidas: paixão, sonho (já está na bio), visibilidade sem lugar.

## Por que esta direção serve à A.M.E (e não a qualquer evento)
- A A.M.E já tem uma língua gráfica nos posts: fundo preto, faixa de advertência amarela e preta, caixa alta condensada, escudo oval com 5 estrelas. O kit de 08/10 ignorou essa língua e ficou com cara de template escuro. Esta direção parte do que o público da A.M.E já reconhece.
- O produto vendido é presença física no campo e na tela dos pais. As linhas do campo e a tabela da rodada mostram ONDE a marca entra; não são enfeite.
- O dourado aparece uma vez, na Noite das Estrelas, como na TV AME: é o momento de premiação, não a cor do kit.

## Receita única (r1 · "Sábado de campo")
- **Tipografia:** Barlow Condensed 800 nos títulos e números; Barlow no texto (par p12 da cartela: uma família em duas larguras, numerais tabulares para tabela e placar).
- **Paleta:** preto `#0B0B0C` (fundo), amarelo A.M.E `#F5D80A` (acento, 1 a 3 usos por página), branco (texto), papel `#F4F1E8` (uma página clara de respiro: o inventário), dourado `#C9A227` só na Noite das Estrelas.
- **Fundo:** escuro. **Máscara:** reta (a diagonal fica com a faixa de advertência, para não haver duas diagonais competindo).
- **Assinatura:** `fio`, o tempo de jogo: a linha de progresso no rodapé corre de 0' a 90' ao longo do kit.

## Língua dos elementos (unidade)
| Elemento | Rota | Função | Onde |
|---|---|---|---|
| Faixa de advertência amarela e preta | código (`listras`) | identidade | constante: canto superior esquerdo, mesma caixa em toda página escura |
| Microtexto de borda "COPA AME · TEMPORADA 2027 · SÃO JOSÉ DO RIO PRETO E REGIÃO · DESDE 2005" | código | acabamento | constante: base, de margem a margem |
| Linhas do campo (meio-campo, círculo central, área) | código (`campo`) | contexto, organização | dados, divisores, cotas: o círculo central enquadra o número, a área enquadra o preço |
| Tabela da rodada / placar | código (`placar`) | organização | alcance, ativo de naming, cotas |
| 5 estrelas do escudo | código (`estrelas`) | identidade | junto do logo e na Noite das Estrelas |
| Fios que ligam rótulo ao valor | código (`fio`, relação `liga`) | conexão | inventário e ativos |
| Telas reais (Instagram, app, tabela) em moldura de celular | código + print real (`celular`) | contexto, prova | plataformas, app |
| Bola de jogo, apito e cartões, troféu dourado | imagem (Codex), objetos com a luz de sábado de manhã (sol baixo pela esquerda) | foco, profundidade | ativos, Noite das Estrelas |
| Atleta e goleiro recortados (fotos reais da A.M.E) | imagem real | foco | capa e manifesto |

## Gramática por tipo de página (variação dentro da unidade)
- **Capa:** foto real recortada (goleiro de braços erguidos) sobrepõe o título por baixo; círculo central do campo atrás, centrado no título; faixa e microtexto nas bordas.
- **Dados (público, alcance):** um número dominante com legenda travada na linha de base; linhas do campo como contexto atrás; resto em tabela de placar.
- **Ativo:** foto do ativo em uso à direita (painel 5/12 + foto 7/12); um objeto do esporte sobrepõe a borda esquerda da foto em 1/3, na direção do título; fio liga o número do ativo ao título.
- **Cota:** preço como placar (numeral grande tabular) emoldurado pela "área" do campo; lista de direitos com divisórias de fio.
- **Divisores:** tipo gigante centrado e o campo inteiro em linhas finas sangrando.
Fugir da gramática pede um porquê escrito na composição da página.

## Bloco de estilo das cenas e objetos (marca.estilo_cena)
Sábado de manhã no interior de SP, sol baixo pela esquerda a 20°, lente de 35 a 50 mm, altura do olho, névoa leve, terra vermelha, uniformes preto e amarelo, fotografia real, sem texto. Objetos recortados com a mesma luz (pela esquerda, sombra para a direita).

## O que este kit não tem
Gráfico 3D, ícone decorativo solto, foto dos ex-atletas famosos (sem direito de imagem), números fora da tabela de provas, gradiente de duas paradas, brilho ou sombra por CSS.
