"""Run with: python -m pytest tests  (or python tests/test_paperkit.py)."""
from pathlib import Path
import shutil
import tempfile

from paperkit import build, read_paper, write_paper
from paperkit.templates import WRITERS

STARTER = Path(__file__).resolve().parents[1] / "paperkit" / "starter"


def test_starter_parses_and_validates():
    paper = read_paper(STARTER)
    assert paper.validate() == []
    kinds = [b[0] for b in paper.blocks]
    for k in ("section", "subsection", "p", "list", "eq", "figure", "table", "appendix"):
        assert k in kinds


def test_roundtrip():
    paper = read_paper(STARTER)
    with tempfile.TemporaryDirectory() as d:
        write_paper(paper, d)
        again = read_paper(d)
        assert [b[0] for b in again.blocks] == [b[0] for b in paper.blocks]
        assert again.abstract == paper.abstract and again.declarations == paper.declarations


def test_every_template_renders_and_passes_static_checks():
    paper = read_paper(STARTER)
    with tempfile.TemporaryDirectory() as d:
        results = build(paper, d, compile=False, log=lambda *_: None)
        assert len(results) == len(WRITERS)
        for r in results:
            for name, problems in r["checks"].items():
                assert problems == [], (name, problems)


if __name__ == "__main__":
    test_starter_parses_and_validates()
    test_roundtrip()
    test_every_template_renders_and_passes_static_checks()
    print("all tests passed")
