"""One printable file: every deck, in the order the table plays them.

Each deck is already duplex (front, back, front, back ...), so the decks can be
concatenated page for page and the alternation survives untouched. The only
thing that must not happen is mixing two decks on one sheet: the back of a sheet
is a single printed page, and every deck prints its own name there.
"""

import os

from pypdf import PdfReader, PdfWriter

base = r"D:\wenje-ma\isaac-four-souls\en\print"
ORDER = ["character", "treasure", "monster", "loot", "room", "soul",
         "rule", "flip", "track", "token"]

out = os.path.join(base, "cards_all.pdf")
w = PdfWriter()
for name in ORDER:
  path = os.path.join(base, "cards_duplex_%s.pdf" % name)
  r = PdfReader(path)
  for page in r.pages:
    w.add_page(page)
  print("%-10s %3d pages  %2d sheets" % (name, len(r.pages), len(r.pages) // 2))

with open(out, "wb") as f:
  w.write(f)
print("total pages", len(w.pages), "sheets", len(w.pages) // 2)
print(out, round(os.path.getsize(out) / 1e6, 2), "MB")
