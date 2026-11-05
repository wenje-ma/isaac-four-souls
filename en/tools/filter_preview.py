"""Turn the wiki match into a keep/drop preview, one row per card.

Only characters, monsters and treasure are judged: loot, room, soul and the
event cards are Four Souls mechanics with no counterpart in the video game, so
they are kept whatever their name matches. Within the three judged kinds:

  exact            the name is a wiki article, the thing is in the game
  variant          a Cursed / Charmed / Holy prefix plus an in-game base name,
                   which is a Four Souls variant of a real enemy
  fuzzy            a close title, kept but flagged, because 0.9 is a weak match
  none             nothing in the wiki, so the card is either a Four Souls
                   original or a crossover

Writes data/filter_preview.csv. Adding an "x" to the keep column drops a card,
that is the only manual step.
"""

import collections
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
IN = os.path.join(BASE, "data", "wiki_match.csv")
OUT = os.path.join(BASE, "data", "filter_preview.csv")

JUDGED = ("character", "monster", "treasure")
CROSS_SETS = {"Requiem Warp Zone", "Tapeworm", "Mewgenics", "Gish", "The Legend of Bum-bo!"}
PREFIX = re.compile(r"^(cursed|charmed|holy)\s+", re.I)


def main():
  rows = list(csv.DictReader(open(IN, encoding="utf-8-sig", newline="")))
  index = {r["name"].strip().lower(): r for r in rows}

  def base_hit(name):
    # "Cursed Gaper" -> "Gaper"; a hit there means the enemy is a real one
    stripped = PREFIX.sub("", name)
    if stripped == name:
      return ""
    for r in rows:
      if r["name"].strip().lower() == stripped.lower() and r["verdict"] == "exact":
        return r["name"]
    return ""

  out = []
  for r in rows:
    keep, reason = "y", ""
    if r["kind"] not in JUDGED:
      reason = "mechanic card, kept as a whole"
    elif r["verdict"] == "exact":
      reason = "in the game"
    elif base_hit(r["name"]):
      reason = "variant of " + base_hit(r["name"])
    elif r["verdict"] == "fuzzy" and float(r["score"]) >= 0.9:
      keep, reason = "y", "close to " + r["wiki_title"] + " (check)"
    else:
      keep, reason = "n", "not in the game" + (" / crossover set" if r["set"] in CROSS_SETS else "")
    out.append({
      "slug": r["slug"],
      "name": r["name"],
      "kind": r["kind"],
      "set": r["set"],
      "match": r["verdict"],
      "wiki_title": r["wiki_title"],
      "score": r["score"],
      "keep": keep,
      "reason": reason,
    })

  with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(out)

  drops = [r for r in out if r["keep"] == "n"]
  print("cards", len(out), "kept", len(out) - len(drops), "dropped", len(drops))
  print()
  print("dropped by kind:", dict(collections.Counter(r["kind"] for r in drops)))
  print("dropped by set:")
  for s, n in collections.Counter(r["set"] for r in drops).most_common():
    print("   %-24s %3d" % (s, n))
  print()
  print("all dropped cards:")
  for r in sorted(drops, key=lambda x: (x["kind"], x["set"], x["name"])):
    print("   %-10s %-28s %s" % (r["kind"], r["name"][:28], r["set"]))
  print()
  print("flagged for a look (close title, kept):")
  for r in out:
    if "(check)" in r["reason"]:
      print("   %-26s -> %-24s %s" % (r["name"][:26], r["wiki_title"][:24], r["score"]))
  print("written", OUT)


main()
