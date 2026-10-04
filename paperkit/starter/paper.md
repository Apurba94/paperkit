---
title: "Your Full Paper Title: Concise and Specific"
short_title: "Short Running Title"
authors:
  - given: Janin A
    surname: Apurba
    email: japurba97@gmail.com
    affiliations: [1]
    corresponding: true
    orcid: ""                       # e.g. 0000-0000-0000-0000 (leave empty if none)
  # - given: Second
  #   surname: Author
  #   email: second@example.org
  #   affiliations: [1, 2]
affiliations:
  - id: 1
    department: Department of Computer Science and Engineering
    organization: Ahsanullah University of Science and Technology
    city: Dhaka
    country: Bangladesh
  # - id: 2
  #   department: ...
  #   organization: ...
  #   city: ...
  #   country: ...
abstract: >
  One paragraph of 150-200 words (the strictest common limit: MDPI 200, Elsevier 250, IEEE 250,
  Springer 150-250). State the problem, the method, the main quantitative result and the
  conclusion. No citations, no undefined abbreviations.
abstract_long: ""                   # optional longer abstract, used only for the arXiv preprint
keywords: [keyword one, keyword two, keyword three, keyword four, keyword five]
highlights:                         # Elsevier: 3-5 bullets, each at most 85 characters
  - First key finding stated in one short line
  - Second key finding stated in one short line
  - Third key finding stated in one short line
acknowledgements: ""                # people/organisations to thank (optional)
ai_use: >
  State how generative AI was used (e.g. code, analysis, language editing), naming the tool.
  Publishers require this disclosure; paperkit places it where each publisher asks for it.
declarations:                       # leave as [Author to complete.] until you know the answer
  funding: "This research received no external funding."
  competing_interests: "The author declares no competing interests."
  ethics_approval: "[Author to complete.]"
  consent_for_publication: "[Author to complete.]"
  data_availability: "The data are available at https://github.com/Apurba94/REPOSITORY."
  materials_availability: "Not applicable."
  code_availability: "The code is available at https://github.com/Apurba94/REPOSITORY."
  author_contributions: "J.A.A.: conceptualization, methodology, software, analysis, writing."
supplementary: ""                   # describe supplementary files/videos (optional)
bibliography: references.bib
journal: "[Journal name]"           # used by the Elsevier template
acm_ccs: ["Computing methodologies~Computer vision"]   # ACM CCS concepts (https://dl.acm.org/ccs)
---

# Introduction {#sec:intro}

Explain the problem and why it matters. Cite prior work with square brackets [@redmon2016] or several
sources at once [@redmon2016; @lin2014coco]. Use **bold**, *italic*, `code` and inline math such as
$y = f(x)$. Special characters like %, & and _ are escaped automatically.

The contributions of this paper are:

- first contribution;
- second contribution;
- third contribution.

# Related Work {#sec:related}

## Subsection title

Text of the subsection. Refer to sections with @sec:method, figures with Fig. @fig:example and tables
with Table @tab:results.

# Method {#sec:method}

Display equations are written between double dollar signs and can carry a label:

$$
\hat{y} = \arg\max_{c} \; p(c \mid x)
$$ {#eq:decision}

Equation @eq:decision selects the most probable class.

![Example figure caption. Put image files in the figures/ folder. Use "wide" for figures that should
span both columns in two-column journals.](figures/example.png){#fig:example width=0.7}

# Experiments {#sec:experiments}

Table: Example results table. Columns: l = left, c = centre, r = right, X = wrapping text.
{#tab:results cols=Xrrr}
| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| Baseline | 0.80 | 0.70 | 0.75 |
| Proposed method | 0.90 | 0.85 | 0.87 |

# Discussion {#sec:discussion}

Interpret the results, compare with prior work and state limitations.

# Conclusion {#sec:conclusion}

Summarise the findings and future work.

# Appendix: Additional results {#sec:appendix}

Material that supports the paper but would interrupt the main text.
