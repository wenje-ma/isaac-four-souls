"""Prepare the two CSV files the duplex print needs, one stack at a time.

nanDECK's `1-{(field)}` is not a filter: it resolves to the highest card number
that has a value in that column, so a literal string or a LINE drawn under that
range lands on every card up to it, fronts included. Backs are therefore built
in their own deck, where every card is a back, and merge_duplex.py interleaves
the finished pages.

Each stack gets:
  cards_fronts_<kind>.csv  the card fronts, one page of nine at a time
  cards_back_<kind>.csv    nine identical backs, a single page

Run without an argument for all stacks, or with "test" for a four page sample.
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
# the printed deck: crossovers dropped, one copy per card, names corrected by
# tools/build_filter.py. data/cards.csv stays the untouched full table.
SRC = os.path.join(BASE, "data", "cards_final.csv")

STACKS = [
  ("character", "CHARACTER"),
  ("treasure", "TREASURE"),
  ("monster", "MONSTER"),
  ("loot", "LOOT"),
  ("room", "ROOM"),
  ("soul", "SOUL"),
]

PER_PAGE = 9
# 规则书明说 "The Lost Soul is a loot card that can become a soul when played":
# 它的 kind 按卡名被归成了 soul, 但它住在 loot 牌堆里, 印的也是自己的类型行.
PILE = {"p-lost_soul": "loot"}
SUBTITLE_FIX = {"p-lost_soul": "Lost Soul Card"}


def pile(r):
  return PILE.get(r["slug"], r["kind"])
# Cards that carry a face on each side. They are left out of their deck here
# because a deck's back is the deck name, and printed by build_flip.py instead.
FLIP = {"Trick/Treat"}
# The type line printed on every card of a deck; see subtitle().
SUBTITLE = {
  "character": "Character Card",
  "start": "Starting Item",
  "treasure": "Treasure Card",
  "monster": "Monster Card",
  "loot": "Loot Card",
  "room": "Room Card",
  "soul": "Soul Card",
}
FRONT_COLS = ["n", "name", "subtitle", "stats", "body", "footer", "set", "slug"]
BACK_COLS = FRONT_COLS + ["back"]


def smart_quotes(s):
  """A quoted phrase gets real quotation marks, not six apostrophes.

  The scrape quotes the words a card cares about — `with "Bomb" in its name`,
  `has "Tap: ..."` — and the card is read aloud, so a straight quote that prints
  as an apostrophe changes the meaning. Straight quotes are turned pairwise
  into the typographic pair; anything already curly is left alone.
  """
  out, opening = [], True
  for ch in s:
    if ch == '"':
      out.append("\u201c" if opening else "\u201d")
      opening = not opening
    else:
      out.append(ch)
  return "".join(out)


def clean(s):
  s = smart_quotes(s or "")
  s = s.replace("’", "'")
  # `clean()` runs on every field twice (body and the row), so it must keep an
  # intentional line break — a stat badge above its ability — instead of
  # flattening it into the space this next step collapses. The break is parked
  # on a NUL while every regex here runs, then handed back.
  s = s.replace("\r", "").replace("\n", "\x00")
  s = re.sub(r"\s+", " ", s).strip()
  s = re.sub(r"\.(\d+:)", r". \1", s)
  s = re.sub(r"(Roll-)(\d+)", r"\1 \2", s)
  # The site writes an em dash as a bare hyphen after words too, not only after
  # `Roll` or `Choose one`: `roll 3x instead- 1-4: ...` is a dash introducing a
  # result table. The assertion keeps this idempotent when an earlier step
  # already wrote the dash.
  s = re.sub(r"(?i)\binstead-(\s+)", r"instead ---\1", s)
  # U+2014 does not survive xeCJK: the engine files the em dash with CJK
  # punctuation and eats the space after it, so `instead — 1-4:` came out as
  # `instead —1-4:`. TeX's own `---` stays Latin and keeps its space.
  s = s.replace("\u2014", "---")
  # The site spells money out when it is a variable: `lose x cents`. The card
  # face always uses the coin sign, so the word goes the same way as `Lose 4c.`
  # (user decision, 2026-11-17).
  s = re.sub(r"(?i)\b(x|\d+)\s+cents?\b", lambda m: m.group(1) + "\u00a2", s)
  # A bullet is only an option break, and the deck writes every option list with
  # ` / `: the dot goes, the choice keeps its em dash, and nothing is left to
  # suggest a second kind of list (user decision, 2026-11-17).
  # both dot shapes the site uses for an option: the round bullet, and the
  # middle dot that Isaac's Last Will carries
  s = re.sub(r"\s*[\u2022\u00b7]\s*", " / ", s)
  # the choice label itself is left alone: the renderer already turns `Choose
  # one:` into `Choose one ---`, and writing the dash here would hand it a dash
  # run to shorten again. Only the separator the bullet left behind goes.
  s = re.sub(r"(?i)(Choose\s*(?:one|\d+))\s*[-:]\s*/\s*", r"\1: ", s)
  s = re.sub(r"\s*/\s*/\s*", " / ", s)
  return s.replace("\x00", "\n")


def stats(r):
  parts = []
  if r["hp"]:
    parts.append("HP " + r["hp"])
  if r["dice"]:
    # the face prints the abbreviation, not the long word: the stat is the
    # number a monster is hit on, and the rule deck spells out that dc stands
    # for dice (user decision, 2026-11-16)
    parts.append("DC " + r["dice"])
  if r["attack"]:
    parts.append("ATK " + r["attack"])
  return " / ".join(parts)


def subtitle(r):
  if r["slug"] in SUBTITLE_FIX:
    return SUBTITLE_FIX[r["slug"]]
  # One type line per deck. The site splits every deck into a dozen subtypes —
  # Passive/Active/Eternal/One-Use/Paid treasure, Basic/Boss/Epic monster, Good
  # and Bad Event, Bonus Soul, and more — and none of those lines says anything
  # a player can act on: the card's own text already shows whether it taps,
  # whether it is a boss, what it pays out. The deck a card lives in is the only
  # useful label, so the whole deck shares one type line, the way every
  # character card shares "Character Card" (user decision, 2026-11-17).
  if r["kind"] == "loot":
    return "Loot Card"
  if r["kind"] in SUBTITLE:
    return SUBTITLE[r["kind"]]
  if r["type"]:
    return r["type"]
  return "Blank Card" if r["kind"] == "other" else r["kind"].capitalize()


def body(r):
  """The effect, with the corner bonus folded back into its HP/ATK head.

  The scrape puts the badge number in `bonus` and the icon in `effect`, so
  Breakfast reads `bonus=+1, effect=HP`; the card has to read `+1 HP`.
  """
  text = clean(r["effect"])
  b = (r["bonus"] or "").strip().lstrip("+")
  if b and not text.startswith("+"):
    head = text.split(" ", 1)
    if head[0] in ("HP", "ATK"):
      rest = head[1].strip() if len(head) > 1 else ""
      # the badge number is an always-on stat and the rest is the ability: two
      # lines on the printed card, and a slash would read as a choice between
      # them. A newline is the one marker the renderer keeps as a line break.
      text = "+" + b + " " + head[0] + ("\n" + rest if rest else "")
  # a few cards keep the badge number in the effect as well (`+1 ATK Each
  # time...`): the badge and the ability are two lines, not one run-on
  m = re.match(r"(?:\+\d+\s+(?:HP|ATK))\s+(\S.*)$", text)
  if m:
    text = text[:m.start(1)].rstrip() + "\n" + m.group(1)
  return re.sub(r"\s*/\s*/\s*", " / ", text)


SOUL = re.compile(r"^(\d+)x Soul$")


COUNT = re.compile(r"^(\d+)x (Coin|Loot|Treasure|Soul)$")


def reward_text(s):
  # A reward is a quantity of something, not a multiplier: the site writes a
  # dime as `x10 Coin`, which reads as "ten times your coins". Counts print as
  # `+10 Coin`, the shape a soul badge already uses, `Soul +2`.
  # A roll table written as `1x Coin; 2x Loot; ...` is not a count list, and is
  # left exactly as it came.
  parts = [re.sub(r"^x(\d+)\s+", r"\1x ", p) for p in s.split("; ")]
  # a reward that is conditional on a roll carries the same label as the body
  # roll tables, and the label takes the em dash, not the site's hyphen. It is
  # spelled `---` so xeCJK treats it as a Latin dash and keeps the space after
  # it; a literal U+2014 counts as CJK punctuation there and swallows that space.
  parts = [re.sub(r"(?i)\bRoll\s*[-:]", "Roll ---", p) for p in parts]
  # the site leaves the roll value as a bare `x` and spells the payout as a word:
  # `Gain x Coin`, `Loot x Loot`, `Gain x Loot`. The faces read `x\u00a2`, `Loot x`
  # and `Loot x`, so the placeholder never reaches print as a noun.
  parts = [re.sub(r"(?i)Gain x Coin", "Gain x\u00a2", p) for p in parts]
  parts = [re.sub(r"(?i)Loot x Loot", "Loot x", p) for p in parts]
  parts = [re.sub(r"(?i)Gain x Loot", "Loot x", p) for p in parts]
  parts = [re.sub(r"(?i)1\u00a2 Coin", "1\u00a2", p) for p in parts]
  out = []
  for p in parts:
    m = COUNT.match(p)
    if not m:
      # a mixed list such as `1x Soul; Roll- Gain x Coin` keeps its roll entry
      # as written, but the counts around it still print in the face's shape
      out.append(p)
      continue
    n, unit = m.group(1), m.group(2)
    if unit == "Soul":
      out.append("+" + n + " Soul")
    elif unit == "Coin":
      # the word never appears on a card face: money is the cent glyph, in the
      # body and in a reward alike, so `+4 Coin` prints as `+4c`
      out.append("+" + n + "\u00a2")
    else:
      out.append("+" + n + " " + unit)
  # every entry in a reward box is gained at once — the rules say the active
  # player "gains any rewards detailed in the reward box" — so a list is a
  # conjunction, not a choice, and joins with `&`
  return " & ".join(out)


MINOR = {"of", "the", "a", "an", "and", "in", "on", "to", "for", "with"}


def title_case(s):
  # the item names arrive in the site's block caps; treasure names print as
  # `Yum Heart`, so the starting item reads the same way. Digits survive, which
  # keeps `The D6` intact. A small word after the first stays lowercase, so it
  # is `Sleight of Hand`, not `Sleight Of Hand`.
  out = []
  for i, w in enumerate(s.split()):
    low = w.lower()
    if i and low in MINOR:
      out.append(low)
    else:
      out.append(w[:1].upper() + w[1:].lower())
  return " ".join(out)


def footer(r):
  if r["starting_item"]:
    return "STARTING ITEM: " + title_case(r["starting_item"])
  # A reward box belongs to a monster you can kill. A card with no HP, dice or
  # attack is an event: it resolves on its own and says in its own words what
  # the players get, so a REWARD line would only repeat it. The rule is the
  # stats test rather than a reading of the prose, because every card here that
  # carries a stat does need the line and every statless one already pays out in
  # text (Angel Room, Secret Room!, I Am Error!, Double Treasure!, Spiked Chest,
  # Betrayal!, Devil Deal, Holy Chest, Hot Potato!, Keeper's Resting Place,
  # Lust For Blood!) -- user decision, 2026-11-16.
  if r["kind"] != "monster":
    return ""
  if not (r["hp"].strip() or r["dice"].strip() or r["attack"].strip()):
    return ""
  if r["rewards"]:
    return "REWARD: " + reward_text(r["rewards"])
  return ""


def front_row(r):
  return [
    r["n"],
    clean(r["name"]).replace("|", "/"),
    clean(subtitle(r)).replace("|", "/"),
    stats(r).replace("|", "/"),
    clean(body(r)).replace("|", "/"),
    clean(footer(r)).replace("|", "/"),
    clean(r["set"]).replace("|", "/"),
    r["slug"],
  ]


def write(path, cols, rows):
  with open(path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(cols)
    w.writerows(rows)
  print("written", path.split("\\")[-1], "rows", len(rows))


def main():
  test = len(sys.argv) > 1 and sys.argv[1] == "test"
  rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig", newline="")))
  for kind, label in STACKS:
    members = [r for r in rows if pile(r) == kind]
    # a two-faced card cannot live in a deck whose backs are all the deck name:
    # build_flip.py prints it as one card with a face on each side instead
    members = [r for r in members if r["name"] not in FLIP]
    if test:
      members = members[:PER_PAGE]
    fronts = [front_row(r) for r in members]
    for i, row in enumerate(fronts, 1):
      row[0] = str(i)
    suffix = "_test" if test else ""
    write(os.path.join(HERE, "cards_fronts_%s%s.csv" % (kind, suffix)), FRONT_COLS, fronts)

    # one page is enough: the nine backs of a stack are identical, the merger
    # repeats that page once per front page
    backs = []
    for i in range(1, PER_PAGE + 1):
      row = [""] * len(BACK_COLS)
      row[0] = str(i)
      row[BACK_COLS.index("back")] = label
      backs.append(row)
    write(os.path.join(HERE, "cards_back_%s%s.csv" % (kind, suffix)), BACK_COLS, backs)


main()
