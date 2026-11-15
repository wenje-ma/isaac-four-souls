"""The seven Chinese decks, each as its own printable duplex file.

These are the per-deck sheets, for printing one pile at a time. The combined
book (`cards_all_cn.pdf`) is built by `impose_all.py` instead, but both call the
same importer, so a pile's last sheet carries exactly as many backs as it has
cards -- never nine backs behind four cards.
"""

import csv
import io
import os

import impose_all as ia

DECKS = ["cncharacter", "cntreasure", "cnmonster", "cnloot", "cnroom",
         "cnsoul", "cnrule"]


def count_of(stack):
  path = os.path.join(ia.CN, "..", "en", "deck", "cards_fronts_%s.csv" % stack)
  with io.open(path, encoding="utf-8", newline="") as f:
    return len(list(csv.DictReader(f)))


def main():
  os.makedirs(ia.PRINT, exist_ok=True)
  for stack in DECKS:
    cards = ia.deck_cards(
        os.path.join(ia.BUILD, "cards_fronts_%s.pdf" % stack),
        os.path.join(ia.BUILD, "cards_back_%s.pdf" % stack),
        count_of(stack))
    ia.impose(cards, os.path.join(ia.PRINT, "cards_duplex_%s.pdf" % stack),
              stack)


if __name__ == "__main__":
  main()
