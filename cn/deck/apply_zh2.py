"""Fold the retranslated cn/data/zh2/*.txt over cn/data/translations.csv.

zh2 is the plain-language pass: same scope as the first translation (body only,
whitelist terms left in English), but written to read like Chinese rather than
like a gloss. Every slug already in the CSV is replaced; a slug that somehow is
not there yet is added. Order is kept at the printed order, punctuation goes
through build_cn.punct() so the half-width / spacing rules hold.
"""

import csv, importlib.util, io, os

CN = r"D:\wenje-ma\isaac-four-souls\cn"
OUT = os.path.join(CN, "data", "translations.csv")
ZH2 = os.path.join(CN, "data", "zh2")


def load(name):
  spec = importlib.util.spec_from_file_location(name, os.path.join(CN, "deck", name + ".py"))
  m = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(m)
  return m


def main():
  mt = load("merge_translations")
  fix = mt.punct()

  rows = {}
  order = []
  for r in csv.DictReader(io.open(OUT, encoding="utf-8")):
    rows[r["slug"]] = r["effect_cn"]
    order.append(r["slug"])

  replaced = added = 0
  for name in sorted(os.listdir(ZH2)):
    if not name.endswith(".txt"):
      continue
    for slug, text in mt.read_zh(os.path.join(ZH2, name)):
      if slug in rows:
        replaced += 1
      else:
        order.append(slug)
        added += 1
      rows[slug] = text

  rank = mt.pdf_order()
  order.sort(key=lambda s: rank.get(s, len(rank)))

  with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writerow(["slug", "effect_cn"])
    for slug in order:
      w.writerow([slug, fix(rows[slug])])

  print("rows %d (replaced %d, added %d)" % (len(order), replaced, added))


if __name__ == "__main__":
  main()
