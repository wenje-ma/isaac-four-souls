"""Check every card name against the article titles of the Isaac wiki.

The wiki forbids crawlers, so the title list was exported by hand from the
user's own browser (`scrape/wiki-titles.js` -> `data/raw/isaac_wiki_titles.json`).
This matches our 1258 card names against those 3471 titles, and writes
`data/wiki_match.csv` with one row per card.

Three verdicts:
  exact  the card name is a wiki article, so the thing exists in the game
  fuzzy  no exact match, but a close title exists; the suggestion is recorded
  none   nothing close; likely a crossover or a Four Souls original

Matching is deliberately literal. Titles and card names differ in punctuation,
possessives, leading articles and trailing punctuation, so those are normalised
away before comparing; nothing else is.
"""

import csv
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
CARDS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "data", "cards.csv")
TITLES = os.path.join(BASE, "data", "raw", "isaac_wiki_titles.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "data", "wiki_match.csv")


def norm(s):
  s = (s or "").lower()
  s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u2014", "-")
  s = s.replace("&", " and ")
  s = re.sub(r"\[[^\]]*\]", " ", s)          # bracketed noise
  s = re.sub(r"\([^)]*\)", " ", s)           # parenthetical noise
  s = re.sub(r"[^a-z0-9' ]", " ", s)         # keep letters and digits only
  s = s.replace("'s ", "s ").replace("'", "")  # mom's -> moms
  s = re.sub(r"\bthe\b", " ", s)             # leading or inner article
  s = re.sub(r"\bof\b", "of", s)
  s = re.sub(r"\s+", " ", s).strip()
  return s


def load_index():
  titles = json.load(open(TITLES, encoding="utf-8"))
  index = {}
  for t in titles:
    index.setdefault(norm(t), t)
  return index


def main():
  index = load_index()
  keys = list(index)

  rows = list(csv.DictReader(open(CARDS, encoding="utf-8-sig", newline="")))

  out = []
  for r in rows:
    n = norm(r["name"])
    verdict, hit, score = "none", "", 0.0
    if n and n in index:
      verdict, hit, score = "exact", index[n], 1.0
    else:
      close = difflib.get_close_matches(n, keys, n=3, cutoff=0.8)
      if close:
        best = close[0]
        verdict = "fuzzy"
        hit = index[best]
        score = round(difflib.SequenceMatcher(None, n, best).ratio(), 2)
    out.append({
      "slug": r["slug"],
      "name": r["name"],
      "kind": r["kind"],
      "set": r["set"],
      "verdict": verdict,
      "wiki_title": hit,
      "score": score,
    })

  with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(out)

  import collections
  print("rows", len(out))
  print(collections.Counter(r["verdict"] for r in out).most_common())
  print()
  print("by kind:")
  for kind in ("character", "monster", "treasure", "loot", "room", "soul", "other"):
    c = collections.Counter(r["verdict"] for r in out if r["kind"] == kind)
    print("  %-10s %4d  %s" % (kind, sum(c.values()), dict(c)))
  print()
  print("--- exact hits, ratio per set")
  for s, n in collections.Counter((r["set"], r["verdict"]) for r in out if r["kind"] in ("character", "monster", "treasure")).most_common():
    pass
  print("--- no match, characters and monsters (the ones worth reading)")
  for r in out:
    if r["verdict"] != "exact" and r["kind"] in ("character", "monster"):
      print("  %-9s %-26s %-22s -> %s %s" % (
        r["verdict"], r["name"][:26], r["set"][:22], r["wiki_title"][:24], r["score"]))
  print()
  print("--- no match among treasure, first 60")
  shown = 0
  for r in out:
    if r["verdict"] == "none" and r["kind"] == "treasure":
      print("  %-30s %s" % (r["name"][:30], r["set"]))
      shown += 1
      if shown >= 60:
        break
  print("written", OUT)


if __name__ == "__main__":
  main()
