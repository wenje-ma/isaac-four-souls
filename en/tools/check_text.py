import csv
import re

rows = list(csv.DictReader(open(r"data\cards.csv", encoding="utf-8-sig", newline="")))
print("rows", len(rows))

for slug in ("anni-greed_mode", "b-holy_dip", "b-pills_2", "aa-godhead", "b-viii_justice"):
	r = next(x for x in rows if x["slug"] == slug)
	print(slug)
	print("   effect :", r["effect"][:150])
	print("   rewards:", r["rewards"][:80])

print()
print("double space       ", sum(1 for r in rows if "  " in r["effect"]))
print("space before punct ", sum(1 for r in rows if re.search(r"\s+[.,;:]", r["effect"]))
)
print("leftover markup    ", sum(1 for r in rows if re.search(r"<|data-src|noscript|lazy", r["effect"])))
print("unresolved bracket ", sum(1 for r in rows if re.search(r"\[[^\]]+\]", r["effect"])))
print("empty effect       ", sum(1 for r in rows if not r["effect"].strip()))
print("empty rewards      ", sum(1 for r in rows if not r["rewards"].strip()))
print("hp / dice / attack ", sum(1 for r in rows if r["hp"]), sum(1 for r in rows if r["dice"]), sum(1 for r in rows if r["attack"]))
print("chars no startitem ", sum(1 for r in rows if r["kind"] == "character" and not r["starting_item"].strip()))
print("stray pipe         ", sum(1 for r in rows if "|" in r["effect"]))
print("tap glyph cards    ", sum(1 for r in rows if "↷" in r["effect"]))
print("curse glyph cards  ", sum(1 for r in rows if "☠" in r["effect"]))
print("LV cards           ", sum(1 for r in rows if re.search(r"LV\d", r["effect"])))
