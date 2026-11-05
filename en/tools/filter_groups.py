"""Split the 169 drop candidates into the ones that come from a crossover
package and the ones that are Four Souls originals, then report card counts
for the combinations the user may pick.
"""

import collections
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
IN = os.path.join(BASE, "data", "filter_preview.csv")

CROSS_SETS = {"Requiem Warp Zone", "Tapeworm", "Mewgenics", "Gish", "The Legend of Bum-bo!"}
SOI_CROSS = {"Clubby The Seal", "Stacy"}

rows = list(csv.DictReader(open(IN, encoding="utf-8-sig", newline="")))


def is_cross(r):
  return r["set"] in CROSS_SETS or (r["set"] == "Summer of Isaac" and r["name"] in SOI_CROSS)


drops = [r for r in rows if r["keep"] == "n"]
group_a = [r for r in drops if is_cross(r)]
group_b = [r for r in drops if not is_cross(r)]

print("drops total", len(drops), "| crossover package", len(group_a), "| Four Souls original", len(group_b))
print()
print("A, crossover package:")
for r in sorted(group_a, key=lambda x: (x["set"], x["kind"], x["name"])):
  print("   %-10s %-28s %s" % (r["kind"], r["name"][:28], r["set"]))
print()
print("B, everything else that has no wiki page:")
for r in sorted(group_b, key=lambda x: (x["set"], x["kind"], x["name"])):
  print("   %-10s %-28s %s" % (r["kind"], r["name"][:28], r["set"]))
print()

PRIO = ["Requiem", "Base Game V2", "Four Souls+ V2", "Gold Box V2", "Promo", "10th Anniversary",
        "Target", "Retro", "Blank", "Dick Knots", "Summer of Isaac", "Alt Art",
        "Base Game", "Four Souls+", "Gold Box", "The Unboxing of Isaac", "Challenges"]


def prio(r):
  return PRIO.index(r["set"]) if r["set"] in PRIO else 99


def dedupe(rs):
  best = {}
  for r in rs:
    k = (r["name"].strip().lower(), r["kind"])
    if k not in best or prio(r) < prio(best[k]):
      best[k] = r
  return list(best.values())


def sheets(n):
  return (n + 8) // 9


for label, rs in (
  ("keep all", rows),
  ("drop A only", [r for r in rows if not is_cross(r)]),
  ("drop A+B", [r for r in rows if not (r["keep"] == "n")]),
):
  d = dedupe(rs)
  print("%-12s %4d cards, deduped %4d, %3d sheets" % (label, len(rs), len(d), sheets(len(d))))
  print("             by kind:", dict(collections.Counter(r["kind"] for r in d)))
