"""paperkit command line.

    python -m paperkit new PAPER_DIR             start a new paper from the starter template
    python -m paperkit build PAPER_DIR [--out DIR] [--only ieee,mdpi] [--compile] [--zip]
    python -m paperkit list                      list templates and variants
    python -m paperkit fetch                     download publisher class files (Springer Nature, MDPI)
    python -m paperkit import-files KEY ZIP      import publisher files from a downloaded zip
                                                 (e.g. taylor-francis interact.zip)
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

from . import publishers
from .build import build, find_tectonic
from .markdown import read_paper
from .templates import WRITERS

STARTER = Path(__file__).resolve().parent / "starter"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="paperkit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("folder")
    b = sub.add_parser("build")
    b.add_argument("folder")
    b.add_argument("--out", default=None, help="output folder (default: PAPER_DIR/journals)")
    b.add_argument("--only", default="", help="comma-separated template keys")
    b.add_argument("--compile", action="store_true", help="compile every variant with Tectonic")
    b.add_argument("--zip", action="store_true", help="also write one zip per template (for Overleaf)")
    sub.add_parser("list")
    sub.add_parser("fetch")
    i = sub.add_parser("import-files")
    i.add_argument("key")
    i.add_argument("zip")
    a = p.parse_args(argv)

    if a.cmd == "new":
        dest = Path(a.folder)
        if dest.exists() and any(dest.iterdir()):
            print(f"{dest} is not empty", file=sys.stderr)
            return 1
        shutil.copytree(STARTER, dest, dirs_exist_ok=True)
        print(f"created {dest}: edit paper.md and references.bib, put figures in figures/, then run\n"
              f"  python -m paperkit build {dest} --compile")
    elif a.cmd == "list":
        for w in WRITERS:
            print(f"{w.key:18s} {w.title}")
            for v in w.variants:
                print(f"    {v.key:22s} [{v.options}] {v.description}")
    elif a.cmd == "fetch":
        for k, msg in publishers.fetch(("springer-nature", "mdpi", "taylor-francis")).items():
            print(f"{k}: {msg}")
    elif a.cmd == "import-files":
        print("\n".join(publishers.import_zip(a.key, a.zip)))
    elif a.cmd == "build":
        paper = read_paper(a.folder)
        out = Path(a.out) if a.out else Path(a.folder) / "journals"
        if a.compile and not find_tectonic():
            print("Tectonic not found: install it (https://tectonic-typesetting.github.io) or set PAPERKIT_TECTONIC;"
                  " building without compiling.", file=sys.stderr)
        results = build(paper, out, only=[x for x in a.only.split(",") if x] or None, compile=a.compile)
        if a.zip:
            for r in results:
                zpath = out / f"{r['writer'].key}.zip"
                with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
                    for f in sorted(r["folder"].rglob("*")):
                        if f.is_file():
                            z.write(f, f"{r['writer'].key}/{f.relative_to(r['folder'])}")
        print(f"done: {out / 'README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
