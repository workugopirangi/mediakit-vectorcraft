# Mídia kit v10 (rota VectorCraft)

Leia `docs/SPEC.md` (o que deve ser), `docs/_STATUS.md` (onde está) e `docs/falhas/` antes de mexer.
- Python: o ambiente próprio `~/.venvs/mediakit-vc` (3.12, `requirements.txt`). Atalho: `scripts/py`.
- Testes: `scripts/py -m pytest` (os marcados `vectorcraft` abrem o VectorCraft sem tela).
- O VectorCraft fica travado no commit de `vectorcraft/VERSAO`; trocar só depois de `scripts/py scripts/rodar_receitas.py` sem regressão.
- Esta é a skill `gerar-mediakit-motion` (v10), a única de mídia kit desde 14/10/2026 (links em `~/.claude/skills` e `~/.agents/skills`). A v9 está em `arquivo/v9/` (só consulta; bancada, exemplos e fontes ficam fora do git). O conhecimento (repertório, memória, formatos, régua) mora no cofre, em `SISTEMAS/GERAR MEDIAKIT/`.
- Sem travessão em nada que o Ugo lê. Commit sem coautoria.
