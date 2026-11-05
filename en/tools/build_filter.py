"""Build the deck we actually print: drop crossovers, keep one copy per card,
fix the names that spell a game entity differently.

Reads data/cards.csv (the full 1258, never edited), writes data/cards_final.csv
with the same columns. deck/make_duplex_csv.py prints from cards_final.csv, so
the scrape and the audit tools keep working against the full table.

Three deliberate rules, all agreed with the user:

1. Crossover packages go. Warp Zone (99) is other games' characters, Mewgenics
   (4) and Dick Knots (1) are spinoff monsters. Inside Tapeworm, the two
   `Tapeworm` cards stay because `Tapeworm` is a real Isaac enemy; its four
   Proglottids and the Rainbow Tapeworm are spinoff only. Inside the Summer of
   Isaac box, `Gish`, `The Hoarder` and `The Miser` all have a wiki article, so
   only `Clubby The Seal` and `Stacy` go. The whole `Gish` and
   `The Legend of Bum-bo!` minis stay: `Gish` is an Isaac boss, `Little Gish`
   is an Isaac item, `Bumbo` is an Isaac transformation.

2. Duplicates keep the newest printing, by release order below. The reprints in
   the V2 boxes and in Requiem carry the same text as the original, so the
   choice only decides which physical card is printed once.

3. Names are corrected only where the same entity is spelled differently:
   `Parabite` vs `Para-Bite`, `Keeper Head` vs `Keeper's Head`. Card names that
   are Four Souls originals (`A Penny!`, `Steamy Sale!`, `Holy Chest`) are left
   alone even when a game item has a similar name, because those are different
   cards, not misspellings. data/name_fixes.csv holds the list.

4. Content decks keep only what the game has (user decision, 2026-11-16):
   characters are cut to the 17 playable base characters, and treasure and
   monster keep only names that match a wiki article. The four mechanic decks
   (loot, room, soul, other) are not filtered this way; a loot card is a rule,
   not a game entity.
"""

import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from match_wiki import norm, load_index

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SRC = os.path.join(BASE, "data", "cards.csv")
FIXES = os.path.join(BASE, "data", "name_fixes.csv")
OUT = os.path.join(BASE, "data", "cards_final.csv")

RANK = [
  "Requiem",
  "Summer of Isaac",
  "Challenges",
  "The Unboxing of Isaac",
  "10th Anniversary",
  "G-Fuel",
  "Promo",
  "Target",
  "Youtoob",
  "Nendoroid",
  "Retro",
  "Blank",
  "Base Game V2",
  "Four Souls+ V2",
  "Gold Box V2",
  "Alt Art",
  "Base Game",
  "Four Souls+",
  "Gold Box",
  "Gish",
  "The Legend of Bum-bo!",
  "Tapeworm",
  "Mewgenics",
  "Dick Knots",
  "Requiem Warp Zone",
]

DROP_SETS = {"Requiem Warp Zone", "Mewgenics", "Dick Knots"}
DROP_CARDS = {
  ("Tapeworm", "White Proglottid"),
  ("Tapeworm", "Pink Proglottid"),
  ("Tapeworm", "Red Proglottid"),
  ("Tapeworm", "Black Proglottid"),
  ("Tapeworm", "Rainbow Tapeworm"),
  ("Summer of Isaac", "Clubby The Seal"),
  ("Summer of Isaac", "Stacy"),
}

# The room deck is kept only where the room exists in the game, so the 33 rooms
# Four Souls invented for itself are dropped (user decision, 2026-11-16).
ROOM_KEEP = {
  "Beggar", "Black Market", "Blind Rage", "Bomb Bum", "Challenge Room", "Daily Run",
  "Devil Beggar", "Dice Room!", "Dice Room!!", "Dice Room!!!", "Dice Room!!!!",
  "Dice Room!!!!!", "Dice Room!!!!!!", "Eden’s Blessing", "Equality", "Eternal Chest",
  "Fortune Teller", "Greed Mode", "I Am Error", "Key Master", "Planetarium",
  "Restock Machine",
}


# The 17 characters the game lets you play. Tainted versions exist in the game
# but Four Souls never printed a card for them, so 34 is not reachable.
CHARACTER_KEEP = {
  "Isaac", "Maggy", "Cain", "Judas", "Blue Baby", "Eve", "Samson", "Azazel",
  "Lazarus", "Eden", "The Lost", "Lilith", "The Keeper", "Apollyon",
  "The Forgotten", "Bethany", "Jacob & Esau",
}

CONTENT_KINDS = {"character", "treasure", "monster"}

# Each deck is printed in card-name order, so a stack can be paged through
# alphabetically instead of in scrape order (user decision, 2026-11-17).
DECK_ORDER = ["character", "start", "treasure", "monster", "loot", "room", "soul"]


def rank(r):
  return RANK.index(r["set"]) if r["set"] in RANK else 99


def main():
  rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig", newline="")))
  fields = list(rows[0].keys())

  fixes = list(csv.DictReader(open(FIXES, encoding="utf-8-sig", newline="")))
  fixed = []
  for r in rows:
    for f in fixes:
      if r["name"] == f["name"] and (not f["kind"] or r["kind"] == f["kind"]):
        r["name"] = f["new"]
        fixed.append((f["name"], f["new"], r["set"]))

  kept = [r for r in rows
          if r["set"] not in DROP_SETS and (r["set"], r["name"]) not in DROP_CARDS
          and (r["kind"] != "room" or r["name"] in ROOM_KEEP)]
  dropped = len(rows) - len(kept)

  best = {}
  dupes = 0
  for r in kept:
    k = (r["name"].strip().lower(), r["kind"])
    if k not in best:
      best[k] = r
      continue
    dupes += 1
    if rank(r) < rank(best[k]):
      best[k] = r

  final = sorted(best.values(),
                 key=lambda r: (DECK_ORDER.index(r["kind"]) if r["kind"] in DECK_ORDER else 99,
                                r["name"].casefold()))

  # Rule 4: content decks keep only game entities.
  index = load_index()
  strict = []
  for r in final:
    if r["kind"] not in CONTENT_KINDS:
      strict.append(r)
    elif r["kind"] == "character":
      if r["name"] in CHARACTER_KEEP:
        strict.append(r)
    elif norm(r["name"]) in index:
      strict.append(r)
  cut = len(final) - len(strict)

  with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(strict)

  print("full %d rows -> dropped %d crossover -> %d left -> %d duplicates removed -> %d cards"
        % (len(rows), dropped, len(kept), dupes, len(final)))
  print("-> %d not in the game removed -> %d cards" % (cut, len(strict)))
  print("by kind:", dict(sorted(collections.Counter(r["kind"] for r in strict).items())))
  print("sheets:", (len(strict) + 8) // 9)
  print()
  print("renamed %d printings:" % len(fixed))
  for old, new, s in fixed:
    print("   %-24s -> %-22s %s" % (old, new, s))
  print("written", OUT)


main()
