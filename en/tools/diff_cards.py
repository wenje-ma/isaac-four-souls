"""Compare two card sheets field by field.

Used to prove what the re-scrape changed: python tools/diff_cards.py OLD.csv NEW.csv
"""

import csv
import sys

A = sys.argv[1] if len(sys.argv) > 1 else r"data\cards_before_html.csv"
B = sys.argv[2] if len(sys.argv) > 2 else r"data\cards.csv"

FIELDS = ["name", "set", "type", "kind", "hp", "dice", "attack", "bonus",
          "starting_item", "effect", "rewards", "artist_front_char",
          "artist_front_bg", "artist_back"]

a = {r["slug"]: r for r in csv.DictReader(open(A, encoding="utf-8-sig", newline=""))}
b = {r["slug"]: r for r in csv.DictReader(open(B, encoding="utf-8-sig", newline=""))}

print("cards old/new:", len(a), len(b))
print("only in old:", len(set(a) - set(b)), "| only in new:", len(set(b) - set(a)))

for f in FIELDS:
	changed = [s for s in a if s in b and (a[s][f] or "").strip() != (b[s][f] or "").strip()]
	print("%-18s %4d changed" % (f, len(changed)))
	for s in changed[:3]:
		print("     ", s)
		print("        old:", (a[s][f] or "")[:100])
		print("        new:", (b[s][f] or "")[:100])
