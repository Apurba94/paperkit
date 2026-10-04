"""Taylor & Francis journals (interact class, Interact layout with NLM numbered references)."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer


class TandF(Writer):
    key = "taylor-francis"
    title = "Taylor & Francis journals (interact)"
    docclass = "interact"
    cite = "citep"
    variants = [Variant("interact-nlm", "", "Interact layout, NLM numbered references")]
    publisher_files = ["interact.cls", "tfnlm.bst"]
    notes = ("Taylor & Francis provides interact.cls via each journal's Instructions for Authors page; some "
             "journals use other reference styles (APA, Chicago) with a different .bst.")

    def preamble(self, paper, v):
        return [r"\documentclass[]{interact}", r"\usepackage[numbers,sort&compress]{natbib}",
                r"\bibpunct[, ]{[}{]}{,}{n}{,}{,}", r"\renewcommand\bibfont{\fontsize{10}{12}\selectfont}",
                r"\makeatletter", r"\def\NAT@def@citea{\def\@citea{\NAT@separator}}", r"\makeatother",
                r"\usepackage{array}", r"\usepackage{url}", ""]

    def frontmatter(self, paper: Paper, v):
        corr = paper.corresponding
        letters = "abcdefghij"
        names = []
        for a in paper.authors:
            sup = ",".join(letters[i - 1] for i in a.affiliations)
            thanks = (rf"\thanks{{CONTACT {self.t(a.name)}. Email: {a.email}}}" if a is corr and a.email else "")
            names.append(f"{self.t(a.name)}\\textsuperscript{{{sup}}}{thanks}")
        affs = "; ".join(rf"\textsuperscript{{{letters[aff.id - 1]}}}{self.t(aff.one_line())}" for aff in paper.affiliations)
        joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        return [r"\articletype{ARTICLE}", "", rf"\title{{{self.t(paper.title)}}}", "",
                r"\author{", rf"\name{{{joined}}}", rf"\affil{{{affs}}}", "}", "", r"\maketitle", "",
                r"\begin{abstract}", self.t(paper.abstract), r"\end{abstract}", "",
                r"\begin{keywords}", "; ".join(self.t(k) for k in paper.keywords), r"\end{keywords}", ""]

    def backmatter(self, paper, v):
        t = self.t
        L = []
        ack = self.acknowledgement_text(paper)
        if ack:
            L += [r"\section*{Acknowledgement(s)}", ack, ""]
        L += [r"\section*{Disclosure statement}", t(paper.declaration("competing_interests")), "",
              r"\section*{Funding}", t(paper.declaration("funding")), "",
              r"\section*{Data availability statement}", t(paper.declaration("data_availability")), ""]
        return L

    def references(self, paper, v):
        return [r"\bibliographystyle{tfnlm}", rf"\bibliography{{{self.bib_name}}}", ""]

    def after_body(self, paper, v):
        # T&F: references, then appendices
        return self.backmatter(paper, v) + self.references(paper, v) + self.appendix(paper, v) + [r"\end{document}"]
