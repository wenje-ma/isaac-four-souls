"""Merge starting_items.csv into cards.csv as a new column.

The starting item line of a character card is printed on the artwork only,
so it was read off the card images and stored separately.
"""

import csv
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
CARDS = DATA / "cards.csv"
ITEMS = DATA / "starting_items.csv"


def read_csv_any(path):
  raw = path.read_bytes()
  bom = raw[:3] == b"\xef\xbb\xbf"
  text = raw.decode("utf-8-sig")
  return list(csv.reader(text.splitlines())), bom


def main():
  rows, bom = read_csv_any(CARDS)
  head = rows[0]
  body = rows[1:]
  items, _ = read_csv_any(ITEMS)
  table = {r[0]: r[1] if len(r) > 1 else "" for r in items[1:]}

  body_slugs = [r[head.index("slug")] for r in body]
  kinds = [r[head.index("kind")] for r in body]
  chars = [s for s, k in zip(body_slugs, kinds) if k == "character"]

  missing = [s for s in chars if s not in table]
  unknown = [s for s in table if s not in body_slugs]
  print("character rows", len(chars))
  print("map entries", len(table))
  print("characters missing from map", len(missing), missing[:8])
  print("map slugs not in cards.csv", len(unknown), unknown[:8])

  extra = [s for s in body_slugs if s not in chars and s in table]
  if extra:
    print("note: map also covers non-character rows", extra)

  at = head.index("bonus") + 1
  if "starting_item" in head:
    at = head.index("starting_item")
  else:
    head.insert(at, "starting_item")
  si = head.index("slug")

  filled = 0
  for r in body:
    v = table.get(r[si], "")
    if len(r) == len(head) - 1:
      r.insert(at, "")
    r[at] = v
    if v:
      filled += 1

  bak = DATA / "cards_before_starting_item.csv"
  if not bak.exists():
    shutil.copy2(CARDS, bak)
  out = []
  for r in [head] + body:
    out.append(",".join('"' + c.replace('"', '""') + '"' for c in r))
  data = "\r\n".join(out) + "\r\n"
  CARDS.write_bytes(("\ufeff" if bom else "").encode("utf-8") + data.encode("utf-8"))
  print("written", CARDS, "rows", len(body), "filled", filled)

  empties = [r[si] for r in body if r[head.index("kind")] == "character" and not r[at]]
  print("characters with no starting item line", len(empties))
  for s in empties:
    print("  " + s)


main()
