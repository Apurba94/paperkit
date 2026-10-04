"""IEEE (IEEEtran class, on CTAN / in every TeX distribution and on Overleaf)."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer


class IEEE(Writer):
    key = "ieee"
    title = "IEEE (IEEEtran)"
    docclass = "IEEEtran"
    cite = "cite"                     # IEEE uses the cite package, not natbib
    variants = [
        Variant("conference", "conference", "IEEE conference paper (two columns)", twocolumn=True),
        Variant("journal", "journal", "IEEE Transactions / journals (two columns)", twocolumn=True),
        Variant("journal-review", "journal,onecolumn,draftclsnofoot,12pt",
                "IEEE journal, single-column double-spaced copy for peer review"),
    ]
    notes = ("IEEE limits abstracts to 150-250 words and asks for the generative-AI disclosure in the "
             "Acknowledgment section.")

    def preamble(self, paper, v):
        return [rf"\documentclass[{v.options}]{{IEEEtran}}",
                r"\usepackage{cite}", r"\usepackage{amsmath,amssymb}", r"\usepackage{graphicx}",
                r"\usepackage{booktabs}", r"\usepackage{array}", r"\usepackage{url}", ""]

    def frontmatter(self, paper: Paper, v):
        L = [rf"\title{{{self.t(paper.title)}}}", ""]
        if v.key == "conference":
            blocks = []
            for a in paper.authors:
                aff = paper.affiliation(a.affiliations[0])
                lines = [rf"\textit{{{self.t(aff.department)}}}" if aff.department else "",
                         rf"\textit{{{self.t(aff.organization)}}}" if aff.organization else "",
                         self.t(", ".join(x for x in [aff.city, aff.country] if x)),
                         a.email]
                blocks.append(r"\IEEEauthorblockN{" + self.t(a.name) + r"}" + "\n" + r"\IEEEauthorblockA{"
                              + r" \\ ".join(x for x in lines if x) + "}")
            L += [r"\author{" + "\n\\and\n".join(blocks) + "}", ""]
        else:
            thanks = []
            for a in paper.authors:
                aff = paper.affiliation(a.affiliations[0])
                thanks.append(f"{self.t(a.name)} is with the {self.t(aff.one_line())}" +
                              (f" (e-mail: {a.email})." if a.email else "."))
            names = " and ".join(self.t(a.name) for a in paper.authors)
            L += [r"\author{" + names + r"\thanks{" + " ".join(thanks) + "}}", ""]
            journal = paper.extra.get("ieee_journal")      # e.g. "IEEE Transactions on Image Processing"
            if journal:
                short = self.t(paper.short_title or paper.title)
                L += [r"\markboth{" + self.t(journal) + "}{" + self.t(paper.authors[0].surname) + ": " + short + "}", ""]
        L += [r"\maketitle", "",
              r"\begin{abstract}", self.t(paper.abstract), r"\end{abstract}", "",
              r"\begin{IEEEkeywords}", self.t(", ".join(paper.keywords)), r"\end{IEEEkeywords}", ""]
        return L

    def after_body(self, paper, v):
        # IEEE order: appendices, acknowledgment, references
        return self.appendix(paper, v) + self.backmatter(paper, v) + self.references(paper, v) + [r"\end{document}"]

    def appendix(self, paper, v):
        blocks = paper.appendix_blocks()
        return (["", r"\appendices", ""] + self.body(blocks, v, appendix=True)) if blocks else []

    def backmatter(self, paper, v):
        L = []
        ack = self.acknowledgement_text(paper)
        if ack:
            L += [r"\section*{Acknowledgment}", ack, ""]
        data = paper.declarations.get("data_availability")
        if data:
            L += [r"\section*{Data Availability}", self.t(data), ""]
        return L

    def references(self, paper, v):
        return [r"\bibliographystyle{IEEEtran}", rf"\bibliography{{{self.bib_name}}}", ""]
