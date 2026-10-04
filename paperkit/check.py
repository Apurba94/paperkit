"""Static checks on generated LaTeX and parsing of compile logs."""
from __future__ import annotations

import re
from pathlib import Path


def static_check(tex_path: Path, bib_keys: set[str]) -> list[str]:
    t = tex_path.read_text(encoding="utf-8")
    body = "\n".join("" if ln.lstrip().startswith("%") else re.sub(r"(?<!\\)%.*$", "", ln) for ln in t.splitlines())
    problems = []
    stack = []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", body):
        if m.group(1) == "begin":
            stack.append(m.group(2))
        elif not stack or stack.pop() != m.group(2):
            problems.append(f"unbalanced \\end{{{m.group(2)}}}")
    if stack:
        problems.append(f"unclosed environments {stack}")
    stripped = re.sub(r"\\[{}$%&#_]", "", body)
    if stripped.count("{") != stripped.count("}"):
        problems.append(f"brace imbalance ({stripped.count('{')} vs {stripped.count('}')})")
    if stripped.count("$") % 2:
        problems.append("odd number of $ signs")
    if any(ord(c) > 127 for c in t):
        problems.append("non-ASCII characters present")
    labels = set(re.findall(r"\\label\{([^}]+)\}", body))
    for ref in sorted(set(re.findall(r"\\ref\{([^}]+)\}", body)) - labels):
        problems.append(f"undefined reference {ref}")
    cites = {k.strip() for g in re.findall(r"\\cite[pt]?\{([^}]+)\}", body) for k in g.split(",")}
    for k in sorted(cites - bib_keys):
        problems.append(f"citation {k} missing from the .bib")
    for f in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", body):
        if not (tex_path.parent / f).exists():
            problems.append(f"missing figure {f}")
    return problems


def parse_log(log: str) -> dict:
    overfull = [float(x) for x in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log)]
    return {
        "undefined_citations": sorted(set(re.findall(r"Citation `([^']+)' (?:on page \d+ )?undefined", log))),
        "undefined_references": sorted(set(re.findall(r"Reference `([^']+)' on page \d+ undefined", log))),
        "overfull_max_pt": max(overfull) if overfull else 0.0,
        "overfull_count": sum(1 for x in overfull if x > 2.0),
        "errors": re.findall(r"^! (.+)$", log, re.M)[:5],
    }
