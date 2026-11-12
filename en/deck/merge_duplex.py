"""Interleave the per-stack front and back PDFs, one duplex file per stack.

Each stack is built twice: a deck of fronts, and a single page of nine identical
backs. The merger walks the front pages and puts that one back page after each
of them, so page 1 carries fronts, page 2 their backs, and so on.

The output stays split by stack. 586 cards is 136 pages in one file, which no
home printer likes to keep in memory as one job, and the piles are printed and
assembled one at a time anyway.
"""

import os
import sys

from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
STACKS = ["character", "treasure", "monster", "loot", "room", "soul", "rule"]
BUILD = os.path.join(HERE, "build")
PRINT = os.path.join(BASE, "print")


def main():
  test = len(sys.argv) > 1 and sys.argv[1] == "test"
  suffix = "_test" if test else ""
  total = 0
  for kind in STACKS:
    fp = os.path.join(BUILD, "cards_fronts_%s%s.pdf" % (kind, suffix))
    bp = os.path.join(BUILD, "cards_back_%s%s.pdf" % (kind, suffix))
    for p in (fp, bp):
      if not os.path.exists(p):
        sys.exit("missing %s, build it first" % p)
    fronts, backs = PdfReader(fp), PdfReader(bp)
    w = PdfWriter()
    for page in fronts.pages:
      w.add_page(page)
      w.add_page(backs.pages[0])
    out = os.path.join(PRINT, "cards_duplex_%s%s.pdf" % (kind, suffix))
    with open(out, "wb") as f:
      w.write(f)
    total += len(fronts.pages)
    print("%-10s sheets %3d  %6.2f MB  %s" % (
      kind, len(fronts.pages), os.path.getsize(out) / 1048576,
      os.path.basename(out)))
  print("done", total, "sheets")


main()
