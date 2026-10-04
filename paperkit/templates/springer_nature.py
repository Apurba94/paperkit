"""Springer Nature journals (sn-jnl class, template version 3.1, December 2024)."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer

CLASS_LINES = [
    ("referee,pdflatex,sn-basic", "referee option is meant for double line spacing"),
    ("lineno,pdflatex,sn-basic", "Basic Springer Nature Reference Style with line numbers"),
    ("pdflatex,sn-nature", "Style for submissions to Nature Portfolio journals"),
    ("pdflatex,sn-basic", "Basic Springer Nature Reference Style/Chemistry Reference Style"),
    ("pdflatex,sn-mathphys-num", "Math and Physical Sciences Numbered Reference Style"),
    ("pdflatex,sn-mathphys-ay", "Math and Physical Sciences Author Year Reference Style"),
    ("pdflatex,sn-aps", "American Physical Society (APS) Reference Style"),
    ("pdflatex,sn-vancouver-num", "Vancouver Numbered Reference Style"),
    ("pdflatex,sn-vancouver-ay", "Vancouver Author Year Reference Style"),
    ("pdflatex,sn-apa", "APA Reference Style"),
    ("pdflatex,sn-chicago", "Chicago-based Humanities Reference Style"),
]


class SpringerNature(Writer):
    key = "springer-nature"
    title = "Springer Nature journals (sn-jnl)"
    docclass = "sn-jnl"
    cite = "citep"
    bottomrule = r"\botrule"
    figure_pos = "ht"
    table_pos = "ht"
    variants = [
        Variant("mathphys-num", "pdflatex,sn-mathphys-num", "Math and Physical Sciences, numbered (template default)"),
        Variant("mathphys-ay", "pdflatex,sn-mathphys-ay", "Math and Physical Sciences, author-year"),
        Variant("basic", "pdflatex,sn-basic", "Basic Springer Nature / Chemistry reference style"),
        Variant("nature", "pdflatex,sn-nature", "Nature Portfolio journals"),
        Variant("aps", "pdflatex,sn-aps", "American Physical Society (APS) reference style"),
        Variant("vancouver-num", "pdflatex,sn-vancouver-num", "Vancouver, numbered"),
        Variant("vancouver-ay", "pdflatex,sn-vancouver-ay", "Vancouver, author-year"),
        Variant("apa", "pdflatex,sn-apa", "APA reference style"),
        Variant("chicago", "pdflatex,sn-chicago", "Chicago-based humanities reference style"),
        Variant("referee", "referee,pdflatex,sn-basic", "Double line spacing for refereeing"),
        Variant("lineno", "lineno,pdflatex,sn-basic", "Line numbers in the margin"),
    ]
    publisher_files = ["sn-jnl.cls", "bst/*.bst"]
    notes = ("Springer journals usually limit abstracts to 150-250 words. Fill in the bracketed Declarations. "
             "For Nature Portfolio (eJP) submissions paste the generated .bbl into the manuscript.")

    def preamble(self, paper, v):
        lines = []
        for opts, desc in CLASS_LINES:
            line = rf"\documentclass[{opts}]{{sn-jnl}}% {desc}"
            lines.append(line if opts == v.options else "%%" + line)
        return lines + ["",
                        r"\usepackage{graphicx}%", r"\usepackage{multirow}%", r"\usepackage{amsmath,amssymb,amsfonts}%",
                        r"\usepackage{amsthm}%", r"\usepackage{mathrsfs}%", r"\usepackage[title]{appendix}%",
                        r"\usepackage{xcolor}%", r"\usepackage{textcomp}%", r"\usepackage{manyfoot}%",
                        r"\usepackage{booktabs}%", r"\usepackage{array}%", r"\usepackage{algorithm}%",
                        r"\usepackage{algorithmicx}%", r"\usepackage{algpseudocode}%", r"\usepackage{listings}%", "",
                        r"\theoremstyle{thmstyleone}%", r"\newtheorem{theorem}{Theorem}%",
                        r"\newtheorem{proposition}[theorem]{Proposition}%", r"\theoremstyle{thmstyletwo}%",
                        r"\newtheorem{example}{Example}%", r"\newtheorem{remark}{Remark}%",
                        r"\theoremstyle{thmstylethree}%", r"\newtheorem{definition}{Definition}%", "",
                        r"\raggedbottom", ""]

    def frontmatter(self, paper: Paper, v):
        L = [rf"\title[{self.t(paper.short_title or paper.title)}]{{{self.t(paper.title)}}}", ""]
        corr = paper.corresponding
        for a in paper.authors:
            star = "*" if a is corr else ""
            ids = ",".join(str(i) for i in a.affiliations)
            L.append(rf"\author{star}[{ids}]{{\fnm{{{self.t(a.given)}}} \sur{{{self.t(a.surname)}}}}}" +
                     (rf"\email{{{a.email}}}" if a.email else ""))
        L.append("")
        corr_affs = set(corr.affiliations[:1])
        for aff in paper.affiliations:
            star = "*" if aff.id in corr_affs else ""
            addr = ", ".join(x for x in [
                rf"\street{{{self.t(aff.street)}}}" if aff.street else "",
                rf"\city{{{self.t(aff.city)}}}" if aff.city else "",
                rf"\postcode{{{self.t(aff.postcode)}}}" if aff.postcode else "",
                rf"\state{{{self.t(aff.state)}}}" if aff.state else "",
                rf"\country{{{self.t(aff.country)}}}" if aff.country else ""] if x)
            parts = [rf"\orgdiv{{{self.t(aff.department)}}}" if aff.department else "",
                     rf"\orgname{{{self.t(aff.organization)}}}" if aff.organization else "",
                     rf"\orgaddress{{{addr}}}" if addr else ""]
            L.append(rf"\affil{star}[{aff.id}]{{" + ", ".join(x for x in parts if x) + "}")
        L += ["", rf"\abstract{{{self.t(paper.abstract)}}}", "",
              rf"\keywords{{{self.t(', '.join(paper.keywords))}}}", "", r"\maketitle", ""]
        return L

    def table(self, b, v):
        L = super().table(b, v)
        # Springer: caption and label on one line, immediately followed by the tabular
        return [x for x in L if x != r"\centering"]

    def after_body(self, paper, v):
        L = ["", r"\backmatter", ""]
        if paper.supplementary:
            L += [r"\bmhead{Supplementary information}", "", self.t(paper.supplementary), ""]
        ack = self.acknowledgement_text(paper)
        if ack:
            L += [r"\bmhead{Acknowledgements}", "", ack, ""]
        L += [r"\section*{Declarations}", "", r"\begin{itemize}"]
        L += [rf"\item \textbf{{{name}:}} {self.t(text)}" for name, text in self.declarations_list(paper)]
        L += [r"\end{itemize}", ""]
        app = paper.appendix_blocks()
        if app:
            L += [r"\begin{appendices}", ""] + self.body(app, v, appendix=True) + [r"\end{appendices}", ""]
        L += [rf"\bibliography{{{self.bib_name}}}% common bib file", "", r"\end{document}"]
        return L

    def appendix_section(self, b, v):
        return rf"\section{{{self.t(b[1])}}}" + self.label("section", b[2] if len(b) > 2 else "")
