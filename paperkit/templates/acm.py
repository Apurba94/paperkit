"""ACM journals and conferences (acmart class, on CTAN)."""
from __future__ import annotations

from ..model import Paper
from ..text import plain
from .base import Variant, Writer


class ACM(Writer):
    key = "acm"
    title = "ACM (acmart)"
    docclass = "acmart"
    cite = "citep"
    variants = [
        Variant("sigconf", "sigconf", "ACM conference proceedings (two columns)", twocolumn=True),
        Variant("acmsmall", "acmsmall", "ACM journals (single column, e.g. TOMM, TIST, CSUR)"),
        Variant("manuscript-review", "manuscript,review,anonymous", "Anonymous single-column review manuscript"),
    ]
    notes = ("Replace the rights/conference/journal placeholders with the values from your ACM rights form. "
             "Choose CCS concepts at https://dl.acm.org/ccs and set them in paper.md (acm_ccs).")

    def preamble(self, paper, v):
        L = [rf"\documentclass[{v.options}]{{acmart}}", r"\usepackage{booktabs}", r"\usepackage{array}", "",
             r"\AtBeginDocument{\providecommand\BibTeX{{Bib\TeX}}}", ""]
        if v.key == "manuscript-review":
            L += [r"\setcopyright{none}", r"\settopmatter{printacmref=false}",
                  r"\renewcommand\footnotetextcopyrightpermission[1]{}", ""]
        else:
            L += [r"\setcopyright{acmlicensed}", r"\copyrightyear{2026}", r"\acmYear{2026}", r"\acmDOI{XXXXXXX.XXXXXXX}"]
            if v.key == "sigconf":
                L += [r"\acmConference[Conference acronym 'XX]{[Conference title]}{[Dates]}{[Location]}",
                      r"\acmISBN{978-1-4503-XXXX-X/2026/XX}"]
            else:
                journal = paper.extra.get("acm_journal", "TOMM")
                L += [rf"\acmJournal{{{journal}}}% ACM journal code, e.g. TOMM, TIST, CSUR, JACM, TOG (set acm_journal in paper.md)",
                      r"\acmVolume{1}", r"\acmNumber{1}", r"\acmArticle{1}", r"\acmMonth{1}"]
            L.append("")
        return L

    def frontmatter(self, paper: Paper, v):
        L = [rf"\title{{{self.t(paper.title)}}}", ""]
        for a in paper.authors:
            L.append(rf"\author{{{self.t(a.name)}}}")
            if a.orcid:
                L.append(rf"\orcid{{{a.orcid}}}")
            if a.email:
                L.append(rf"\email{{{a.email}}}")
            for aid in a.affiliations:
                aff = paper.affiliation(aid)
                parts = [rf"\department{{{self.t(aff.department)}}}" if aff.department else "",
                         rf"\institution{{{self.t(aff.organization)}}}",
                         rf"\city{{{self.t(aff.city)}}}" if aff.city else "",
                         rf"\country{{{self.t(aff.country)}}}" if aff.country else ""]
                L.append(r"\affiliation{" + "\n  ".join(x for x in parts if x) + "}")
            L.append("")
        short = ", ".join(a.surname for a in paper.authors[:3]) + (" et al." if len(paper.authors) > 3 else "")
        L += [rf"\renewcommand{{\shortauthors}}{{{self.t(short)}}}", "",
              r"\begin{abstract}", self.t(paper.abstract), r"\end{abstract}", ""]
        ccs = paper.extra.get("acm_ccs") or ["Computing methodologies~Computer vision"]
        for i, c in enumerate(ccs):
            L.append(rf"\ccsdesc[{500 if i == 0 else 300}]{{{c}}}")
        L += ["", rf"\keywords{{{self.t(', '.join(paper.keywords))}}}", "", r"\maketitle", ""]
        return L

    def figure_extra(self, b, v):
        return [rf"\Description{{{self.t(plain(b[3]))}}}"]

    def after_body(self, paper, v):
        L = []
        ack = self.acknowledgement_text(paper)
        if ack:
            L += [r"\begin{acks}", ack, r"\end{acks}", ""]
        data = paper.declarations.get("data_availability")
        if data:
            L += [r"\section*{Data Availability}", self.t(data), ""]
        L += [r"\bibliographystyle{ACM-Reference-Format}", rf"\bibliography{{{self.bib_name}}}", ""]
        L += self.appendix(paper, v)
        L += [r"\end{document}"]
        return L
