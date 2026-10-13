import re
from mediakit import config

SKILL = config.RAIZ / "skill"


def test_skill_curta():
    assert len((SKILL / "SKILL.md").read_text().splitlines()) <= 80


def test_todo_passo_citado_existe():
    citados = re.findall(r"passos/([^`)]+\.md)", (SKILL / "SKILL.md").read_text())
    assert len(citados) == 6
    for c in citados:
        assert (SKILL / "passos" / c).exists(), c


def test_sem_travessao_em_nada():
    for p in SKILL.rglob("*.md"):
        t = p.read_text()
        assert "\N{EM DASH}" not in t and "\N{EN DASH}" not in t, p.name


def test_referencia_nova_entra_na_biblioteca():
    t = (SKILL / "SKILL.md").read_text() + (SKILL / "passos" / "2 DIRIGIR.md").read_text()
    assert "mediakit.referencias adicionar" in t
