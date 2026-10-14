# Mídia kit v10 (rota VectorCraft)

Leia `docs/SPEC.md` (o que deve ser), `docs/_STATUS.md` (onde está) e `docs/falhas/` antes de mexer.
- Python: o ambiente próprio `~/.venvs/mediakit-vc` (3.12, `requirements.txt`). Atalho: `scripts/py`.
- Testes: `scripts/py -m pytest` (os marcados `vectorcraft` abrem o VectorCraft sem tela).
- O VectorCraft fica travado no commit de `vectorcraft/VERSAO`; trocar só depois de `scripts/py scripts/rodar_receitas.py` sem regressão.
- A v9 terminou (14/10): as ferramentas dela entram como cópia em `src/mediakit/ferramentas/` (plano `docs/superpowers/plans/2026-10-14-juncao-v9.md`); a pasta `pipeline/` da v9 não se edita até o fim do teste cego.
- Sem travessão em nada que o Ugo lê. Commit sem coautoria.
@AGENTS.md
