"""Elsevier journals: elsarticle (classic) and the CAS templates (cas-sc / cas-dc). Both are on CTAN."""
from __future__ import annotations

from ..model import Paper
from .base import Variant, Writer


class ElsevierMixin:
    def elsevier_backmatter(self, paper: Paper) -> list[str]:
        t = self.t
        L = []
        L += [r"\section*{CRediT authorship contribution statement}", t(paper.declaration("author_contributions")), ""]
        L += [r"\section*{Declaration of competing interest}", t(paper.declaration("competing_interests")), ""]
        if paper.ai_use:
            L += [r"\section*{Declaration of generative AI and AI-assisted technologies in the writing process}",
                  t(paper.ai_use), ""]
        L += [r"\section*{Funding}", t(paper.declaration("funding")), ""]
        L += [r"\section*{Ethics statement}", t(paper.declaration("ethics_approval")), ""]
        L += [r"\section*{Data availability}", t(paper.declaration("data_availability")), ""]
        if paper.declarations.get("code_availability"):
            L += [r"\section*{Code availability}", t(paper.declarations["code_availability"]), ""]
        if paper.acknowledgements:
            L += [r"\section*{Acknowledgements}", t(paper.acknowledgements), ""]
        return L


class Elsevier(ElsevierMixin, Writer):
    key = "elsevier"
    title = "Elsevier journals (elsarticle)"
    docclass = "elsarticle"
    cite = "citep"
    variants = [
        Variant("preprint-num", "preprint,12pt", "Submission preprint, numbered references (most Elsevier journals)",
                extra={"bst": "elsarticle-num"}),
        Variant("review-num", "review,12pt", "Double-spaced review copy, numbered references",
                extra={"bst": "elsarticle-num"}),
        Variant("preprint-harv", "preprint,12pt,authoryear", "Submission preprint, author-year (Harvard) references",
                extra={"bst": "elsarticle-harv"}),
        Variant("final-1p", "final,1p,times", "Journal layout, single column (1p)", extra={"bst": "elsarticle-num"}),
        Variant("final-3p-twocolumn", "final,3p,times,twocolumn", "Journal layout, two columns (3p)", twocolumn=True,
                extra={"bst": "elsarticle-num"}),
        Variant("final-5p-twocolumn", "final,5p,times,twocolumn", "Journal layout, two columns (5p)", twocolumn=True,
                extra={"bst": "elsarticle-num"}),
    ]
    notes = ("Elsevier abstracts are limited to 250 words; highlights are 3-5 bullet points of at most 85 "
             "characters (upload them as a separate file as well). Replace the journal name in \\journal{}.")

    def preamble(self, paper, v):
        return [rf"\documentclass[{v.options}]{{elsarticle}}", r"\usepackage{graphicx}", r"\usepackage{amsmath,amssymb}",
                r"\usepackage{booktabs}", r"\usepackage{array}", r"\usepackage[hidelinks]{hyperref}", "",
                r"\journal{" + self.t(paper.extra.get("journal", "[Journal name]")) + "}", ""]

    def frontmatter(self, paper: Paper, v):
        L = [r"\begin{frontmatter}", "", rf"\title{{{self.t(paper.title)}}}", ""]
        corr = paper.corresponding
        for a in paper.authors:
            ids = ",".join(str(i) for i in a.affiliations)
            L.append(rf"\author[{ids}]{{{self.t(a.name)}" + (r"\corref{cor1}" if a is corr else "") + "}")
            if a.email:
                L.append(rf"\ead{{{a.email}}}")
        L += [r"\cortext[cor1]{Corresponding author.}", ""]
        for aff in paper.affiliations:
            fields = [("organization", ", ".join(x for x in [aff.department, aff.organization] if x)),
                      ("addressline", aff.street), ("city", aff.city), ("postcode", aff.postcode),
                      ("state", aff.state), ("country", aff.country)]
            L.append(rf"\affiliation[{aff.id}]{{" + ",\n            ".join(
                f"{k}={{{self.t(val)}}}" for k, val in fields if val) + "}")
        L += ["", r"\begin{abstract}", self.t(paper.abstract), r"\end{abstract}", ""]
        if paper.highlights:
            L += [r"\begin{highlights}"] + [r"\item " + self.t(h) for h in paper.highlights] + [r"\end{highlights}", ""]
        L += [r"\begin{keyword}", r" \sep ".join(self.t(k) for k in paper.keywords), r"\end{keyword}", "",
              r"\end{frontmatter}", ""]
        return L

    def backmatter(self, paper, v):
        return self.elsevier_backmatter(paper)

    def references(self, paper, v):
        return [rf"\bibliographystyle{{{v.extra['bst']}}}", rf"\bibliography{{{self.bib_name}}}", ""]


