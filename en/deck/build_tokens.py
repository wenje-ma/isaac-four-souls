"""Build the accessory deck: coins and hearts as cards.

Four Souls ships 100 plastic pennies, one D6 and one D8. The dice are bought
elsewhere; everything that is normally a token is printed here instead, at the
same 63 x 88 mm size as the cards so the whole deck cuts with one knife.

Contents
- 100 x 1c and 10 x 5c, the rules ask for a pool of at least 100c
- 48 hearts, one card is one HP

Hearts are cards rather than numbers so that damage is paid by taking a card
away, the way HP works in Sanguosha; a 0 to 8 number card would have to be
swapped every time something bled.

Counters are deliberately absent. 99 cards use counters and one starts with 32,
which paper chits cannot show, so a handful of 12 mm dice does that job.

Rendering is XeLaTeX, the same as the card deck: the coin glyph, the heart and
the small caps all have to land on a millimetre grid or the cutter misses them.
"""

import csv
import os
import subprocess

from pypdf import PdfReader, PdfWriter


def find_xelatex():
  "xelatex lives in MiKTeX's bin, which is not always on PATH."
  import shutil
  p = shutil.which('xelatex')
  if p:
    return p
  for cand in (r'D:\MiKTeX\miktex\bin\x64\xelatex.exe',):
    if os.path.exists(cand):
      return cand
  return 'xelatex'


XELATEX = find_xelatex()


HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")
TEX = os.path.join(BUILD, "tex")
CSV_OUT = os.path.join(HERE, "tokens.csv")

BASE_W, BASE_H = 70.0, 99.0
CARD_W, CARD_H = 63.5, 88.9
SX = CARD_W / BASE_W
SY = CARD_H / BASE_H
PER_COL, PER_ROW = 3, 3
PAGE_W, PAGE_H = 210.0, 297.0
GRID_W, GRID_H = CARD_W * PER_COL, CARD_H * PER_ROW
X0 = (PAGE_W - GRID_W) / 2.0
Y0 = (PAGE_H - GRID_H) / 2.0
INSET = 5.0 * SX
IN_W = CARD_W - 2 * INSET

PREAMBLE = r"""\documentclass[UTF8,fontset=none]{ctexart}
\usepackage[paperwidth=210mm,paperheight=297mm,margin=0mm]{geometry}
\usepackage{tikz}
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont[Path=C:/Windows/Fonts/]{simhei.ttf}
\newfontfamily\symfont[Path=C:/Windows/Fonts/]{seguisym.ttf}
\setmainfont{lmroman10-regular.otf}[
  BoldFont      = lmroman10-bold.otf,
  ItalicFont    = lmroman10-italic.otf,
  BoldItalicFont= lmroman10-bolditalic.otf]
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\newcommand{\tokfont}[2]{\fontsize{#1}{\dimexpr#1pt*#2\relax}\selectfont}
\begin{document}
"""
PAGE_HEAD = (r"\begin{tikzpicture}[remember picture, overlay, x=1mm, y=1mm]"
             r"\begin{scope}[shift={(current page.north west)}]")
PAGE_TAIL = r"\end{scope}\end{tikzpicture}\clearpage"

# coins first, so the pool cards come off the cutter before the hearts
ROWS = [("1\u00a2", "", "ONE CENT", "CENT POOL", "COIN")] * 100
# the rules never mention a 5c coin, "A Nickel!" is a loot card that says
# "Gain 5c". Ten of them is the Ultimate Collection's set: a convenience so a
# player holding 20c does not need twenty cards, not a rule.
ROWS += [("5\u00a2", "", "FIVE CENTS", "CENT POOL", "COIN")] * 10
# 4 players at 3 HP is 12; two monster slots of 8 HP is 16; the rest is spare
ROWS += [("", "\u2665", "1 HP", "HEALTH", "HEART")] * 48


def esc(text):
  out = []
  for ch in text:
    if ch in "&%$#_{}":
      out.append("\\" + ch)
    elif ch == "~":
      out.append(r"\textasciitilde{}")
    else:
      out.append(ch)
  return "".join(out)


def box(x, y, w, h, body):
  return (r"\node[anchor=north west,inner sep=0pt,outer sep=0pt,"
          r"text width=%.2fmm,minimum height=%.2fmm,align=flush center] "
          r"at (%.3f,%.3f) {%s};" % (w, h, x, y, body))


def front_cell(r, c, row):
  xl = X0 + CARD_W * c
  yt = Y0 + CARD_H * r
  # same trim frame as a card face, 0.2 pt on the cut line: the whole deck is
  # cut against the front, tokens included
  parts = [r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
           % (xl, -yt, xl + CARD_W, -(yt + CARD_H))]
  if row["big"]:
    # the ink, not the line box, is what should land on the card's mid line:
    # bold digits sit low in an LM line box, so the node starts 0.75 mm higher
    # than the box would need to and the glyph centres at 49.5.
    parts.append(box(xl + INSET, -(yt + 27.75 * SY), IN_W, 44.0 * SY,
                     r"{\bfseries\tokfont{%.1f}{1.0}%%s\par}" % (50.0 * SX) % esc(row["big"])))
  if row["heart"]:
    parts.append(box(xl + INSET, -(yt + 25.0 * SY), IN_W, 46.0 * SY,
                     r"{\symfont\tokfont{%.1f}{1.0}%%s\par}" % (64.0 * SX) % esc(row["heart"])))
  parts.append(box(xl + INSET, -(yt + 73.0 * SY), IN_W, 7.0 * SY,
                   r"{\bfseries\tokfont{%.1f}{1.2}%%s\par}" % (9.0 * SX) % esc(row["caption"])))
  return "\n".join(parts)


