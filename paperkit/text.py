r"""Inline markup -> LaTeX.

Text in blocks uses a small, publisher-neutral markup:

    $...$              inline math (passed through)
    `code`             \texttt{}
    **bold**           \textbf{}
    *italic*           \emph{}
    \cite{a,b}         citation; rendered with the template's citation command
    \ref{label}        cross reference (figures, tables, equations, sections)
    bare URLs          wrapped in \url{}

Everything else is escaped for LaTeX, and common Unicode characters are mapped
to ASCII LaTeX so that the output compiles with pdfLaTeX and on any submission system.
"""
from __future__ import annotations

import re

TOKEN = re.compile(r"(\$[^$]+\$|`[^`]+`|\\cite\{[^}]+\}|\\ref\{[^}]+\}|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")
URL = re.compile(r"(https?://[^\s,;)}]+?)([.,;)]?(?:\s|$))")

UNI = {
    "–": "--", "—": "---", "×": r"$\times$", "≥": r"$\geq$", "≤": r"$\leq$", "≈": r"$\approx$",
    "±": r"$\pm$", "→": r"$\rightarrow$", "·": r"$\cdot$", "°": r"$^\circ$", "τ": r"$\tau$",
    "μ": r"$\mu$", "α": r"$\alpha$", "β": r"$\beta$", "σ": r"$\sigma$", "Δ": r"$\Delta$", "∈": r"$\in$",
    "“": "``", "”": "''", "‘": "`", "’": "'", "′": "'", "…": r"\ldots{}", "\u00a0": "~",
    "á": r"\'{a}", "é": r"\'{e}", "í": r"\'{\i}", "ó": r"\'{o}", "ú": r"\'{u}", "ñ": r"\~{n}",
    "ä": r"\"{a}", "ö": r"\"{o}", "ü": r"\"{u}", "Ä": r"\"{A}", "Ö": r"\"{O}", "Ü": r"\"{U}", "ß": r"\ss{}",
    "ç": r"\c{c}", "è": r"\`{e}", "à": r"\`{a}", "ø": r"\o{}", "å": r"\aa{}",
}
SPECIAL = {"%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape(s: str) -> str:
    out = []
    for ch in s:
        if ch in SPECIAL:
            out.append(SPECIAL[ch])
        elif ch in UNI:
            out.append(UNI[ch])
        elif ord(ch) > 127:
            raise ValueError(f"unsupported character {ch!r} (U+{ord(ch):04X}) in: {s[:60]}")
        else:
            out.append(ch)
    return "".join(out)


def wrap_urls(s: str) -> str:
    return URL.sub(lambda m: r"\url{" + m.group(1).replace(r"\_", "_").replace(r"\%", "%") + "}" + m.group(2), s)


def to_latex(s: str, cite: str = "cite") -> str:
    """Convert inline markup to LaTeX. ``cite`` is the citation command (cite, citep, ...)."""
    if not s:
        return ""
    out = []
    for part in TOKEN.split(s):
        if not part:
            continue
        if part.startswith("$"):
            out.append(part)
        elif part.startswith("\\cite"):
            out.append("\\" + cite + part[5:])
        elif part.startswith("\\ref"):
            out.append(part)
        elif part.startswith("`"):
            out.append(r"\texttt{" + escape(part[1:-1]) + "}")
        elif part.startswith("**"):
            out.append(r"\textbf{" + escape(part[2:-2]) + "}")
        elif part.startswith("*") and len(part) > 2:
            out.append(r"\emph{" + escape(part[1:-1]) + "}")
        else:
            out.append(escape(part))
    text = wrap_urls("".join(out))
    # non-breaking space before cross references and citations
    text = re.sub(r"(Fig\.|Figs\.|Figure|Table|Tables|Eq\.|Section|Appendix) \\ref\{", r"\1~\\ref{", text)
    text = re.sub(r"(\w) \\(cite|citep|citet)\{", r"\1~\\\2{", text)
    return text


def plain(s: str) -> str:
    """Strip inline markup (for PDF metadata, running heads, etc.)."""
    s = re.sub(r"\\cite\{[^}]+\}", "", s or "")
    s = re.sub(r"[*`$]", "", s)
    return re.sub(r"\s+", " ", s).strip()
