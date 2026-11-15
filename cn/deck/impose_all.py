"""Impose every deck into printable duplex sheets, one card at a time.

Two decks print whole sheets at a time and two do not, so the book is built
card by card rather than sheet by sheet: each card's face is cut out of whatever
sheet it happens to sit on and its back is cut out of the back sheet that faces
it. That is what keeps the last sheet honest -- if only four cards are left,
only four backs are printed, instead of a nine cell sheet where five cells
carry a pile name with no card in front of it.

The same function prints the seven decks on their own (`merge_cn.py`) and the
one combined book (`cards_all_cn.pdf`), so both come out of one rule.
"""

import os

import pymupdf

CN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(CN, "..", "en", "deck", "build")
PRINT = os.path.join(CN, "print")
EN_PRINT = os.path.join(CN, "..", "en", "print")

MM = 72.0 / 25.4
CARD_W, CARD_H = 63.5, 88.9
PER_COL, PER_ROW = 3, 3
PAGE_W, PAGE_H = 210.0, 297.0
X0 = (PAGE_W - CARD_W * PER_COL) / 2.0
Y0 = (PAGE_H - CARD_H * PER_ROW) / 2.0
PAD = 0.08  # points of bleed on each side, so the 0.2 pt trim line survives
SLOTS = PER_COL * PER_ROW


def cell(slot, pad=0.0):
  """The square one card occupies, in points, from the page's top left corner."""
  r, c = divmod(slot, PER_COL)
  x = X0 + CARD_W * c
  y = Y0 + CARD_H * r
  return pymupdf.Rect((x - pad) * MM, (y - pad) * MM,
                      (x + CARD_W + pad) * MM, (y + CARD_H + pad) * MM)


def deck_cards(front_path, back_path, count):
  """One entry per card: (front doc, front page, back doc, back page, slot).

  A deck whose back is a single repeated sheet reuses page 0; the combined
  deck has one back page per front page, so the pages pair up 1:1.
  """
  front = pymupdf.open(front_path)
  back = pymupdf.open(back_path)
  nb = back.page_count
  cards = []
  for j in range(count):
    page, slot = divmod(j, SLOTS)
    cards.append((front, page, back, page if nb > page else 0, slot))
  return cards


def impose(cards, target, label=""):
  """Write the cards as duplex sheets: face, then the back of the same card."""
  sheets = (len(cards) + SLOTS - 1) // SLOTS
  out = pymupdf.open()
  for s in range(sheets):
    for side in (0, 1):
      page = out.new_page(width=PAGE_W * MM, height=PAGE_H * MM)
      for i in range(SLOTS):
        idx = s * SLOTS + i
        if idx >= len(cards):
          break
        front, fpage, back, bpage, slot = cards[idx]
        src, pno = (front, fpage) if side == 0 else (back, bpage)
        page.show_pdf_page(cell(i, PAD), src, pno, clip=cell(slot, PAD))
  out.save(target, garbage=4, deflate=True)
  print("%-12s %3d cards -> %d pages / %d sheets  %5.2f MB  %s" % (
    label, len(cards), out.page_count, sheets,
    os.path.getsize(target) / 1048576, os.path.basename(target)))
  return out.page_count


def all_cards():
  """Every card of the set, in print order, as separate one-deck runs."""
  cards = deck_cards(os.path.join(BUILD, "cards_fronts_cnall.pdf"),
                     os.path.join(BUILD, "cards_back_cnall.pdf"), 571)
  # the flip card is one card with two faces, printed centred on its own sheet
  flip = pymupdf.open(os.path.join(PRINT, "cards_duplex_cnflip.pdf"))
  cards.append((flip, 0, flip, 1, 4))
  # nine track cards, same face on every sheet
  track = pymupdf.open(os.path.join(PRINT, "cards_duplex_cntrack.pdf"))
  for j in range(9):
    cards.append((track, 0, track, 1, j))
  # 158 coins and hearts, already paired page to page by the token builder
  token = pymupdf.open(os.path.join(EN_PRINT, "cards_duplex_token.pdf"))
  for j in range(158):
    page, slot = divmod(j, SLOTS)
    cards.append((token, 2 * page, token, 2 * page + 1, slot))
  return cards


def main():
  cards = all_cards()
  impose(cards, os.path.join(PRINT, "cards_all_cn.pdf"), "ALL")


if __name__ == "__main__":
  main()
