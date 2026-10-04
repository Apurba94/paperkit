"""Render a paper into every journal template, check it, and optionally compile it."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import publishers
from .check import parse_log, static_check
from .model import PLACEHOLDER, Paper
from .templates import BY_KEY, WRITERS

TECTONIC_CANDIDATES = [
    os.environ.get("PAPERKIT_TECTONIC", ""),
    shutil.which("tectonic") or "",
    str(Path.home() / ".paperkit" / "bin" / "tectonic.exe"),
    str(Path.home() / ".paperkit" / "bin" / "tectonic"),
]


def find_tectonic() -> str | None:
    return next((c for c in TECTONIC_CANDIDATES if c and Path(c).exists()), None)


def bib_keys(bib: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))


GS_CANDIDATES = [os.environ.get("PAPERKIT_GS", ""), shutil.which("gswin64c") or "", shutil.which("gs") or "",
                 str(Path.home() / ".paperkit" / "bin" / "gs" / "bin" / "gswin64c.exe")]
EPS_CACHE = Path.home() / ".paperkit" / "eps_cache"


def eps_as_pdf(eps: Path) -> bytes:
    """PDF rendering of an EPS file (Ghostscript), cached by content hash. Falls back to a blank
    placeholder of the same aspect ratio when Ghostscript is unavailable."""
    import hashlib

    data = eps.read_bytes()
    key = hashlib.sha256(data).hexdigest()[:20]
    cached = EPS_CACHE / f"{key}.pdf"
    if cached.exists():
        return cached.read_bytes()
    gs = next((c for c in GS_CANDIDATES if c and Path(c).exists()), None)
    EPS_CACHE.mkdir(parents=True, exist_ok=True)
    if gs:
        subprocess.run([gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-dEPSCrop", "-sDEVICE=pdfwrite",
                        f"-sOutputFile={cached}", str(eps)], check=True, capture_output=True, timeout=120)
        return cached.read_bytes()
    import re as _re
    from PIL import Image

    m = _re.search(rb"%%BoundingBox:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", data)
    w, h = ((int(m.group(3)) - int(m.group(1))), (int(m.group(4)) - int(m.group(2)))) if m else (200, 60)
    tmp = EPS_CACHE / f"{key}-placeholder.pdf"
    Image.new("RGB", (max(w, 1), max(h, 1)), (235, 235, 235)).save(tmp, "PDF", resolution=72)
    return tmp.read_bytes()


def compile_tex(tex: Path, tectonic: str, timeout: int = 1800) -> dict:
    build = tex.parent / "_build"
    build.mkdir(exist_ok=True)
    cmd = [tectonic, "-X", "compile", tex.name, "--outdir", "_build", "--keep-logs"]
    # Tectonic cannot convert EPS (pdfLaTeX on Overleaf / the journals does, via epstopdf). For the compile
    # test only, temporarily replace each .eps with its PDF rendering; xdvipdfmx detects the format by content.
    swapped = {}
    for eps in tex.parent.rglob("*.eps"):
        swapped[eps] = eps.read_bytes()
        eps.write_bytes(eps_as_pdf(eps))
    if swapped:   # and tell graphicx to read those .eps files as PDF (size from the PDF itself)
        src = tex.read_text(encoding="utf-8")
        swapped[tex] = src.encode("utf-8")
        hook = "\n\\AtBeginDocument{\\DeclareGraphicsRule{.eps}{pdf}{*}{}}% paperkit compile test only\n"
        i = src.index("\\documentclass")
        j = src.index("\n", src.index("}", src.index("{", i)))
        tex.write_text(src[:j] + hook + src[j + 1:], encoding="utf-8")
    try:
        p = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True, timeout=timeout)
        rc, stderr = p.returncode, p.stderr + p.stdout
    except subprocess.TimeoutExpired:
        rc, stderr = -1, "timeout"
    finally:
        for eps, data in swapped.items():
            eps.write_bytes(data)
    log_path = build / f"{tex.stem}.log"
    log = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
    info = parse_log(log)
    if not info["errors"]:   # Tectonic stops before writing a log on fatal errors; use its stderr
        info["errors"] = [l.split("error:", 1)[1].strip() for l in stderr.splitlines()
                          if l.startswith("error:") and "something bad happened" not in l
                          and "unrecoverable" not in l][:3]
    pdf = build / f"{tex.stem}.pdf"
    info.update({"ok": rc == 0 and pdf.exists(), "returncode": rc, "pages": None,
                 "stderr_tail": "\n".join(l for l in stderr.splitlines() if "error" in l.lower())[-1500:]})
    if pdf.exists():
        try:
            import pypdfium2

            info["pages"] = len(pypdfium2.PdfDocument(str(pdf)))
        except Exception:  # noqa: BLE001
            pass
        (tex.parent / "pdf").mkdir(exist_ok=True)
        shutil.move(str(pdf), tex.parent / "pdf" / pdf.name)
    return info


def write_folder(paper: Paper, writer, out: Path) -> dict:
    folder = out / writer.key
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    keys = bib_keys(paper.bib)
    files = []
    for v in writer.variants:
        name = f"{writer.key}-{v.key}.tex"
        (folder / name).write_text(writer.render(paper, v), encoding="utf-8")
        files.append((name, v))
    (folder / f"{writer.bib_name}.bib").write_text(writer.bib_for_template(paper.bib).strip() + "\n", encoding="utf-8")
    for f in paper.figure_files():
        shutil.copy2(Path(paper.figures_dir) / Path(f).name, folder / Path(f).name)
    writer.support_files(folder)
    has_files = True
    if writer.publisher_files:
        has_files = publishers.copy_into(writer.key, folder)
    checks = {name: static_check(folder / name, keys) for name, _ in files}
    return {"writer": writer, "folder": folder, "files": files, "publisher_files": has_files, "checks": checks,
            "compile": {}}


def build(paper: Paper, out: str | Path, only: list[str] | None = None, compile: bool = False,
          tectonic: str | None = None, keep_publisher_files: bool = True, log=print) -> list[dict]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    problems = paper.validate()
    if problems:
        raise ValueError("paper source has problems:\n  " + "\n  ".join(problems))
    writers = [BY_KEY[k] for k in only] if only else WRITERS
    tectonic = tectonic or (find_tectonic() if compile else None)
    results = []
    for w in writers:
        r = write_folder(paper, w, out)
        log(f"[{w.key}] {len(r['files'])} variant(s) written" + ("" if r["publisher_files"] else
                                                                 " (publisher class files not available locally)"))
        if compile and tectonic and r["publisher_files"]:
            for name, v in r["files"]:
                info = compile_tex(r["folder"] / name, tectonic)
                r["compile"][name] = info
                notes = ["OK" if info["ok"] else "FAILED"]
                if info["pages"]:
                    notes.append(f"{info['pages']} pages")
                if info["undefined_citations"] or info["undefined_references"]:
                    notes.append("undefined citations/references")
                if info["overfull_count"]:
                    notes.append(f"{info['overfull_count']} overfull lines (max {info['overfull_max_pt']:.0f}pt)")
                if info["errors"]:
                    notes.append("errors: " + " | ".join(info["errors"][:2]))
                log(f"    {name}: " + ", ".join(notes))
        shutil.rmtree(r["folder"] / "_build", ignore_errors=True)
        write_readme(paper, r)
        if not keep_publisher_files:
            for rel in publishers.files_in(w.key):
                target = r["folder"] / rel
                if target.exists():
                    target.unlink()
            shutil.rmtree(r["folder"] / "Definitions", ignore_errors=True)
        results.append(r)
    write_summary(paper, results, out)
    return results


def placeholders(paper: Paper) -> list[str]:
    from .model import DECLARATION_KEYS

    return [name for key, name in DECLARATION_KEYS if not paper.declarations.get(key)
            or PLACEHOLDER[:-2] in paper.declarations.get(key, "") or paper.declarations[key].startswith("[")]


def write_readme(paper: Paper, r: dict) -> None:
    w = r["writer"]
    rows = []
    for name, v in r["files"]:
        c = r["compile"].get(name)
        status = ("not compiled" if c is None else
                  ("compiles" + (f", {c['pages']} pages" if c["pages"] else "")) if c["ok"] else "COMPILE ERROR")
        issues = "; ".join(r["checks"][name]) or "none"
        rows.append(f"| `{name}` | `{v.options or '(none)'}` | {v.description} | {status} | {issues} |")
    pub = ""
    if w.publisher_files:
        pub = ("\n## Publisher files\n\nThis template needs the publisher's class files ("
               + ", ".join(f"`{f}`" for f in w.publisher_files) + "). "
               + ("They have been copied into this folder from your local paperkit cache; they are not "
                  "redistributed in public repositories."
                  if r["publisher_files"] else
                  "Run `python -m paperkit fetch` (or `import-files` for Taylor & Francis) and rebuild.")
               + f"\nOfficial source: {publishers.SOURCES[w.key]['page']}\n")
    todo = placeholders(paper)
    text = f"""# {w.title}

