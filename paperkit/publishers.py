"""Publisher-owned class files that are not part of TeX distributions.

They are downloaded (or imported from a zip you downloaded) into a local cache,
``~/.paperkit/publishers/<template>/``, and copied next to the generated .tex files.
They are never committed to your repositories.
"""
from __future__ import annotations

import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path.home() / ".paperkit" / "publishers"

SOURCES = {
    "springer-nature": {
        "url": "https://cms-resources.apps.public.k8s.springernature.io/springer-cms/rest/v1/content/18782940/data/v12",
        "page": "https://www.springernature.com/gp/authors/campaigns/latex-author-support",
        "keep": lambda name: name.endswith(("sn-jnl.cls", ".bst")),
        "flatten": True,
    },
    "mdpi": {
        "url": "https://res.mdpi.com/data/MDPI_template_ACS.zip",
        "page": "https://www.mdpi.com/authors/latex",
        "keep": lambda name: "/Definitions/" in "/" + name or name.startswith("Definitions/"),
        "flatten": False,
    },
    "taylor-francis": {
        "url": None,   # behind a bot check: download interact.zip from your journal's author page
        "page": "Your Taylor & Francis journal's 'Instructions for authors' page (LaTeX template link)",
        "keep": lambda name: name.endswith(("interact.cls", ".bst")),
        "flatten": True,
    },
}


def _extract(data: bytes, key: str) -> list[str]:
    spec = SOURCES[key]
    dest = CACHE / key
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    written = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir() or not spec["keep"](name):
                continue
            if spec["flatten"]:
                target = dest / Path(name).name
            else:
                target = dest / name[name.index("Definitions/"):]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
            written.append(str(target.relative_to(dest)))
    return written


def fetch(keys=("springer-nature", "mdpi")) -> dict:
    out = {}
    for key in keys:
        spec = SOURCES[key]
        if not spec["url"]:
            out[key] = f"manual: download the template zip from {spec['page']} and run " \
                       f"`python -m paperkit import-files {key} <zip>`"
            continue
        req = urllib.request.Request(spec["url"], headers={"User-Agent": "Mozilla/5.0 (paperkit)"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        out[key] = f"{len(_extract(data, key))} files"
    return out


def import_zip(key: str, zip_path: str | Path) -> list[str]:
    return _extract(Path(zip_path).read_bytes(), key)


def available(key: str) -> bool:
    return (CACHE / key).exists() and any((CACHE / key).iterdir())


def copy_into(key: str, folder: Path) -> bool:
    src = CACHE / key
    if not available(key):
        return False
    for p in src.rglob("*"):
        if p.is_file():
            target = folder / p.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
    return True


def files_in(key: str) -> list[Path]:
    src = CACHE / key
    return [p.relative_to(src) for p in src.rglob("*") if p.is_file()] if src.exists() else []
