"""Read and write the human-editable paper source: ``paper.md`` (YAML front matter + Markdown body)
and ``references.bib``.

Body syntax
-----------
    # Section title {#sec:intro}         (## subsection, ### subsubsection)
    # Appendix: Title {#sec:appA}        starts the appendix
    Plain paragraphs, **bold**, *italic*, `code`, $inline math$
    [@key] or [@key1; @key2]             citations (keys from references.bib)
    @fig:label  @tab:label  @eq:label  @sec:label     cross references
    - item / 1. item                     lists

    $$
    C_t = \\sum_i x_i
    $$ {#eq:count}

    ![Caption text.](figures/fig1.png){#fig:overview wide width=1.0}

    Table: Caption text. {#tab:results cols=Xrrr wide}
    | Method | P | R | F1 |
    |---|---|---|---|
    | A | 0.9 | 0.8 | 0.85 |

``wide`` makes a figure/table span both columns in two-column journals; ``cols`` gives
column alignment (l, c, r; X = wrapping text column).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .model import Affiliation, Author, Paper

HEADING = re.compile(r"^(#{1,3})\s+(.*?)(?:\s*\{#([\w:.\-]+)\})?\s*$")
FIGURE = re.compile(r"^!\[(.*)\]\(([^)]+)\)(?:\{([^}]*)\})?\s*$")
CAPTION = re.compile(r"^Table:\s*(.*?)\s*(?:\{([^}]*)\})?\s*$")
EQ_END = re.compile(r"^(.*?)\$\$\s*(?:\{#([\w:.\-]+)\})?\s*$")


# ---------------------------------------------------------------------------- inline
def md_inline_to_markup(s: str) -> str:
    s = re.sub(r"\[((?:@[\w:.\-]+\s*;?\s*)+)\]",
               lambda m: r"\cite{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";") if k.strip()) + "}", s)
    return re.sub(r"(?<![\w.@])@((?:fig|tab|eq|sec):[\w\-]+(?:\.[\w\-]+)*)", r"\\ref{\1}", s)


def markup_to_md_inline(s: str) -> str:
    s = re.sub(r"\\cite\{([^}]+)\}", lambda m: "[" + "; ".join("@" + k.strip() for k in m.group(1).split(",")) + "]", s)
    return re.sub(r"\\ref\{((?:fig|tab|eq|sec):[^}]+)\}", r"@\1", s)


def parse_attrs(attrs: str | None) -> dict:
    out = {}
    for tok in (attrs or "").split():
        if tok.startswith("#"):
            out["label"] = tok[1:]
        elif "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
        else:
            out[tok] = True
    return out


# ---------------------------------------------------------------------------- read
def read_paper(folder: str | Path) -> Paper:
    folder = Path(folder)
    text = (folder / "paper.md").read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise ValueError("paper.md must start with a YAML front matter block between --- lines")
    meta = yaml.safe_load(m.group(1)) or {}
    blocks = parse_body(m.group(2))
    bib_file = folder / meta.get("bibliography", "references.bib")
    bib = bib_file.read_text(encoding="utf-8") if bib_file.exists() else ""
    affs = [Affiliation(**a) for a in meta.get("affiliations", [])]
    authors = [Author(**a) for a in meta.get("authors", [])]
    known = {"title", "short_title", "authors", "affiliations", "abstract", "abstract_long", "keywords",
             "highlights", "acknowledgements", "ai_use", "declarations", "supplementary", "bibliography"}
    return Paper(
        title=meta["title"], short_title=meta.get("short_title", ""), authors=authors, affiliations=affs,
        abstract=md_inline_to_markup(str(meta.get("abstract", "")).strip()),
        abstract_long=md_inline_to_markup(str(meta.get("abstract_long", "")).strip()),
        keywords=list(meta.get("keywords", [])), highlights=list(meta.get("highlights", [])),
        acknowledgements=md_inline_to_markup(str(meta.get("acknowledgements", "")).strip()),
        ai_use=str(meta.get("ai_use", "")).strip(),
        declarations={k: str(v).strip() for k, v in (meta.get("declarations") or {}).items()},
        supplementary=md_inline_to_markup(str(meta.get("supplementary", "")).strip()),
        blocks=blocks, bib=bib, figures_dir=folder / meta.get("figures_dir", "figures"),
        extra={k: v for k, v in meta.items() if k not in known},
    )


def parse_body(body: str) -> list[tuple]:
    lines = body.splitlines()
    blocks: list[tuple] = []
    pending_caption = None
    i = 0
    para: list[str] = []

    def flush():
        nonlocal para
        if para:
            blocks.append(("p", md_inline_to_markup(" ".join(s.strip() for s in para))))
            para = []

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        h = HEADING.match(s)
        if h:
            flush()
            level, title, label = len(h.group(1)), h.group(2).strip(), h.group(3) or ""
            if level == 1 and title.lower().startswith("appendix:"):
                blocks.append(("appendix", md_inline_to_markup(title.split(":", 1)[1].strip()), label))
            else:
                kind = {1: "section", 2: "subsection", 3: "subsubsection"}[level]
                blocks.append((kind, md_inline_to_markup(title), label))
            i += 1
            continue
        if s.startswith("$$"):
            flush()
            rest = s[2:]
            eq_lines = []
            m_end = EQ_END.match(rest) if rest.strip() else None
            if m_end and rest.strip():
                eq_lines.append(m_end.group(1))
                label = m_end.group(2) or ""
                i += 1
            else:
                if rest.strip():
                    eq_lines.append(rest)
                i += 1
                label = ""
                while i < len(lines):
                    m_end = EQ_END.match(lines[i].strip())
                    if m_end:
                        if m_end.group(1).strip():
                            eq_lines.append(m_end.group(1))
                        label = m_end.group(2) or ""
                        i += 1
                        break
                    eq_lines.append(lines[i])
                    i += 1
            blocks.append(("eq", "\n".join(x.strip() for x in eq_lines).strip(), label))
            continue
        if s.startswith("![") and not FIGURE.match(s):       # caption spread over several lines
            j = i
            joined = s
            while j + 1 < len(lines) and not FIGURE.match(joined) and lines[j + 1].strip():
                j += 1
                joined += " " + lines[j].strip()
            if FIGURE.match(joined):
                s = joined
                i = j
        if s.startswith("Table:") and "{" not in s:         # caption continued on the next lines
            j = i
            joined = s
            while j + 1 < len(lines) and lines[j + 1].strip() and not lines[j + 1].strip().startswith("|"):
                j += 1
                joined += " " + lines[j].strip()
                if "}" in lines[j]:
                    break
            s = joined
            i = j
        f = FIGURE.match(s)
        if f:
            flush()
            a = parse_attrs(f.group(3))
            blocks.append(("figure", a.get("label", ""), f.group(2), md_inline_to_markup(f.group(1)),
                           bool(a.get("wide")), float(a.get("width", 1.0 if a.get("wide") else 0.62))))
            i += 1
            continue
        c = CAPTION.match(s)
        if c:
            flush()
            pending_caption = (md_inline_to_markup(c.group(1)), parse_attrs(c.group(2)))
            i += 1
            if blocks and blocks[-1][0] == "table" and blocks[-1][2] == "":  # caption after table
                _, _, _, header, rows, colspec, wide = blocks.pop()
                cap, a = pending_caption
                blocks.append(("table", a.get("label", ""), cap, header, rows, a.get("cols", colspec),
                               bool(a.get("wide", wide))))
                pending_caption = None
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip().replace(r"\|", "|") for x in re.split(r"(?<!\\)\|", lines[i].strip().strip("|"))]
                rows.append(cells)
                i += 1
            header, sep, body_rows = rows[0], rows[1], rows[2:]
            colspec = "".join("c" if x.startswith(":") and x.endswith(":") else "r" if x.endswith(":") else "l"
                              for x in sep)
            header = [md_inline_to_markup(x) for x in header]
            body_rows = [[md_inline_to_markup(x) for x in r] for r in body_rows]
            if pending_caption:
                cap, a = pending_caption
                blocks.append(("table", a.get("label", ""), cap, header, body_rows, a.get("cols", colspec),
                               bool(a.get("wide"))))
                pending_caption = None
            else:
                blocks.append(("table", "", "", header, body_rows, colspec, False))
            continue
        if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
            flush()
            numbered = bool(re.match(r"^\d+\.\s+", s))
            items = []
            while i < len(lines) and lines[i].strip():
                t = lines[i].strip()
                mm = re.match(r"^(?:[-*]|\d+\.)\s+(.*)$", t)
                if mm:
                    items.append(mm.group(1))
                elif items:
                    items[-1] += " " + t
                i += 1
            blocks.append(("enum" if numbered else "list", [md_inline_to_markup(x) for x in items]))
            continue
        para.append(line)
        i += 1
    flush()
    return blocks


# ---------------------------------------------------------------------------- write
def write_paper(paper: Paper, folder: str | Path, copy_figures: bool = True) -> Path:
    import shutil

    folder = Path(folder)
    (folder / "figures").mkdir(parents=True, exist_ok=True)
    meta = {
        "title": paper.title,
        "short_title": paper.short_title,
        "authors": [{k: v for k, v in a.__dict__.items() if v not in ("", None)} for a in paper.authors],
        "affiliations": [{k: v for k, v in a.__dict__.items() if v not in ("", None)} for a in paper.affiliations],
        "abstract": markup_to_md_inline(paper.abstract),
        "abstract_long": markup_to_md_inline(paper.abstract_long),
        "keywords": paper.keywords,
        "highlights": paper.highlights,
        "acknowledgements": markup_to_md_inline(paper.acknowledgements),
        "ai_use": paper.ai_use,
        "declarations": paper.declarations,
        "supplementary": markup_to_md_inline(paper.supplementary),
        "bibliography": "references.bib",
    }
    meta = {k: v for k, v in meta.items() if v not in ("", [], {}, None)}
    out = ["---", yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=110).rstrip(), "---", ""]
    for b in paper.blocks:
        kind = b[0]
        if kind in ("section", "subsection", "subsubsection"):
            hashes = {"section": "#", "subsection": "##", "subsubsection": "###"}[kind]
            out += [f"{hashes} {markup_to_md_inline(b[1])}" + (f" {{#{b[2]}}}" if b[2] else ""), ""]
        elif kind == "appendix":
            out += [f"# Appendix: {markup_to_md_inline(b[1])}" + (f" {{#{b[2]}}}" if b[2] else ""), ""]
        elif kind == "p":
            out += [markup_to_md_inline(b[1]), ""]
        elif kind in ("list", "enum"):
            out += [("1. " if kind == "enum" else "- ") + markup_to_md_inline(x) for x in b[1]] + [""]
        elif kind == "eq":
            out += ["$$", b[1], "$$" + (f" {{#{b[2]}}}" if b[2] else ""), ""]
        elif kind == "figure":
            _, label, path, caption, wide, width = b
            attrs = " ".join(x for x in [f"#{label}" if label else "", "wide" if wide else "", f"width={width:g}"] if x)
            out += [f"![{markup_to_md_inline(caption)}](figures/{Path(path).name}){{{attrs}}}", ""]
            if copy_figures and paper.figures_dir:
                src = Path(paper.figures_dir) / Path(path).name
                if src.exists():
                    shutil.copy2(src, folder / "figures" / src.name)
        elif kind == "table":
            _, label, caption, header, rows, colspec, wide = b
            attrs = " ".join(x for x in [f"#{label}" if label else "", f"cols={colspec}", "wide" if wide else ""] if x)
            out.append(f"Table: {markup_to_md_inline(caption)} {{{attrs}}}")
            sep = ["---:" if c == "r" else ":---:" if c == "c" else "---" for c in colspec.replace("X", "l")]
            esc = lambda x: markup_to_md_inline(str(x)).replace("|", r"\|")  # noqa: E731
            out.append("| " + " | ".join(esc(h) for h in header) + " |")
            out.append("|" + "|".join(sep) + "|")
            out += ["| " + " | ".join(esc(c) for c in row) + " |" for row in rows]
            out.append("")
    (folder / "paper.md").write_text("\n".join(out), encoding="utf-8")
    (folder / "references.bib").write_text(paper.bib.strip() + "\n", encoding="utf-8")
    return folder / "paper.md"
