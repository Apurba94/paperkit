"""paperkit: write a paper once, get submission-ready LaTeX for every major publisher.

Templates: IEEE, Springer Nature (all reference styles), Springer LNCS, Elsevier (elsarticle and
CAS), MDPI, ACM, Taylor & Francis and a generic arXiv preprint.
"""
from .build import build, find_tectonic
from .markdown import read_paper, write_paper
from .model import Affiliation, Author, Paper

__version__ = "0.1.0"
__all__ = ["Paper", "Author", "Affiliation", "read_paper", "write_paper", "build", "find_tectonic"]
