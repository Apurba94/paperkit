"""MDPI journals (Definitions/mdpi.cls, official MDPI LaTeX template)."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer

JOURNALS = [
    ("drones", "Drones"), ("remotesensing", "Remote Sensing"), ("sensors", "Sensors"),
    ("applsci", "Applied Sciences"), ("electronics", "Electronics"), ("jimaging", "Journal of Imaging"),
    ("ai", "AI"), ("computers", "Computers"), ("information", "Information"), ("bdcc", "Big Data and Cognitive Computing"),
]


class MDPI(Writer):
    key = "mdpi"
    title = "MDPI journals (mdpi.cls)"
    docclass = "Definitions/mdpi"
    cite = "citep"
    figure_pos = "H"
    table_pos = "H"
    variants = [Variant(j, f"{j},article,submit", f"MDPI {name}", extra={"journal": j}) for j, name in JOURNALS]
    publisher_files = ["Definitions/"]
    notes = ("MDPI abstracts are a single paragraph of at most 200 words, with 3-10 keywords. Change the journal "
             "by editing the first \\documentclass option (list in Definitions/journalnames.tex).")

    def render(self, paper: Paper, v: Variant) -> str:
        # MDPI puts all metadata before \begin{document}; the class typesets the title page itself
        L = (self.header(paper, v) + [r"\PassOptionsToPackage{hyphens}{url}"] + self.preamble(paper, v)
             + self.COMMON_PREAMBLE + self.metadata(paper, v))
        L += [r"\begin{document}", ""] + self.body(paper.main_blocks(), v) + self.after_body(paper, v)
        text = "\n".join(L).rstrip() + "\n"
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        return text

    def preamble(self, paper, v):
        authors = "moreauthors" if len(paper.authors) > 1 else "oneauthor"
        return [rf"\documentclass[{v.options},{authors}]{{Definitions/mdpi}}", "",
                r"%=================================================================",
                r"% MDPI internal commands - do not modify",
                r"\firstpage{1}", r"\makeatletter", r"\setcounter{page}{\@firstpage}", r"\makeatother",
                r"\pubvolume{1}", r"\issuenum{1}", r"\articlenumber{0}", r"\pubyear{2026}", r"\copyrightyear{2026}",
                r"\datereceived{ }", r"\daterevised{ }", r"\dateaccepted{ }", r"\datepublished{ }",
                "", r"\usepackage{array}", ""]

    def metadata(self, paper: Paper, v):
        corr = paper.corresponding
        L = [rf"\Title{{{self.t(paper.title)}}}", ""]
        orcids = [a for a in paper.authors if a.orcid]
        letters = "ABCDEFGHIJ"
        for i, a in enumerate(orcids):
            L.append(rf"\newcommand{{\orcidauthor{letters[i]}}}{{{a.orcid}}}")
        names = []
        for a in paper.authors:
            sup = ",".join(str(x) for x in a.affiliations)
            orc = rf"\orcid{letters[orcids.index(a)]}{{}}" if a in orcids else ""
            mark = f"$^{{{sup},}}$*" if a is corr else f"$^{{{sup}}}$"     # MDPI: "Name $^{1,}$*"
            names.append(f"{self.t(a.name)} {mark}" + orc)
        joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        L += [rf"\Author{{{joined}}}", rf"\AuthorNames{{{self.t(self.author_list(paper))}}}", ""]
        if len(paper.affiliations) == 1:
            aff = paper.affiliations[0]
            L += [r"\address[1]{" + self.t(aff.one_line()) + "}"]
        else:
            L += [r"\address{%"] + [rf"$^{{{aff.id}}}$ \quad {self.t(aff.one_line())}" +
                                    (r"\\" if i < len(paper.affiliations) - 1 else "}")
                                    for i, aff in enumerate(paper.affiliations)]
        L += [rf"\corres{{Correspondence: {corr.email}}}", "",
              rf"\abstract{{{self.t(paper.abstract)}}}", "",
              r"\keyword{" + "; ".join(self.t(k) for k in paper.keywords) + "}", ""]
        return L

    def frontmatter(self, paper, v):
        return []

    def bib_for_template(self, bib: str) -> str:
        # mdpi.bst prints "In Proceedings of the <booktitle>", so drop that prefix from booktitles
        import re

        return re.sub(r"(booktitle\s*=\s*[{\"])\s*(?:Proceedings of the|Proceedings of|Proc\.)\s+", r"\1", bib,
                      flags=re.I)

    def figure(self, b, v):
        _, label, path, caption, wide, width = b
        w = r"\textwidth" if (wide or width >= 0.999) else f"{width:.2f}\\textwidth"
        return [rf"\begin{{figure}}[H]", r"\centering", rf"\includegraphics[width={w}]{{{self.figure_name(path)}}}",
                rf"\caption{{{self.t(caption)}" + self.label("figure", label) + "}", r"\end{figure}"]

    def table(self, b, v):
        _, label, caption, header, rows, spec, wide = b
        begin, end = self.tabular(spec, header, rows, True)
        L = [r"\begin{table}[H]", rf"\caption{{{self.t(caption)}" + self.label("table", label) + "}", r"\footnotesize",
             begin, r"\toprule",
             " & ".join(r"\textbf{" + self.t(str(h)) + "}" for h in header) + r" \\", r"\midrule"]
        L += [" & ".join(self.t(str(c)) for c in row) + r" \\" for row in rows]
        L += [r"\bottomrule", end, r"\end{table}"]
        return L

    def after_body(self, paper, v):
        t = self.t
        L = ["", r"\vspace{6pt}", ""]
        if paper.supplementary:
            L += [rf"\supplementary{{{t(paper.supplementary)}}}", ""]
        L += [rf"\authorcontributions{{{t(paper.declaration('author_contributions'))}}}", "",
              rf"\funding{{{t(paper.declaration('funding'))}}}", "",
              rf"\institutionalreview{{{t(paper.declaration('ethics_approval'))}}}", "",
              rf"\informedconsent{{{t(paper.declaration('consent_for_publication'))}}}", "",
              rf"\dataavailability{{{t(paper.declaration('data_availability'))}}}", ""]
        if v.extra.get("journal") == "drones":
            L += [r"\durcstatement{" + t(paper.declarations.get(
                "durc", "[Author to complete: MDPI Drones requires a dual-use research of concern (DURC) statement; "
                        "see the template comment for the suggested wording.]")) + "}", ""]
        ack = self.acknowledgement_text(paper)
        L += [rf"\acknowledgments{{{ack or 'Not applicable.'}}}", "",
              rf"\conflictsofinterest{{{t(paper.declaration('competing_interests'))}}}", ""]
        app = paper.appendix_blocks()
        if app:
            L += [r"\appendixtitles{yes}", r"\appendixstart", r"\appendix"] + self.body(app, v, appendix=True)
        L += [r"\begin{adjustwidth}{-\extralength}{0cm}", r"\reftitle{References}",
              rf"\bibliography{{{self.bib_name}}}", r"\PublishersNote{}", r"\end{adjustwidth}", r"\end{document}"]
        return L
