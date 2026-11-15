"""The Chinese Trick/Treat card: one physical card, a face on each side.

English builds this from the scraped text (see en/deck/build_flip.py); here the
two faces come from cn/data/translations.csv, split at the "Treat:" label, so
the Chinese card stays in step with the rest of the deck. Everything else -- the
centre cell, the shrink-until-it-fits loop, the sheet geometry -- is reused from
the English builder unchanged.
"""

import csv, importlib.util, os, sys

CN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(CN, "..", "en", "deck")
PRINT = os.path.join(CN, "print")

SLUG = "challenge-trick_treat-comp"
NAME = "Trick/Treat"


def load(path, name):
  spec = importlib.util.spec_from_file_location(name, path)
  m = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(m)
  return m


def faces():
  bf = load(os.path.join(DECK, "build_flip.py"), "build_flip")
  c = load(os.path.join(DECK, "make_duplex_csv.py"), "make_duplex_csv")
  bc = load(os.path.join(CN, "deck", "build_cn.py"), "build_cn")
  tr = {r["slug"]: r["effect_cn"] for r in csv.DictReader(
      open(os.path.join(CN, "data", "translations.csv"), encoding="utf-8"))}
  if SLUG not in tr:
    sys.exit("%s is not translated" % SLUG)
  text = bc.punct(tr[SLUG])
  cut = text.find("Treat:")
  if cut < 0:
    sys.exit("%s has no Treat half" % SLUG)
  for r in csv.DictReader(open(os.path.join(CN, "..", "en", "data", "cards_final.csv"),
                               encoding="utf-8")):
    if r["name"] != NAME:
      continue
    head = {"name": c.clean(r["name"]), "subtitle": c.subtitle(r),
            "stats": c.stats(r), "footer": ""}
    front = dict(head)
    back = dict(head)
    front["body"] = text[:cut].strip()
    back["body"] = text[cut:].strip()
    return bf, front, back
  sys.exit("%s is not in cards_final.csv" % NAME)


def main():
  # build_flip renders through card() with a freshly loaded renderer, never
  # through build_tex, so the two per-language marks are set here: a Chinese
  # body wants SimSun's circled digits and a straight ASCII quote.
  os.environ["CARD_PIP_FONT"] = "pipsong"
  os.environ["CARD_STRAIGHT_QUOTE"] = "1"
  bf, front, back = faces()
  fp = bf.render(front, "cards_fronts_cnflip")
  bp = bf.render(back, "cards_back_cnflip")
  from pypdf import PdfReader, PdfWriter
  os.makedirs(PRINT, exist_ok=True)
  w = PdfWriter()
  w.add_page(PdfReader(fp).pages[0])
  w.add_page(PdfReader(bp).pages[0])
  out = os.path.join(PRINT, "cards_duplex_cnflip.pdf")
  with open(out, "wb") as f:
    w.write(f)
  print("cnflip       sheets   1  %5.2f MB  %s" % (
    os.path.getsize(out) / 1048576, os.path.basename(out)))


if __name__ == "__main__":
  main()
