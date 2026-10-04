"""Generic preprint (arXiv, SSRN, TechRxiv, institutional repositories): standard article class only,
so it compiles on any TeX installation without extra files."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer


class Preprint(Writer):
    key = "preprint-arxiv"
    title = "Preprint / arXiv (article class)"
    docclass = "article"
    cite = "citep"
    variants = [Variant("arxiv", "11pt,a4paper", "Single-column preprint for arXiv and other repositories")]
    notes = "Uses only standard packages; upload the .tex, .bbl (or .bib) and figures to arXiv."

    def preamble(self, paper, v):
        return [rf"\documentclass[{v.options}]{{article}}", r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}",
                r"\usepackage[margin=2.5cm]{geometry}", r"\usepackage{amsmath,amssymb}", r"\usepackage{graphicx}",
                r"\usepackage{booktabs}", r"\usepackage{array}", r"\usepackage[numbers,sort&compress]{natbib}",
                r"\usepackage[hidelinks]{hyperref}", ""]

    def frontmatter(self, paper: Paper, v):
        authors = []
        for a in paper.authors:
            # \author is typeset in a tabular (one row per \\); each affiliation part gets its own row
            # so long affiliations never run past the margin
            rows = [self.t(a.name)]
            for i in a.affiliations:
                aff = paper.affiliation(i)
                parts = [aff.department, aff.organization, ", ".join(x for x in [aff.city, aff.country] if x)]
                rows += [r"\small " + self.t(p) for p in parts if p]
            if a.email:
                rows.append(rf"\small\texttt{{{a.email}}}")
            authors.append(r" \\ ".join(rows))
        return [rf"\title{{{self.t(paper.title)}}}", r"\author{" + r" \and ".join(authors) + "}", r"\date{}", "",
                r"\maketitle", "", r"\begin{abstract}", self.t(paper.abstract_long or paper.abstract), r"\end{abstract}",
                "", r"\noindent\textbf{Keywords:} " + self.t(", ".join(paper.keywords)), ""]

    def backmatter(self, paper, v):
        L = []
        ack = self.acknowledgement_text(paper)
        if ack:
            L += [r"\section*{Acknowledgments}", ack, ""]
        for key, title in (("data_availability", "Data availability"), ("code_availability", "Code availability")):
            if paper.declarations.get(key):
                L += [rf"\section*{{{title}}}", self.t(paper.declarations[key]), ""]
        return L

    def references(self, paper, v):
        return [r"\bibliographystyle{unsrtnat}", rf"\bibliography{{{self.bib_name}}}", ""]
