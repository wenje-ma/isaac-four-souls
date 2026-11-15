"""Assemble cn/data/translations.csv from the hand-written per-deck sources.

The pilot (loot + room) lives in translations.csv itself and stays there; every
larger deck is kept as a flat `slug|text` file under cn/data/zh/ so it can be
edited with an ordinary text editor and diffed line by line. `\n` in those files
is a literal two-character escape: the renderer splits keyword lines on a real
newline, so the escape is expanded here, once.

Punctuation is normalised here through build_cn.punct(), so the source files can
be typed with whatever comes out of the keyboard and the CSV always ends up
half-width with English spacing (STYLE 48-59). Files are written QUOTE_ALL: the
commas punct() inserts would otherwise split a field for any reader that opens
the CSV by hand.
"""

import csv, importlib.util, io, os, sys

CN = r"D:\wenje-ma\isaac-four-souls\cn"
DECK = r"D:\wenje-ma\isaac-four-souls\en\deck"
ZH = os.path.join(CN, "data", "zh")
OUT = os.path.join(CN, "data", "translations.csv")

SOURCES = ["monster.txt", "treasure.txt", "rule_soul_char.txt", "flip.txt"]

# The order the printed book uses: the stacks in the order merge_all / merge_cn
# concatenate them, then the flip sheet. A translator looking a card up in the
# CSV follows the same path as a player flipping through the PDF.
PAGE_ORDER = ["character", "treasure", "monster", "loot", "room", "soul",
              "rule", "flip"]


def punct():
  spec = importlib.util.spec_from_file_location("build_cn",
                                                os.path.join(CN, "deck", "build_cn.py"))
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  return mod.punct


def read_zh(path):
  """slug|text, `\\n` expanded to a real newline. Later lines win on a duplicate."""
  rows = []
  with io.open(path, encoding="utf-8") as f:
    for line in f:
      line = line.rstrip("\n")
      if not line.strip():
        continue
      slug, text = line.split("|", 1)
      rows.append((slug.strip(), text.replace("\\n", "\n").strip()))
  return rows


def pdf_order():
  """slug -> rank, in the order the assembled PDF prints the cards.

  Read from the fronts CSVs rather than from cards_final.csv: those are what the
  renderer actually lays out, stack by stack, and they are already trimmed to
  the cards a stack prints.
  """
  rank = {}
  for stack in PAGE_ORDER:
    if stack == "flip":
      # the flip card is printed straight from cards_final, not via a stack CSV
      src = os.path.join(DECK, "..", "data", "cards_final.csv")
      for r in csv.DictReader(io.open(src, encoding="utf-8")):
        if r["name"] == "Trick/Treat":
          rank.setdefault(r["slug"], len(rank))
      continue
    path = os.path.join(DECK, "cards_fronts_%s.csv" % stack)
    if not os.path.exists(path):
      continue
    for r in csv.DictReader(io.open(path, encoding="utf-8")):
      rank.setdefault(r["slug"], len(rank))
  return rank


def main():
  fix = punct()
  rows = []
  with io.open(OUT, encoding="utf-8") as f:
    rows = [(r["slug"], r["effect_cn"]) for r in csv.DictReader(f)]
  seen = {s for s, _ in rows}
  added = 0
  for name in SOURCES:
    path = os.path.join(ZH, name)
    if not os.path.exists(path):
      continue
    for slug, text in read_zh(path):
      if slug in seen:
        continue
      seen.add(slug)
      rows.append((slug, text))
      added += 1

  bodies = {r["slug"] for r in csv.DictReader(
      io.open(os.path.join(CN, "..", "en", "data", "cards_final.csv"),
              encoding="utf-8")) if r["effect"].strip()}
  missing = sorted(s for s in bodies if s not in seen)

  # sort into the printed order; a slug the book does not print keeps its
  # position relative to the others, at the end.
  rank = pdf_order()
  rows.sort(key=lambda r: rank.get(r[0], len(rank)))

  with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writerow(["slug", "effect_cn"])
    for slug, text in rows:
      w.writerow([slug, fix(text)])

  print("rows %d (+%d), cards with a body %d, untranslated %d" % (len(rows), added, len(bodies), len(missing)))
  if missing:
    print("missing:", ", ".join(missing))


if __name__ == "__main__":
  main()
