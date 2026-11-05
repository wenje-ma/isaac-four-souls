"""Rebuild data/cards.csv from the markup-preserving scrape (scrape-html.js).

The v4 scrape stored text only, so every icon inside a card sentence vanished:
"they gain 1$" instead of "they gain 1 cent", "equal to its ." instead of
"equal to its HP". This script puts a readable token back where the icon stood,
using the src basename of the <img> tag, and keeps the existing row order and
the OCR'd starting items so the print layout does not shift.

Usage: python tools/normalize_html.py [path to four_souls_html_nNNNN.json]
"""

import csv
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DATA = BASE / "data"
CARDS = DATA / "cards.csv"
BACKUP = DATA / "cards_before_html.csv"

# icon alt -> text that reads correctly on a text-only card.
# Arial has no glyph for the die pips ❶-❻, the tap arrow or the curse skull,
# so those are spelled out; only the cent sign survives as a character.
ICONS = {
    "HP": "HP",
    "ATK": "ATK",
    "DC": "DC",
    "Tap Effect": "Tap",
    "Paid Effect": "¢",
    "Curse Effect": "Curse",
    "StevenTapIcon": "Tap",
    "Loot": "Loot",
}

# fallback by src basename, for images without alt
ICONS_BY_FILE = {
    "coin": "¢",
    "cent": "¢",
    "Heart": "HP",
    "Sword": "ATK",
    "Dice": "DC",
    "TapIcon": "↷",
    "PaidIcon": "¢",
    "CurseEffect": "☠",
}

STAT_NAMES = {"HP": "HP", "DC": "Dice", "ATK": "Attack", "Dice": "Dice", "Attack": "Attack"}
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

unknown = Counter()


def kind_of(t):
    for key, k in TYPE_KEYWORDS:
        if key in t:
            return k
    return "loot"


def icon_token(src):
    """Name of the icon behind an <img> tag, mapped to card text."""
    file = src.split("/")[-1].split("?")[0]
    file = re.sub(r"\.(png|jpe?g|svg|gif|webp)$", "", file, flags=re.I)
    file = re.sub(r"-\d+x\d+$", "", file)
    key = file.strip().lower()
    if key in ICONS:
        return ICONS[key]
    unknown[key] += 1
    return "[%s]" % file


IMG = re.compile(r"<img[^>]*>")


def icon_token(tag):
    """Text for one <img> tag: alt first, file name only as a fallback."""
    alt = re.search(r'alt="([^"]*)"', tag)
    if alt and alt.group(1).strip():
        name = alt.group(1).strip()
        if name in ICONS:
            return ICONS[name]
        m = re.match(r"LV(\d+) Effect", name)
        if m:
            return "LV" + m.group(1)
        unknown[name] += 1
        return "[%s]" % name
    src = re.search(r'src="([^"]+)"', tag)
    file = src.group(1).split("/")[-1].split("?")[0] if src else ""
    file = re.sub(r"\.(png|jpe?g|svg|gif|webp)$", "", file, flags=re.I)
    file = re.sub(r"-\d+x\d+$", "", file)
    if file in ICONS_BY_FILE:
        return ICONS_BY_FILE[file]
    unknown[file or "inline"] += 1
    return "[%s]" % (file or "icon")


def text_of(markup):
    """Turn one effect block into card text, icons included."""
    # the lazy-load markup repeats every icon inside <noscript>; drop that copy first
    s = re.sub(r"<noscript>.*?</noscript>", "", markup, flags=re.S | re.I)
    s = IMG.sub(lambda m: " %s " % icon_token(m.group(0)), s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"</?(p|div|span|td|tr)[^>]*>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\u00a0", " ")
    s = s.replace("$", "¢")
    # the site writes the die faces as dingbats and the tap icon inline as an
    # arrow; Arial draws neither, so both become words and numbers
    s = s.replace("\u21b7", "Tap")
    for cp in list(range(0x2776, 0x277C)) + list(range(0x2780, 0x278A)):
        s = s.replace(chr(cp), str(cp - (0x2775 if cp < 0x2780 else 0x277F)))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    # a leading cost marker reads better with a colon: "Tap: ..." / "Curse: ..."
    s = re.sub(r"^(Tap|Curse) (?!:)", r"\1: ", s)
    return s


