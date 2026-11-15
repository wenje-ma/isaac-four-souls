"""Chinese pilot: the same cards, bodies translated except for the vocabulary.

Only the body changes. The card name, the type line and the back stay English --
the rule deck already explains every whitelisted term, so a translated body that
keeps `loot`, `hp`, `treasure` in English reads consistently against it.

The output is a separate stack (`cnroom`) so the English build is untouched: the
renderer keys everything (CSV, sizes cache, tex, PDF) on the stack name.
"""

import csv, os, re, shutil, sys

CN = r"D:\wenje-ma\isaac-four-souls\cn"
DECK = r"D:\wenje-ma\isaac-four-souls\en\deck"

STACKS = [("cncharacter", "character"), ("cntreasure", "treasure"),
          ("cnmonster", "monster"), ("cnloot", "loot"), ("cnroom", "room"),
          ("cnsoul", "soul"), ("cnrule", "rule")]

# STYLE.md 50-59: no Chinese punctuation anywhere, half-width marks with English
# spacing. Applied here, at build time, and not in the source CSV: the commas it
# introduces would otherwise be read as field separators by anything that opens
# the file by hand.
_PUNCT = {
  "，": ",", "、": ",", "。": ".", "：": ":", "；": ";", "？": "?", "！": "!",
  "（": "(", "）": ")", "【": "[", "】": "]", "“": '"', "”": '"',
  "‘": "'", "’": "'", "…": "...", "　": " ",
}

_CJK = r"\u4e00-\u9fff"


def punct(text):
  for old, new in _PUNCT.items():
    text = text.replace(old, new)
  # no space in front of a mark, one space behind it (unless the line ends there)
  text = re.sub(r" +([,.;:?!)\]])", r"\1", text)
  text = re.sub(r"([,.;:?!])(?=[^\s)\]}])", r"\1 ", text)
  # one space where a Chinese character meets Latin or a digit
  text = re.sub(r"([%s])([A-Za-z0-9])" % _CJK, r"\1 \2", text)
  text = re.sub(r"([A-Za-z0-9])([%s])" % _CJK, r"\1 \2", text)
  # quotes hug the text inside them; the one space goes outside, on the CJK side
  # (pair them in order: odd quote is the opening one)
  parts = []
  opening = True
  for i, ch in enumerate(text):
    if ch == '"':
      while parts and parts[-1] == " ":
        parts.pop()
      if opening:
        if parts and re.match(r"[%sA-Za-z0-9]" % _CJK, parts[-1]):
          parts.append(" ")
        parts.append('"')
      else:
        parts.append('"')
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if nxt and re.match(r"[%sA-Za-z0-9]" % _CJK, nxt):
          parts.append(" ")
      opening = not opening
    else:
      parts.append(ch)
  text = "".join(parts)
  # a closing bracket followed by a Chinese character
  text = re.sub(r"([\)\]])([%s])" % _CJK, r"\1 \2", text)
  text = re.sub(r" {2,}", " ", text)
  return text.strip()


def build(src_stack, cn_stack):
  tr = {r["slug"]: r["effect_cn"] for r in
        csv.DictReader(open(os.path.join(CN, "data", "translations.csv"),
                            encoding="utf-8"))}

  fronts = list(csv.DictReader(open(os.path.join(DECK, "cards_fronts_%s.csv" % src_stack),
                                    encoding="utf-8")))
  missing = [r["slug"] for r in fronts if r["slug"] not in tr]
  for r in fronts:
    if r["slug"] in tr:
      r["body"] = punct(tr[r["slug"]])
  if missing:
    print("no translation, left English:", missing)

  fout = os.path.join(DECK, "cards_fronts_%s.csv" % cn_stack)
  with open(fout, "w", encoding="utf-8", newline="\n") as f:
    w = csv.DictWriter(f, fieldnames=list(fronts[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(fronts)

  backs = list(csv.DictReader(open(os.path.join(DECK, "cards_back_%s.csv" % src_stack),
                                   encoding="utf-8")))
  for r in backs:
    r["back"] = src_stack.upper()
  with open(os.path.join(DECK, "cards_back_%s.csv" % cn_stack), "w",
            encoding="utf-8", newline="\n") as f:
    w = csv.DictWriter(f, fieldnames=list(backs[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(backs)

  print("translated %d of %d cards -> %s" % (len(fronts) - len(missing), len(fronts), fout))


def main():
  for cn_stack, src_stack in STACKS:
    build(src_stack, cn_stack)


if __name__ == "__main__":
  main()
