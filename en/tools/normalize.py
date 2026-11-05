import csv
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RAW = BASE / "data" / "raw" / "four_souls_v4_n1258.json"
OUT = BASE / "data" / "cards.csv"

STAT_NAMES = {"HP": "HP", "DC": "Dice", "ATK": "Attack"}
TYPE_KEYWORDS = [
    ("Character Card", "character"),
    ("Epic Boss", "monster"),
    ("Boss Card", "monster"),
    ("Monster Card", "monster"),
    ("Treasure Card", "treasure"),
    ("Trinket Card", "treasure"),
    ("Soul Treasure", "treasure"),
    ("Room Card", "room"),
    ("Bonus Soul", "soul"),
    ("Lost Soul", "soul"),
]


def kind_of(t):
    for key, k in TYPE_KEYWORDS:
        if key in t:
            return k
    if t.strip() == "":
        return "other"
    if re.search(r"(Cent|Bomb|Wildcard|Pill/Rune|Event|Curse|Battery|Butter Bean|Dice Shard)", t):
        return "loot"
    return "loot"


def parse_stats(s):
    out = {}
    for part in s.split("; "):
        if not part.strip():
            continue
        m = re.match(r"^(\w+):+\s*(.+)$", part.strip())
        if m:
            out[STAT_NAMES.get(m.group(1), m.group(1))] = m.group(2).strip()
    return out


ARTIST_LABELS = {
    "front_char": r"(?:Card front artist|Front character artist):",
    "front_bg": r"Front background artist:",
    "back": r"Card back artist:",
}


def label_value(display, pattern, stop_patterns, set_name):
    """Grab the text after a label, stopping at the next label or the set name."""
    m = re.search(pattern, display)
    if not m:
        return ""
    tail = display[m.end():]
    cut = len(tail)
    for stop in stop_patterns:
        mm = re.search(stop, tail)
        if mm:
            cut = min(cut, mm.start())
    mm = re.search(r"\s" + re.escape(set_name) + r"(\s|$)", tail)
    if mm:
        cut = min(cut, mm.start())
    return tail[:cut].strip()[:60]


def parse_artists(display, set_name):
    stops = [ARTIST_LABELS["front_char"], ARTIST_LABELS["front_bg"], ARTIST_LABELS["back"]]
    return (
        label_value(display, ARTIST_LABELS["front_char"], stops, set_name),
        label_value(display, ARTIST_LABELS["front_bg"], stops, set_name),
        label_value(display, ARTIST_LABELS["back"], [], set_name),
    )


data = json.load(open(RAW, encoding="utf-8-sig"))
out_rows = []

for i, r in enumerate(sorted(data, key=lambda x: (x["set"], x["type"], x["name"]))):
    stats = parse_stats(r["stats"])
    front_char, front_bg, back = parse_artists(r["display"], r["set"])
    bonus = ""
    m = re.search(r"\bCard \+(\d+)", r["display"])
    if m:
        bonus = "+" + m.group(1)
    out_rows.append({
        "n": i + 1,
        "slug": r["slug"].strip("/").replace("cards/", ""),
        "name": r["name"],
        "set": r["set"],
        "type": r["type"],
        "kind": kind_of(r["type"]),
        "hp": stats.get("HP", ""),
        "dice": stats.get("Dice", ""),
        "attack": stats.get("Attack", ""),
        "bonus": bonus,
        "effect": r["effect"],
        "rewards": r["rewards"],
        "artist_front_char": front_char,
        "artist_front_bg": front_bg,
        "artist_back": back,
        "display": r["display"],
    })

fields = list(out_rows[0].keys())
with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows(out_rows)

print("rows", len(out_rows))
print("kind:", Counter(r["kind"] for r in out_rows).most_common())
print("hp:", sum(1 for r in out_rows if r["hp"]), "\tdice:", sum(1 for r in out_rows if r["dice"]),
      "\tattack:", sum(1 for r in out_rows if r["attack"]))
print("bonus:", Counter(r["bonus"] for r in out_rows if r["bonus"]).most_common())
print("artist empty: front_char", sum(1 for r in out_rows if not r["artist_front_char"]),
      "| front_bg", sum(1 for r in out_rows if not r["artist_front_bg"]),
      "| back", sum(1 for r in out_rows if not r["artist_back"]))
print("effect empty:", sum(1 for r in out_rows if not r["effect"]))
print("rewards empty:", sum(1 for r in out_rows if not r["rewards"]))
print()
for r in out_rows[:3]:
    print({k: r[k] for k in ("n", "name", "set", "type", "kind", "hp", "dice", "attack", "effect")})