Generated by paperkit from the paper source. Every file in this folder renders the same paper; pick the
variant your target journal asks for.

| File | Class options | Variant | Compile test | Static checks |
|---|---|---|---|---|
{chr(10).join(rows)}
{pub}
## How to submit

1. **Overleaf:** upload this whole folder (or its zip) as a new project and set the chosen `.tex` file as
   the main document. Publisher templates are also in the Overleaf gallery.
2. **Local TeX:** `pdflatex FILE && bibtex FILE && pdflatex FILE && pdflatex FILE`
   (or `tectonic FILE.tex`).
3. Submit the `.tex`, `{w.bib_name}.bib` (or the generated `.bbl`) and the figure files.

## Before submitting

{w.notes}

""" + ("Fill in these statements in `paper.md` (they currently contain placeholders): "
       + ", ".join(todo) + ".\n" if todo else "All declaration statements are filled in.\n")
    (r["folder"] / "README.md").write_text(text, encoding="utf-8")


def write_summary(paper: Paper, results: list[dict], out: Path) -> None:
    lines = [f"# Journal versions of: {paper.title}", "",
             "Generated by [paperkit](https://github.com/Apurba94/paperkit). One folder per publisher; each folder "
             "has its own README with submission notes.", "",
             "| Publisher / template | Variants | Compile test | Folder |", "|---|---|---|---|"]
    summary = {}
    for r in results:
        w = r["writer"]
        n = len(r["files"])
        if r["compile"]:
            ok = sum(1 for c in r["compile"].values() if c["ok"])
            status = f"{ok}/{n} compile"
        elif not r["publisher_files"]:
            status = "publisher files missing"
        else:
            status = "not compiled"
        bad = sum(1 for c in r["checks"].values() if c)
        if bad:
            status += f", {bad} with static-check issues"
        lines.append(f"| {w.title} | {n} | {status} | [`{w.key}/`]({w.key}/) |")
        summary[w.key] = {"variants": [f for f, _ in r["files"]], "compile": r["compile"], "checks": r["checks"]}
    todo = placeholders(paper)
    lines += ["", "## Checklist before any submission", "",
              "- [ ] Abstract within the journal's word limit (current abstract: "
              f"{len(paper.abstract.split())} words).",
              "- [ ] Declarations completed" + (f" (placeholders: {', '.join(todo)})." if todo else "."),
              "- [ ] Journal-specific fields set (journal name, article type, conference/rights data for ACM).",
              "- [ ] Figures at the resolution the journal asks for (usually 300 dpi or vector).",
              "- [ ] Generative-AI use disclosed as the publisher requires (paperkit inserts `ai_use`).", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "build_report.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
