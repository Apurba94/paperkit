# paperkit

**Write a research paper once — get submission-ready LaTeX for every major publisher.**

You write the paper as plain Markdown (`paper.md`) with a BibTeX file and a `figures/` folder. paperkit
renders it into the official LaTeX templates of IEEE, Springer Nature, Springer LNCS, Elsevier, MDPI, ACM,
Taylor & Francis and arXiv. It checks every output and, if Tectonic is installed, compiles every variant to
PDF to prove it works. Text, numbers and references are identical in every format, so you can submit the
same paper anywhere and re-target it after a rejection in minutes.

| Publisher | Template | Variants |
|---|---|---|
| IEEE | `IEEEtran` | conference, journal (Transactions), single-column review copy |
| Springer Nature journals | `sn-jnl` (v3.1, Dec 2024) | all 9 reference styles + referee (double-spaced) + line numbers |
| Springer proceedings | `llncs` | LNCS / CCIS / LNAI |
| Elsevier | `elsarticle` | preprint & review (numbered), preprint (author-year), 1p, 3p and 5p journal layouts |
| Elsevier (newer journals) | `cas-sc` / `cas-dc` | single and double column |
| MDPI | `mdpi.cls` (official) | Drones, Remote Sensing, Sensors, Applied Sciences, Electronics, J. Imaging, AI, Computers, Information, BDCC (any MDPI journal by changing one option) |
| ACM | `acmart` | sigconf, acmsmall (journals), anonymous review manuscript |
| Taylor & Francis | `interact` | Interact layout, NLM references |
| Preprint | `article` | arXiv / TechRxiv / SSRN (standard packages only) |

Each publisher's back matter is mapped to what that publisher asks for: Springer *Declarations*, Elsevier
*CRediT* + *competing interest* + *generative-AI* statements and highlights, MDPI's statement commands
(including the DURC statement for *Drones*), the IEEE/ACM acknowledgement with AI disclosure, and the T&F
disclosure, funding and data statements.

## Quick start

```bash
pip install git+https://github.com/Apurba94/paperkit        # or: pip install -e path/to/paperkit
python -m paperkit new my-paper                               # creates paper.md, references.bib, figures/
# ... write the paper in my-paper/paper.md ...
python -m paperkit fetch                                      # once: Springer Nature + MDPI class files
python -m paperkit build my-paper --compile --zip             # -> my-paper/journals/
```

Open `my-paper/journals/README.md` to see every variant with its compile status, then upload the folder (or
its zip) for your target journal to Overleaf or compile it locally.

## Writing `paper.md`

The YAML header holds the metadata (title, authors with affiliations/ORCID/e-mail, abstract, keywords,
Elsevier highlights, generative-AI disclosure and the declarations). The body is Markdown:

| Element | Syntax |
|---|---|
| Section / subsection / subsubsection | `# Title {#sec:label}`, `##`, `###` |
| Appendix | `# Appendix: Title {#sec:appA}` |
| Citation | `[@key]`, `[@key1; @key2]` |
| Cross reference | `@fig:label`, `@tab:label`, `@eq:label`, `@sec:label` |
| Emphasis, code, math | `**bold**`, `*italic*`, `` `code` ``, `$x^2$` |
| Display equation | `$$ ... $$ {#eq:label}` |
| Figure | `![Caption.](figures/file.png){#fig:label width=0.7}` (add `wide` to span two columns) |
| Table | `Table: Caption. {#tab:label cols=Xrrr wide}` followed by a pipe table (`X` = wrapping column) |
| Lists | `- item`, `1. item` |

See [`paperkit/starter/paper.md`](paperkit/starter/paper.md) for a complete example.
Unknown declarations should stay `[Author to complete.]`; paperkit lists them in the build README so
nothing is submitted with a placeholder by accident.

## Publisher class files

IEEE, Springer LNCS, Elsevier, ACM and the arXiv template use classes that ship with every TeX distribution
and with Overleaf. Springer Nature, MDPI and Taylor & Francis distribute their classes as downloads;
`python -m paperkit fetch` downloads the Springer Nature and MDPI packages from the publishers into
`~/.paperkit/publishers/`. Taylor & Francis protects its site with a bot check, so download the template zip
from your journal's *Instructions for authors* page and run
`python -m paperkit import-files taylor-francis interact.zip`. These files are copied next to the generated
`.tex` files but are never committed to your repositories.

## Compile testing

With [Tectonic](https://tectonic-typesetting.github.io) installed (on `PATH`, at
`~/.paperkit/bin/tectonic(.exe)`, or via `PAPERKIT_TECTONIC`), `--compile` compiles every variant (BibTeX
included) and reports page counts, undefined citations/references and overfull lines. Tectonic uses the
XeTeX engine; journals compile with pdfLaTeX, which these ASCII-only sources also support.

## Python API

```python
from paperkit import read_paper, build
paper = read_paper("my-paper")
build(paper, "my-paper/journals", only=["mdpi", "elsevier"], compile=True)
```

Projects that generate their paper programmatically (e.g. numbers computed from experiment results) can
construct `paperkit.Paper` directly; see `paperkit/model.py` for the block types.

## License

MIT. Publisher templates remain the property of their publishers.
