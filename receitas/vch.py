"""Ponte: as receitas importam `vch`; o cliente agora mora em src/mediakit/vc.py."""
import sys
from pathlib import Path

_SRC = next(p / "src" for p in Path(__file__).resolve().parents if (p / "src" / "mediakit").exists())
sys.path.insert(0, str(_SRC))
from mediakit.vc import VC, VCError  # noqa: E402,F401
