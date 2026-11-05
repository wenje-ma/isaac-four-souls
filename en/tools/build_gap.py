"""Compare the printed deck against the game's own entity lists.

Reads data/raw/isaac_wiki_categories.json (exported by hand from the wiki, see
scrape/wiki-categories.js) and data/cards_final.csv, then writes
data/game_gap.csv with one row per game entity: covered by a card or not.

entity lists used:
  Collectibles  724  items, active and passive
  Trinkets      189
  Bosses        132
  Monsters      105
  Characters     37
  Rooms          23

Matching is the same normalisation as tools/match_wiki.py: case, punctuation,
possessives, articles. A card only counts as covering an entity when the
normalised names are equal; near misses are reported separately so a spelling
difference stays visible instead of being silently forgiven.
"""

import collections
import csv
import difflib
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from match_wiki import norm, load_index

BASE = os.path.dirname(HERE)
CATS = os.path.join(BASE, "data", "raw", "isaac_wiki_categories.json")
CARDS = os.path.join(BASE, "data", "cards_final.csv")
OUT = os.path.join(BASE, "data", "game_gap.csv")

# Container pages that sit in the same category as the entities themselves.
NOISE = {
  "Bosses", "Monsters", "Items", "Challenges", "Collection Page", "Co-op",
  "All Mini-Bosses (Bosses)", "Challenge", "Characters", "Trinkets", "Rooms",
  "Pickups", "Cards", "Runes", "NPCs", "Tainted Characters",
}

# The card and the game name the same thing differently.
ALIAS = {
  "maggy": "magdalene",
  "blue baby": "???",
}

GROUPS = [
  ("item", "Collectibles"),
  ("trinket", "Trinkets"),
  ("boss", "Bosses"),
  ("monster", "Monsters"),
  ("character", "Characters"),
  ("room", "Rooms"),
]


def key(name):
  base = re.sub(r"\([^)]*\)", "", name).strip()    # `??? (Character)` -> `???`
  n = norm(base)
  if not n:                                       # `???` normalises to nothing
    return base.lower()
  return ALIAS.get(n, n)


def main():
  data = json.load(open(CATS, encoding="utf-8"))
  cats = data["categories"]
  cards = list(csv.DictReader(open(CARDS, encoding="utf-8-sig", newline="")))

  index = {}
  for c in cards:
    index.setdefault(key(c["name"]), c)
  keys = list(index)

  rows = []
  for group, cat in GROUPS:
    seen = set()
    for name in cats.get(cat, []):
      if name in NOISE or name.startswith("Chapter "):
        continue
      n = key(name)
      if not n or n in seen:
        continue
      seen.add(n)
      hit = index.get(n)
      verdict, guess = ("covered" if hit else "missing"), ""
      if not hit:
        close = difflib.get_close_matches(n, keys, n=1, cutoff=0.9)
        if close:
          guess = index[close[0]]["name"]
      rows.append({
        "group": group,
        "entity": name,
        "verdict": verdict,
        "card": hit["name"] if hit else "",
        "card_set": hit["set"] if hit else "",
        "near": guess,
      })

  with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

  print("entities %d" % len(rows))
  for group, cat in GROUPS:
    sub = [r for r in rows if r["group"] == group]
    got = sum(1 for r in sub if r["verdict"] == "covered")
    near = sum(1 for r in sub if r["near"])
    print("  %-10s %4d  covered %4d  missing %4d  near %3d"
          % (group, len(sub), got, len(sub) - got, near))
  print("written", OUT)


if __name__ == "__main__":
  main()
