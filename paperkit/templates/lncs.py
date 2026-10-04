"""Springer Lecture Notes in Computer Science and other Springer proceedings (llncs class, on CTAN)."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer


class LNCS(Writer):
    key = "springer-lncs"
    title = "Springer LNCS / proceedings (llncs)"
    docclass = "llncs"
    cite = "cite"
    variants = [Variant("lncs", "runningheads", "LNCS / CCIS / LNAI proceedings with running heads")]
    notes = ("LNCS abstracts are 150-250 words and most venues limit papers to 12-16 pages including "
             "references; shorten or move material to the appendix if needed.")

    def preamble(self, paper, v):
        return [rf"\documentclass[{v.options}]{{llncs}}", r"\usepackage[T1]{fontenc}",
                r"\usepackage{graphicx}", r"\usepackage{amsmath,amssymb}", r"\usepackage{booktabs}",
                r"\usepackage{array}", r"\usepackage{url}", "",
                r"% llncs >= 2.23 provides the credits environment; fall back gracefully on older versions",
                r"\makeatletter",
                r"\@ifundefined{credits}{\newenvironment{credits}{\par\medskip\small}{\par}}{}",
                r"\makeatother",
                r"\providecommand{\discintname}{Disclosure of Interests}",
                r"\providecommand{\ackname}{Acknowledgements}", ""]

    def frontmatter(self, paper: Paper, v):
        names = []
        for a in paper.authors:
            inst = r"\inst{" + ",".join(str(i) for i in a.affiliations) + "}"
            orcid = rf"\orcidID{{{a.orcid}}}" if a.orcid else ""
            names.append(self.t(a.name) + inst + orcid)
        insts = []
        for aff in paper.affiliations:
            emails = [a.email for a in paper.authors if aff.id in a.affiliations and a.email]
            line = self.t(aff.one_line())
            if emails:
                line += r" \\ " + r"\email{" + ", ".join(emails) + "}"
            insts.append(line)
        initials = ", ".join(f"{a.initials} {a.surname}" for a in paper.authors[:3])
        if len(paper.authors) > 3:
            initials += " et al."
        return [rf"\title{{{self.t(paper.title)}}}",
                rf"\titlerunning{{{self.t(paper.short_title or paper.title)}}}",
                r"\author{" + r" \and ".join(names) + "}",
                rf"\authorrunning{{{self.t(initials)}}}",
                r"\institute{" + r" \and ".join(insts) + "}", "",
                r"\maketitle", "",
                r"\begin{abstract}", self.t(paper.abstract), "",
                r"\keywords{" + r" \and ".join(self.t(k) for k in paper.keywords) + "}",
                r"\end{abstract}", ""]

    def after_body(self, paper, v):
        L = self.appendix(paper, v)
        ack = self.acknowledgement_text(paper)
        L += ["", r"\begin{credits}"]
        if ack:
            L += [r"\subsubsection{\ackname} " + ack, ""]
        L += [r"\subsubsection{\discintname} " + self.t(paper.declaration("competing_interests")), r"\end{credits}", ""]
        data = paper.declarations.get("data_availability")
        if data:
            L += [r"\subsubsection*{Data availability.} " + self.t(data), ""]
        L += [r"\bibliographystyle{splncs04}", rf"\bibliography{{{self.bib_name}}}", "", r"\end{document}"]
        return L
