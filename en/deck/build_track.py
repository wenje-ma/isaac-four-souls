"""The TRACK card: the D8's countdown, and the HP ruler that replaces it.

The rules put the D8 in solo and co-op and never roll it there: it starts at 8,
goes down once per round, and once more every time a character dies, and the run
is over when it reaches 0. That is a track, not a randomiser, so it fits on
paper -- and the same ladder shows a monster's HP at the table.

The name is TRACK and not COUNTER: COUNTER is the die a player puts on a card as
a marker, and one word for both was ambiguous -- user decision, 2026-11-17.

Rendered with XeLaTeX like the rest of the deck.
"""

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

# Card size: 63.5 x 88.9 mm, poker size, the same sheet as the card deck.
# The ladder was drawn for 70 x 99, so every slot below is the old value scaled
# by SY (height) and every letter by SX (width); the grid is centred on A4.
BASE_W, BASE_H = 70.0, 99.0
CARD_W, CARD_H = 63.5, 88.9
SX = CARD_W / BASE_W
SY = CARD_H / BASE_H
PAGE_W, PAGE_H = 210.0, 297.0
GRID_W, GRID_H = CARD_W * 3, CARD_H * 3
X0 = (PAGE_W - GRID_W) / 2.0
Y0 = (PAGE_H - GRID_H) / 2.0

INSET = 5.5 * SX
TOP, BOX_H, GAP = 26.5 * SY, 5.2 * SY, 0.5 * SY
BOX_W = 42.0 * SX  # card relative, 10.5 mm in from the trim
WORD = {8: "START", 7: "", 6: "", 5: "", 4: "", 3: "", 2: "", 1: "LAST STEP", 0: "DEFEAT"}
FOOT = ["DOWN 1 PER ROUND", "AND 1 FOR EVERY DEATH"]

PREAMBLE = r"""\documentclass[UTF8,fontset=none]{ctexart}
\usepackage[paperwidth=210mm,paperheight=297mm,margin=0mm]{geometry}
\usepackage{tikz}
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont[Path=C:/Windows/Fonts/]{simhei.ttf}
\setmainfont{lmroman10-regular.otf}[
  BoldFont      = lmroman10-bold.otf,
  ItalicFont    = lmroman10-italic.otf,
  BoldItalicFont= lmroman10-bolditalic.otf]
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\newcommand{\tkfont}[2]{\fontsize{#1}{\dimexpr#1pt*#2\relax}\selectfont}
\begin{document}
"""
PAGE_HEAD = (r"\begin{tikzpicture}[remember picture, overlay, x=1mm, y=1mm]"
             r"\begin{scope}[shift={(current page.north west)}]")
PAGE_TAIL = r"\end{scope}\end{tikzpicture}\clearpage"


def box(x, y, w, h, body):
  return (r"\node[anchor=north west,inner sep=0pt,outer sep=0pt,"
          r"text width=%.2fmm,minimum height=%.2fmm,align=flush center] "
          r"at (%.3f,%.3f) {%s};" % (w, h, x, y, body))



def cut_frame(xl, yt):
  "The trim rectangle of one card, 0.2 pt on the cut line, like every other face."
  return (r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
          % (xl, -yt, xl + CARD_W, -(yt + CARD_H)))


def cbox(xc, yc, w, h, body):
  "A node centred on (xc, yc): the row's type sits in the middle of its box."
  return (r"\node[anchor=center,inner sep=0pt,outer sep=0pt,"
          r"text width=%.2fmm,minimum height=%.2fmm,align=flush center] "
          r"at (%.3f,%.3f) {%s};" % (w, h, xc, -yc, body))


