"""Second pass over the character starting items.

The 113 character cards were cropped again at 520 px and read off
data/raw/start_items/*.png, independently of the first pass. This compares that
reading against data/starting_items.csv, the table the printed cards were built
from, and reports every card whose two readings disagree.
"""

import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SRC = os.path.join(BASE, "data", "starting_items.csv")
OUT = os.path.join(HERE, "starting_items_second_pass.csv")

SECOND = {
  "aa-azazel": "LORD OF THE PIT",
  "aa-blue_baby": "FOREVER ALONE",
  "aa-eden": "",
  "aa-eden_2": "",
  "aa-guppy": "INFESTATION",
  "aa-isaac": "THE D6",
  "aa-lilith": "INCUBUS",
  "aa-judas": "BOOK OF BELIAL",
  "aa-the_capricious": "GLITCH",
  "aa-the_harlot": "GELLO",
  "aa-the_forgotten": "THE BONE",
  "aa-the_keeper": "WOODEN NICKEL",
  "aa-the_lost": "HOLY MANTLE",
  "aa-the_savage": "BERSERK",
  "anni-bumbo_the_stout": "BAG-O-HOLES",
  "anni-florian": "GAME SQUID",
  "anni-level_one_isaac": "",
  "b-cain": "SLEIGHT OF HAND",
  "b-eden": "",
  "b-blue_baby": "FOREVER ALONE",
  "b-eve": "THE CURSE",
  "b-judas": "BOOK OF BELIAL",
  "b-isaac": "THE D6",
  "b-lazarus": "LAZARUS' RAGS",
  "b-lilith": "INCUBUS",
  "b-samson": "BLOOD LUST",
  "b-the_forgotten": "THE BONE",
  "b-maggy": "YUM HEART",
  "b2-blue_baby": "FOREVER ALONE",
  "b2-eve": "THE CURSE",
  "b2-cain": "SLEIGHT OF HAND",
  "b2-eden": "",
  "b2-lilith": "INCUBUS",
  "b2-isaac": "THE D6",
  "b2-judas": "BOOK OF BELIAL",
  "b2-lazarus": "LAZARUS' RAGS",
  "b2-maggy": "YUM HEART",
  "b2-samson": "BLOOD LUST",
  "b2-the_forgotten": "THE BONE",
  "blank-character": "",
  "box-cain": "SLEIGHT OF HAND",
  "box-isaac": "THE D6",
  "box-the_lost": "HOLY MANTLE",
  "bum-bum_bo": "BAG-O-TRASH",
  "fsp-bum_bo": "BAG-O-TRASH",
  "fsp-dark_judas": "DARK ARTS",
  "fsp-guppy": "INFESTATION",
  "fsp-whore_of_babylon": "GIMPY",
  "fsp2-bum_bo": "BAG-O-TRASH",
  "fsp2-dark_judas": "DARK ARTS",
  "fsp2-guppy": "INFESTATION",
  "fsp2-whore_of_babylon": "GIMPY",
  "g-azazel": "LORD OF THE PIT",
  "g-apollyon": "VOID",
  "g-the_keeper": "WOODEN NICKEL",
  "g-the_lost": "HOLY MANTLE",
  "g2-azazel": "LORD OF THE PIT",
  "g2-apollyon": "VOID",
  "g2-the_keeper": "WOODEN NICKEL",
  "g2-the_lost": "HOLY MANTLE",
  "p-eden": "",
  "p-eden_3": "",
  "p-eden_4": "",
  "r-eden": "",
  "r-eden_2": "",
  "ret-eden": "",
  "r-bethany": "BOOK OF VIRTUES",
  "r-flash_isaac": "CLASSIC ROLLER",
  "r-jacob_and_esau": "SIBLING RIVALRY",
  "r-the_baleful": "SOULBOND",
  "r-the_benighted": "HEMOPTYSIS",
  "r-the_broken": "SPINDOWN DICE",
  "r-the_capricious": "GLITCH",
  "r-the_curdled": "SUMPTORIUM",
  "r-the_dauntless": "HYPERCOAGULATION",
  "r-the_deceiver": "CEREMONIAL BLADE",
  "r-the_deserter": "ANIMA SOLA",
  "r-the_empty": "ABYSS",
  "r-the_enigma": "FLIP",
  "r-the_fettered": "DEAD WEIGHT",
  "r-the_harlot": "GELLO",
  "r-the_hoarder": "BAG OF CRAFTING",
  "r-the_miser": "KEEPER'S BARGAIN",
  "r-the_savage": "BERSERK",
  "r-the_soiled": "IBS",
  "r-the_zealot": "LEMEGETON",
  "rwz-abe": "POSSESSION",
  "rwz-ash": "BALL OF TUMORS",
  "rwz-baba": "IS YOU",
  "rwz-blind_johnny": "JOHNNY'S KNIVES",
  "rwz-blue_archer": "BOW AND ARROW",
  "rwz-boyfriend": "GIRLFRIEND",
  "rwz-bum_bo_the_weird": "STRANGE MARBLE",
  "rwz-captain_viridian": "GRAVITY",
  "rwz-crewmate": "EMERGENCY MEETING!",
  "rwz-edmund": "THE REAL LEFT HAND",
  "rwz-guy_spelunky": "SPELUNKING PACK",
  "rwz-johnny": "FOOTBALL",
  "rwz-pink_knight": "LOLLYPOP",
  "rwz-psycho_goreman": "HUNKY BOYS",
  "rwz-quote": "POLAR STAR",
  "rwz-salad_fingers": "RUSTY SPOONS",
  "rwz-steven": "LIL STEVEN",
  "rwz-the_knight": "FOCUS",
  "rwz-the_silent": "RING OF THE SNAKE",
  "rwz-yung_venuz": "POP POP!",
  "soi-clubby_the_seal": "CLUB",
  "soi-gish": "BALL OF TAR",
  "soi-stacy": "UNSTABLE DNA",
  "soi-the_hoarder": "BAG OF CRAFTING",
  "soi-the_miser": "KEEPER'S BARGAIN",
  "tw-tapeworm": "PINK PROGLOTTID",
  "ytz-guppy": "INFESTATION",
}


def norm(s):
  s = (s or "").upper().strip()
  s = s.replace("\u2019", "'").replace("\u2018", "'")
  s = s.replace("\u2014", "-").replace("\u2013", "-")
  s = re.sub(r"\s+", " ", s)
  s = re.sub(r"^THE ", "", s)  # "THE CURSE" / "CURSE" style noise
  return s


def main():
  rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig", newline="")))
  first = {r["slug"]: r["starting_item"] for r in rows}

  missing = sorted(set(first) - set(SECOND))
  extra = sorted(set(SECOND) - set(first))
  print("first pass rows", len(first), "second pass rows", len(SECOND))
  print("in the table but not read again", len(missing), missing)
  print("read again but not in the table", len(extra), extra)

  diff = []
  for slug in sorted(set(first) & set(SECOND)):
    if norm(first[slug]) != norm(SECOND[slug]):
      diff.append((slug, first[slug], SECOND[slug]))
  print("disagreements", len(diff))
  for slug, a, b in diff:
    print(" ", slug, "| table:", repr(a), "| second read:", repr(b))

  with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, quotting=csv.QUOTE_MINIMAL, lineterminator="\n") if False else csv.writer(f, lineterminator="\n")
    w.writerow(["slug", "starting_item"])
    for slug in sorted(SECOND):
      w.writerow([slug, SECOND[slug]])
  print("written", OUT)


main()
