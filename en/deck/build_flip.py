"""The one double-faced card, printed as one card with a face on each side.

Trick/Treat is a two-faced monster card: the Trick half and the Treat half
share a single physical card, so a front that carries both halves is not the
card. This builder puts the Trick half on the front sheet and the Treat half on
the back sheet, both in the centre cell of a 3 x 3 A4 page. The centre cell is
the one position a duplex flip leaves where it was, whichever edge the printer
flips on, so the two faces always land on the same piece of card after cutting.

Nothing else reads this output: the monster deck skips the card (see FLIP in
make_duplex_csv.py) and merge_duplex.py does not know the stack.
"""

import csv
import importlib.util
import os
import sys

from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")
TEX = os.path.join(BUILD, "tex")
PRINT = os.path.join(BASE, "print")
SRC = os.path.join(BASE, "data", "cards_final.csv")

NAME = "Trick/Treat"


def load(name):
  spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
  m = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(m)
  return m


def faces():
  """Split the scraped effect at the second face, keeping the labels."""
  c = load("make_duplex_csv")
  for r in csv.DictReader(open(SRC, encoding="utf-8")):
    if r["name"] != NAME:
      continue
    text = c.body(r)
    cut = text.find("Treat:")
    if cut < 0:
      sys.exit("%s has no Treat half" % NAME)
    head = {"name": c.clean(r["name"]), "subtitle": c.subtitle(r),
            "stats": c.stats(r), "footer": ""}
    front = dict(head)
    back = dict(head)
    front["body"] = text[:cut].strip()
    back["body"] = text[cut:].strip()
    return front, back
  sys.exit("%s is not in %s" % (NAME, os.path.basename(SRC)))


def sheet(r, file_stem, body_size):
  """One page with the card in the centre cell; the other cells stay empty."""
  rt = load("render_cards_tex")
  out = [rt.PREAMBLE, rt.PAGE_HEAD, rt.cut_guides()]
  rows = [{} for _ in range(9)]
  rows[4] = r
  out.append(rt.card(1, 1, r, {"body": body_size}))
  out.append(rt.PAGE_TAIL)
  out.append("\\end{document}\n")
  os.makedirs(TEX, exist_ok=True)
  path = os.path.join(TEX, file_stem + ".tex")
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(out))
  return path, rows


def render(r, file_stem):
  """Compile, shrinking the body until the text fits its own box."""
  rt = load("render_cards_tex")
  pdf = os.path.join(TEX, file_stem + ".pdf")
  for size in (10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0):
    path, rows = sheet(r, file_stem, size)
    rt.compile_tex(path)
    if not os.path.exists(pdf):
      sys.exit("compile failed for %s, see %s.log" % (file_stem, file_stem))
    if not rt.measure(pdf, rows):
      print("%-10s body %.2fpt" % (file_stem, size))
      break
  else:
    sys.exit("%s never fits" % file_stem)
  return pdf


def main():
  front, back = faces()
  os.makedirs(PRINT, exist_ok=True)
  fp = render(front, "cards_fronts_flip")
  bp = render(back, "cards_back_flip")
  w = PdfWriter()
  w.add_page(PdfReader(fp).pages[0])
  w.add_page(PdfReader(bp).pages[0])
  out = os.path.join(PRINT, "cards_duplex_flip.pdf")
  with open(out, "wb") as f:
    w.write(f)
  print("flip        sheets   1  %6.2f MB  %s" % (
    os.path.getsize(out) / 1048576, os.path.basename(out)))


if __name__ == "__main__":
  main()
