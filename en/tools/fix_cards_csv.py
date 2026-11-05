"""Repair the header of cards.csv: strip stray BOMs and requote cleanly."""

import csv
import io
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "data" / "cards.csv"
raw = open(P, "rb").read()
while raw.startswith(b"\xef\xbb\xbf"):
  raw = raw[3:]
text = raw.decode("utf-8")
rows = list(csv.reader(io.StringIO(text)))
print("first field before:", repr(rows[0][0]))
rows[0][0] = rows[0][0].replace("\ufeff", "").strip('"')
print("first field after:", repr(rows[0][0]))
print("header:", rows[0])

with open(P, "w", encoding="utf-8", newline="") as f:
  w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
  w.writerows(rows)
print("rows rewritten:", len(rows) - 1)
