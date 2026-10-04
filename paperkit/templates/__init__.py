"""Registry of journal template writers."""
from .acm import ACM
from .arxiv import Preprint
from .elsevier import Elsevier, ElsevierCAS
from .ieee import IEEE
from .lncs import LNCS
from .mdpi import MDPI
from .springer_nature import SpringerNature
from .tandf import TandF

WRITERS = [IEEE(), SpringerNature(), LNCS(), Elsevier(), ElsevierCAS(), MDPI(), ACM(), TandF(), Preprint()]
BY_KEY = {w.key: w for w in WRITERS}

__all__ = ["WRITERS", "BY_KEY"]
