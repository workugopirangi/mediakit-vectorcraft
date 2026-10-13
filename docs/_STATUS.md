---
tags: [MP]
tipo: status
status: ativo
updated: 2026-10-13
autor: agente
---

# Onde a v10 está

- Skill `gerar-mediakit-vc` instalada ao lado da v9 (em `~/.claude/skills` e `~/.agents/skills`); ainda não substitui a v9.
- Provado: o kit Sprint × World Tennis (12 páginas) remonta pelo pacote com o mesmo texto do aprovado e a checagem dá 0 falhas.
- Testes: `python3 -m pytest` → 46 passed (13/10/2026).
- Receitas na versão travada do VectorCraft: 65 de 65 rodam (`receitas/_linha-de-base.json`). "Roda" é sair sem erro, não "funciona": o veredito visual de cada uma continua em `receitas/indice-*.md` (49 funcionam, 15 parciais, 1 não).
- Bibliotecas: referências (86 do repertório do cofre, entrada automática de referência nova), receitas (65), peças de patrocínio (3: pórtico, estande e camisa da World Tennis), formatos (ainda no cofre, da v9).
- Falta: junção com a v9 (SPEC seção 7) e a comparação cega (SPEC seção 8), quando a sessão v9 terminar.
