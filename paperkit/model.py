"""Publisher-neutral representation of a paper.

A paper is metadata (title, authors, affiliations, abstract, keywords, back matter)
plus an ordered list of *blocks*.  Every template writer renders the same blocks, so
the text, numbers and references are identical in every journal format.

Block types (tuples, first element is the type):

    ("section", title, label)              label may be ""
    ("subsection", title, label)
    ("subsubsection", title, label)
    ("p", text)                            inline markup, see paperkit.text
    ("list", [item, ...])                  bulleted list
    ("enum", [item, ...])                  numbered list
    ("eq", latex, label)                   display equation (label may be "")
    ("figure", label, path, caption, wide, width)   width = fraction of the line width
    ("table", label, caption, header, rows, colspec, wide)
                                           colspec letters l/c/r, X = wrapping text column
    ("appendix", title, label)             starts an appendix section; following blocks
                                           belong to the appendix
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DECLARATION_KEYS = [
    ("funding", "Funding"),
    ("competing_interests", "Competing interests"),
    ("ethics_approval", "Ethics approval and consent to participate"),
    ("consent_for_publication", "Consent for publication"),
    ("data_availability", "Data availability"),
    ("materials_availability", "Materials availability"),
    ("code_availability", "Code availability"),
    ("author_contributions", "Author contributions"),
]

PLACEHOLDER = "[Author to complete.]"


@dataclass
class Affiliation:
    id: int
    department: str = ""
    organization: str = ""
    street: str = ""
    city: str = ""
    postcode: str = ""
    state: str = ""
    country: str = ""

    def one_line(self) -> str:
        parts = [self.department, self.organization, self.street, self.city, self.postcode, self.state, self.country]
        return ", ".join(p for p in parts if p)


@dataclass
class Author:
    given: str
    surname: str
    email: str = ""
    affiliations: list[int] = field(default_factory=lambda: [1])
    corresponding: bool = False
    orcid: str = ""

    @property
    def name(self) -> str:
        return f"{self.given} {self.surname}".strip()

    @property
    def initials(self) -> str:
        """'Janin A' -> 'J.A.'"""
        return "".join(p[0] + "." for p in self.given.replace("-", " ").split() if p)


@dataclass
class Paper:
    title: str
    authors: list[Author]
    affiliations: list[Affiliation]
    abstract: str                       # journal abstract (about 150-250 words)
    keywords: list[str]
    blocks: list[tuple]
    bib: str                            # BibTeX source
    figures_dir: Path | None = None     # where figure files referenced by blocks live
    short_title: str = ""
    abstract_long: str = ""             # optional longer abstract (preprints)
    highlights: list[str] = field(default_factory=list)   # Elsevier: 3-5 items, <= 85 characters
    acknowledgements: str = ""
    ai_use: str = ""                    # disclosure of generative-AI use
    declarations: dict[str, str] = field(default_factory=dict)
    supplementary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ helpers
    @property
    def corresponding(self) -> Author:
        return next((a for a in self.authors if a.corresponding), self.authors[0])

    def declaration(self, key: str) -> str:
        return self.declarations.get(key) or PLACEHOLDER

    def affiliation(self, aid: int) -> Affiliation:
        return next(a for a in self.affiliations if a.id == aid)

    def main_blocks(self) -> list[tuple]:
        out = []
        for b in self.blocks:
            if b[0] == "appendix":
                break
            out.append(b)
        return out

    def appendix_blocks(self) -> list[tuple]:
        for i, b in enumerate(self.blocks):
            if b[0] == "appendix":
                return self.blocks[i:]
        return []

    def figure_files(self) -> list[str]:
        return [b[2] for b in self.blocks if b[0] == "figure"]

    def validate(self) -> list[str]:
        """Return a list of problems (empty if the paper is consistent)."""
        import re

        problems = []
        keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", self.bib))
        labels = set()
        for b in self.blocks:
            if b[0] in ("section", "subsection", "subsubsection", "appendix") and len(b) > 2 and b[2]:
                labels.add(b[2])
            elif b[0] == "eq" and b[2]:
                labels.add(b[2])
            elif b[0] in ("figure", "table"):
                labels.add(b[1])
        texts = [self.abstract, self.abstract_long, self.acknowledgements, self.supplementary]
        for b in self.blocks:
            if b[0] == "p":
                texts.append(b[1])
            elif b[0] in ("list", "enum"):
                texts += list(b[1])
            elif b[0] == "figure":
                texts.append(b[3])
            elif b[0] == "table":
                texts += [b[2]] + list(b[3]) + [str(c) for row in b[4] for c in row]
        for t in texts:
            for group in re.findall(r"\\cite\{([^}]+)\}", t or ""):
                for k in group.split(","):
                    if k.strip() not in keys:
                        problems.append(f"citation '{k.strip()}' not in the bibliography")
            for ref in re.findall(r"\\ref\{([^}]+)\}", t or ""):
                if ref not in labels:
                    problems.append(f"reference to undefined label '{ref}'")
        if self.figures_dir:
            for f in self.figure_files():
                if not (Path(self.figures_dir) / Path(f).name).exists():
                    problems.append(f"figure file missing: {f}")
        for h in self.highlights:
            if len(h) > 85:
                problems.append(f"highlight longer than 85 characters: {h[:40]}...")
        return problems