def back_cell(r, c, row):
  xl = X0 + CARD_W * c
  yt = Y0 + CARD_H * r
  parts = []
  # frame restored, 7.0mm in: same inset as the coin rim on the face
  parts.append(
      r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
      % (xl + 7.0 * SX, -(yt + 7.0 * SY), xl + CARD_W - 7.0 * SX,
         -(yt + CARD_H - 7.0 * SY)))
  parts.append(box(xl + INSET, -(yt + 17.5 * SY), IN_W, 5.0 * SY,
                   r"{\tokfont{%.2f}{1.2} THE BINDING OF ISAAC\par}" % (5.5 * SX)))
  parts.append(box(xl + INSET, -(yt + 22.1 * SY), IN_W, 6.0 * SY,
                   r"{\bfseries\tokfont{%.2f}{1.2} FOUR SOULS\par}" % (7.5 * SX)))
  parts.append(box(xl + INSET, -(yt + 39.5 * SY), IN_W, 20.0 * SY,
                   r"{\bfseries\tokfont{%.2f}{1.1}%%s\par}" % (20.0 * SX) % esc(row["back"])))
  parts.append(r"\draw[line width=0.12pt] (%.2f,%.2f) -- (%.2f,%.2f);"
               % (xl + 19.0 * SX, -(yt + 63.0 * SY), xl + CARD_W - 19.0 * SX,
                  -(yt + 63.0 * SY)))
  return "\n".join(parts)


def cut_guides():
  # interior grid hairlines only: the sheet is exactly 3 x 3 cards, so the
  # outer four sides are the paper edge and cannot carry ink
  parts = []
  for c in range(1, PER_COL):
    x = X0 + CARD_W * c
    parts.append(r"\draw[line width=0.2pt] (%.2f,%.2f) -- (%.2f,%.2f);"
                 % (x, -Y0, x, -(Y0 + GRID_H)))
  for r in range(1, PER_ROW):
    y = Y0 + CARD_H * r
    parts.append(r"\draw[line width=0.2pt] (%.2f,%.2f) -- (%.2f,%.2f);"
                 % (X0, -y, X0 + GRID_W, -y))
  return "\n".join(parts)


def build_tex(mode):
  rows = [{"n": i + 1, "big": b, "heart": h, "caption": c, "tag": t, "back": k}
          for i, (b, h, c, t, k) in enumerate(ROWS)]
  out = [PREAMBLE]
  for start in range(0, len(rows), PER_COL * PER_ROW):
    chunk = rows[start:start + PER_COL * PER_ROW]
    out.append(PAGE_HEAD)
    # each token cell carries its own trim frame, so no grid hairlines here
    for i, row in enumerate(chunk):
      r, c = divmod(i, PER_COL)
      out.append(front_cell(r, c, row) if mode == "fronts" else back_cell(r, c, row))
    out.append(PAGE_TAIL)
  out.append(r"\end{document}" + "\n")
  os.makedirs(TEX, exist_ok=True)
  path = os.path.join(TEX, "tokens_%s.tex" % mode)
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(out))
  return path


def compile_tex(path):
  for _ in range(2):
    subprocess.run([XELATEX, "-interaction=nonstopmode", "-halt-on-error",
                    os.path.basename(path)], cwd=TEX,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
  pdf = path.replace(".tex", ".pdf")
  dest = os.path.join(BUILD, "tokens_%s.pdf" % os.path.basename(path)[7:-4])
  if os.path.exists(dest):
    os.remove(dest)
  os.replace(pdf, dest)
  return dest


def main():
  os.makedirs(BUILD, exist_ok=True)
  rows = [{"n": i + 1, "big": b, "heart": h, "caption": c, "tag": t, "back": k}
          for i, (b, h, c, t, k) in enumerate(ROWS)]
  with open(CSV_OUT, "w", encoding="utf-8", newline="\n") as f:
    w = csv.DictWriter(f, fieldnames=["n", "big", "heart", "caption", "tag", "back"])
    w.writeheader()
    w.writerows(rows)

  front = compile_tex(build_tex("fronts"))
  back = compile_tex(build_tex("backs"))

  fronts, backs = PdfReader(front), PdfReader(back)
  out = PdfWriter()
  for f, b in zip(fronts.pages, backs.pages):
    out.add_page(f)
    out.add_page(b)
  target = os.path.join(BASE, "print", "cards_duplex_token.pdf")
  with open(target, "wb") as fh:
    out.write(fh)
  print("wrote", os.path.basename(target), len(fronts.pages), "sheets", len(rows), "cards")


main()