def parse_stats(rows):
    out = set()
    order = []
    for r in rows:
        v = r["value"]
        out.add((r["icon"], v))
        order.append((r["icon"], v))
    return out, order


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg:
        raw_path = Path(arg)
    else:
        found = sorted((DATA / "raw").glob("four_souls_html_n*.json"), key=lambda p: p.stat().st_mtime)
        if not found:
            print("no four_souls_html_n*.json in data/raw - run scrape-html.js first")
            return
        raw_path = found[-1]

    data = json.load(open(raw_path, encoding="utf-8-sig"))
    old = {}
    if CARDS.exists():
        for r in csv.DictReader(open(CARDS, encoding="utf-8-sig", newline="")):
            old[r["slug"]] = r

    rows = []
    changed = []
    for i, r in enumerate(data):
        slug = r["slug"].strip("/").replace("cards/", "")
        stats = {}
        for row in r["stat_rows"]:
            key = STAT_NAMES.get(row["icon"], row["icon"])
            stats[key] = row["value"]
        effect = " ".join(text_of(h) for h in r["effect_html"]).strip()
        rewards = "; ".join(
            (x["value"] + (" " + ICONS.get(x["icon"], x["icon"]) if x["icon"] else "")).replace("$", "¢").strip()
            for x in r["reward_rows"]
        )
        prev = old.get(slug)
        m = re.search(r"Card \+(\d+)", r["display"] or "")
        bonus = "+" + m.group(1) if m else ""
        rows.append({
            "slug": slug,
            "name": r["name"],
            "set": r["set"],
            "type": r["type"],
            "kind": prev["kind"] if prev else kind_of(r["type"]),
            "hp": stats.get("HP", ""),
            "dice": stats.get("Dice", ""),
            "attack": stats.get("Attack", ""),
            "bonus": bonus,
            "starting_item": prev["starting_item"] if prev else "",
            "effect": effect,
            "rewards": rewards,
            "artist_front_char": prev["artist_front_char"] if prev else "",
            "artist_front_bg": prev["artist_front_bg"] if prev else "",
            "artist_back": prev["artist_back"] if prev else "",
            "display": r["display"],
        })
        if prev and prev["effect"].strip() != effect:
            changed.append((slug, prev["effect"], effect))

    # keep the old sheet order, append anything new
    order = {s: i for i, s in enumerate(old.keys())}
    rows.sort(key=lambda x: (order.get(x["slug"], 10 ** 6), x["name"]))
    for i, r in enumerate(rows):
        r["n"] = i + 1

    fields = ["n", "slug", "name", "set", "type", "kind", "hp", "dice", "attack", "bonus",
              "starting_item", "effect", "rewards", "artist_front_char", "artist_front_bg",
              "artist_back", "display"]
    if CARDS.exists() and not BACKUP.exists():
        BACKUP.write_bytes(CARDS.read_bytes())
    with open(CARDS, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows([{k: r[k] for k in fields} for r in rows])

    print("source", raw_path.name, "| cards", len(rows))
    print("kind:", Counter(r["kind"] for r in rows).most_common())
    print("effect changed:", len(changed))
    for slug, a, b in changed[:12]:
        print("  ", slug)
        print("      old:", a[:110])
        print("      new:", b[:110])
    print("cards with a hole before punctuation:",
          sum(1 for r in rows if re.search(r"\s+[.,;:]", r["effect"])))
    print("cards still using $:", sum(1 for r in rows if "$" in r["effect"]))
    print("cards with an unmapped [icon]:", sum(1 for r in rows if re.search(r"\[[^\]]+\]", r["effect"])))
    if unknown:
        print("unknown icon names:", unknown.most_common())


if __name__ == "__main__":
    main()