def front(c, r):
  xl, yt = X0 + CARD_W * c, Y0 + CARD_H * r
  parts = [cut_frame(xl, yt)]
  parts.append(box(xl + 3.5 * SX, -(yt + 9.4 * SY), CARD_W - 7.0 * SX, 9.0 * SY,
                   r"{\bfseries\tkfont{%.2f}{1.1} TRACK\par}" % (13.0 * SX)))
  for i in range(9):  # 8 down to 0
    y = yt + TOP + i * (BOX_H + GAP)
    parts.append(r"\draw[line width=0.12pt] (%.2f,%.2f) rectangle (%.2f,%.2f);"
                 % (xl + 14.0 * SX, -y, xl + 14.0 * SX + BOX_W, -(y + BOX_H)))
    # the row is two cells with their own rule: the digit centres in the left
    # 12 mm, the word centres in the right 30 mm, so both look placed and the
    # 42 mm box stops reading as an empty strip with type shoved to the edges
    mid = y + BOX_H / 2.0 - 0.08 * SY
    parts.append(cbox(xl + 20.0 * SX, mid, 12.0 * SX, BOX_H,
                      r"{\bfseries\tkfont{%.2f}{1.0} %d\par}" % (13.5 * SX, 8 - i)))
    word = WORD[8 - i]
    if word:
      parts.append(cbox(xl + 41.0 * SX, mid, 30.0 * SX, BOX_H,
                        r"{\bfseries\tkfont{%.2f}{1.0}%s\par}" % (6.5 * SX, word)))
  parts.append(box(xl + 3.5 * SX, -(yt + 79.4 * SY), CARD_W - 7.0 * SX, 3.4 * SY,
                   r"{\tkfont{%.2f}{1.1} %s\par}" % (5.5 * SX, FOOT[0])))
  parts.append(box(xl + 3.5 * SX, -(yt + 82.9 * SY), CARD_W - 7.0 * SX, 3.4 * SY,
                   r"{\tkfont{%.2f}{1.1} %s\par}" % (5.5 * SX, FOOT[1])))
  return "\n".join(parts)


def back(c, r):
  xl, yt = X0 + CARD_W * c, Y0 + CARD_H * r
  parts = []
  # frame restored, 7.0mm in, matching the token backs
  parts.append(
      r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
      % (xl + 7.0 * SX, -(yt + 7.0 * SY), xl + CARD_W - 7.0 * SX,
         -(yt + CARD_H - 7.0 * SY)))
  parts.append(box(xl + 3.5 * SX, -(yt + 17.5 * SY), CARD_W - 7.0 * SX, 5.0 * SY,
                   r"{\tkfont{%.2f}{1.2} THE BINDING OF ISAAC\par}" % (5.5 * SX)))
  parts.append(box(xl + 3.5 * SX, -(yt + 22.1 * SY), CARD_W - 7.0 * SX, 6.0 * SY,
                   r"{\bfseries\tkfont{%.2f}{1.2} FOUR SOULS\par}" % (7.5 * SX)))
  parts.append(box(xl + 3.5 * SX, -(yt + 39.5 * SY), CARD_W - 7.0 * SX, 20.0 * SY,
                   r"{\bfseries\tkfont{%.2f}{1.1}TRACK\par}" % (20.0 * SX)))
  parts.append(r"\draw[line width=0.12pt] (%.2f,%.2f) -- (%.2f,%.2f);"
               % (xl + 19.0 * SX, -(yt + 63.0 * SY), xl + CARD_W - 19.0 * SX,
                  -(yt + 63.0 * SY)))
  return "\n".join(parts)


def compile_tex(name, cell):
  out = [PREAMBLE, PAGE_HEAD, cell, PAGE_TAIL, r"\end{document}" + "\n"]

def compile_tex(name, cell):
  out = [PREAMBLE, PAGE_HEAD, cell, PAGE_TAIL, r"\end{document}" + "\n"]
  os.makedirs(TEX, exist_ok=True)
  path = os.path.join(TEX, "track_%s.tex" % name)
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(out))
  for _ in range(2):
    subprocess.run([XELATEX, "-interaction=nonstopmode", "-halt-on-error",
                    os.path.basename(path)], cwd=TEX,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
  pdf = path.replace(".tex", ".pdf")
  dest = os.path.join(BUILD, "track_%s.pdf" % name)
  if os.path.exists(dest):
    os.remove(dest)
  os.replace(pdf, dest)
  return dest


def main():
  os.makedirs(BUILD, exist_ok=True)
  cells = [(c, r) for r in range(3) for c in range(3)]
  front_page = "".join(front(c, r) for c, r in cells)
  back_page = "".join(back(c, r) for c, r in cells)
  f = compile_tex("fronts", front_page)
  b = compile_tex("back", back_page)
  out = PdfWriter()
  out.add_page(PdfReader(f).pages[0])
  out.add_page(PdfReader(b).pages[0])
  target = os.path.join(BASE, "print", "cards_duplex_track.pdf")
  with open(target, "wb") as fh:
    out.write(fh)
  stale = os.path.join(BASE, "print", "cards_duplex_counter.pdf")
  if os.path.exists(stale):
    os.remove(stale)
  print("wrote", os.path.basename(target), "1 sheet, 9 copies")


if __name__ == "__main__":
  main()
