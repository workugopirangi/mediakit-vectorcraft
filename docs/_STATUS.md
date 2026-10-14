---
tags: [MP]
tipo: status
status: ativo
updated: 2026-10-13
autor: agente
---

# Onde a v10 está

- Skill `gerar-mediakit-motion` (v10) é a única de mídia kit desde 14/10/2026 (links em `~/.claude/skills` e `~/.agents/skills`). A v9 foi para `arquivo/v9/`; a v8 do claude.ai sai pelo Ugo.
- Kits feitos pela v10: Sprint × World Tennis (12 p., aprovado) e Copa AME 2027 (18 p., aguardando o Ugo).
- Provado: o kit Sprint × World Tennis (12 páginas) remonta pelo pacote com o mesmo texto do aprovado e a checagem dá 0 falhas.
- Testes: `python3 -m pytest` → 46 passed (13/10/2026).
- Receitas na versão travada do VectorCraft: 65 de 65 rodam (`receitas/_linha-de-base.json`). "Roda" é sair sem erro, não "funciona": o veredito visual de cada uma continua em `receitas/indice-*.md` (49 funcionam, 15 parciais, 1 não).
- Bibliotecas: referências (86 do repertório do cofre, entrada automática de referência nova), receitas (65), peças de patrocínio (3: pórtico, estande e camisa da World Tennis), formatos (ainda no cofre, da v9).
- Junção com a v9 feita e enxuta (SPEC seção 7). A comparação cega foi dispensada pelo Ugo em 14/10 ("é teste não, só faz").
- Pendente: segurança restante do Codex (ver `~/.claude/DEPOIS.md`), formatos e biblioteca de objetos quando um kit pedir.