class ElsevierCAS(ElsevierMixin, Writer):
    key = "elsevier-cas"
    title = "Elsevier CAS templates (cas-sc / cas-dc)"
    cite = "citep"
    variants = [
        Variant("cas-sc", "a4paper,fleqn", "CAS single column (newer Elsevier journals)", extra={"cls": "cas-sc"}),
        Variant("cas-dc", "a4paper,fleqn", "CAS double column", twocolumn=True, extra={"cls": "cas-dc"}),
    ]
    notes = "Check the journal's Guide for Authors for whether it uses the CAS or the classic elsarticle template."

    def preamble(self, paper, v):
        return [rf"\documentclass[{v.options}]{{{v.extra['cls']}}}", r"\usepackage[numbers,sort&compress]{natbib}",
                r"\usepackage{booktabs}", r"\usepackage{array}", "",
                rf"\shorttitle{{{self.t(paper.short_title or paper.title)}}}",
                rf"\shortauthors{{{self.t(', '.join(a.initials + ' ' + a.surname for a in paper.authors[:3]))}}}", ""]

    def frontmatter(self, paper: Paper, v):
        L = [rf"\title [mode = title]{{{self.t(paper.title)}}}", ""]
        corr = paper.corresponding
        for a in paper.authors:
            ids = ",".join(str(i) for i in a.affiliations)
            orcid = f"[orcid={a.orcid}]" if a.orcid else ""
            L.append(rf"\author[{ids}]{{{self.t(a.name)}}}{orcid}")
            if a is corr:
                L.append(r"\cormark[1]")
            if a.email:
                L.append(rf"\ead{{{a.email}}}")
            L.append("")
        for aff in paper.affiliations:
            fields = [("organization", ", ".join(x for x in [aff.department, aff.organization] if x)),
                      ("addressline", aff.street), ("city", aff.city), ("postcode", aff.postcode),
                      ("state", aff.state), ("country", aff.country)]
            L.append(rf"\affiliation[{aff.id}]{{" + ",\n    ".join(
                f"{k}={{{self.t(val)}}}" for k, val in fields if val) + "}")
        L += ["", r"\cortext[1]{Corresponding author}", "",
              r"\begin{abstract}", self.t(paper.abstract), r"\end{abstract}", ""]
        if paper.highlights:
            L += [r"\begin{highlights}"] + [r"\item " + self.t(h) for h in paper.highlights] + [r"\end{highlights}", ""]
        L += [r"\begin{keywords}", r" \sep ".join(self.t(k) for k in paper.keywords), r"\end{keywords}", ""]
        if not any(a.orcid for a in paper.authors):
            L += [r"\renewcommand{\printorcid}{}% no ORCID iDs given: suppress the empty 'ORCID(s):' footnote", ""]
        L += [r"\maketitle", ""]
        return L

    def backmatter(self, paper, v):
        return self.elsevier_backmatter(paper)

    def references(self, paper, v):
        return [r"\bibliographystyle{cas-model2-names}", rf"\bibliography{{{self.bib_name}}}", ""]

    def support_files(self, folder):
        """cas-common.sty prints small icons from thumbnails/*.jpeg next to e-mail/URL/social links.
        Elsevier's template zip ships them; generate simple equivalents so the folder is self-contained."""
        from PIL import Image, ImageDraw

        (folder / "thumbnails").mkdir(exist_ok=True)
        for name, letter in (("email", "@"), ("url", "W"), ("facebook", "f"), ("twitter", "X"),
                             ("gplus", "g"), ("linkedin", "in")):
            img = Image.new("RGB", (64, 64), "white")
            d = ImageDraw.Draw(img)
            d.ellipse((2, 2, 62, 62), fill=(90, 90, 90))
            d.text((32, 33), letter, fill="white", anchor="mm", font_size=34)
            img.save(folder / "thumbnails" / f"cas-{name}.jpeg", quality=90)
