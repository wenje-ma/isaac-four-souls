"""Build the Chinese card sheets with XeLaTeX.

Geometry is the same as the English deck: 63 x 88 mm cards, 3 x 3 on A4,
189 x 264 mm grid centred on the page. One .tex per stack, all pages, nine cards
per page; pages are then merged with merge_duplex.py exactly like the English
deck.

Why LaTeX: the Chinese text needs real justification, punctuation compression
and line breaking rules, and XeLaTeX gets all three from xeCJK. It also means
the output PDF carries real text, so a card can be checked by measuring what
landed inside its rectangle instead of by looking at a picture.

  python en/deck/render_cards_tex.py            all stacks
  python en/deck/render_cards_tex.py sample     one stack
"""

import csv
import os
import re
import subprocess
import sys


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
ROOT = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build")

# Card size: 63.5 x 88.9 mm, poker size, i.e. 2.5 x 3.5 inches (user decision,
# 2026-11-18). The whole layout was drawn for 70 x 99, so every measurement
# below is the old one scaled by SX (width) / SY (height); fonts scale with SX.
BASE_W, BASE_H = 70.0, 99.0
CARD_W, CARD_H = 63.5, 88.9
SX = CARD_W / BASE_W
SY = CARD_H / BASE_H
PER_COL, PER_ROW = 3, 3
PAGE_W, PAGE_H = 210.0, 297.0
MARGIN = 3.5
GRID_W, GRID_H = CARD_W * PER_COL, CARD_H * PER_ROW
X0 = (PAGE_W - GRID_W) / 2.0
Y0 = (PAGE_H - GRID_H) / 2.0

INSET = 5.0 * SX
IN_W = CARD_W - 2 * INSET


# A duplex printer can place its second pass a millimetre or two off the first.
# Trim is cut against the front's border, so that slip shows up as a back frame
# that is not centred inside the cut card. These two shifts move the whole back
# grid against the paper to cancel it; they stay at zero for a printer that
# registers cleanly, and are in millimetres, positive meaning right and down.
BACK_DX = 0.0
BACK_DY = 0.0

# The front's ink sat 7.6 mm from the trim at the top and 11.3 mm at the bottom,
# which read as a card that leans up. Shifting the whole type block by half that
# difference puts the white above and below the type at the same depth.
CONTENT_DY = 1.85 * SY

# slot, measured from the top edge of the card
Y_TITLE, H_TITLE = 4.0 * SY, 11.0 * SY
Y_SUB, H_SUB = 15.4 * SY, 4.4 * SY
Y_STATS, H_STATS = 19.4 * SY, 5.0 * SY
Y_BODY, H_BODY = 25.6 * SY, 44.0 * SY
Y_FOOT, H_FOOT = 81.4 * SY, 9.6 * SY

# size limits, pt (the second number is the leading, a multiple of the size)
SIZE_TITLE = (16.0 * SX, 7.0)
SIZE_SUB = (8.5 * SX, 5.0)
SIZE_STATS = (9.0 * SX, 6.0)
SIZE_BODY = (10.0 * SX, 5.0)
SIZE_FOOT = (10.0 * SX, 5.0)

STACKS = ["character", "start", "treasure", "monster", "loot", "room", "soul", "rule"]
MIN_BODY = {"rule": 3.6 * SX}  # the quick references hold a whole page of rules

# A mixed stack prints several decks as one continuous stream, so a deck whose
# card count is not a multiple of nine no longer leaves its last sheet half empty:
# the next deck starts in the gap. Every card keeps its own stack's back name,
# because the back page is emitted per front page, not repeated.
MIX = {"cnall": ["cncharacter", "cntreasure", "cnmonster", "cnloot", "cnroom",
                 "cnsoul", "cnrule"]}

PREAMBLE = r"""\documentclass[UTF8,fontset=none]{ctexart}
\usepackage[paperwidth=210mm,paperheight=297mm,margin=0mm]{geometry}
\usepackage{tikz}
\usepackage{graphicx}
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont[Path=C:/Windows/Fonts/,AutoFakeBold=2]{simsun.ttc}
\xeCJKDeclareCharClass{CJK}{"25C6}
% xeCJK files the curly quotes as full-width CJK punctuation (U+2018/201C as an
% opening mark, U+2019/201D as a closing one) and sets them in the CJK face, so
% a quoted phrase came out in SimHei among Latin letters. Dashes and quotes
% belong to the Latin text. The class has to be redeclared at the start of the
% document: xeCJK installs its own punctuation lists while the package loads,
% which overrides anything declared earlier in the preamble.
\AtBeginDocument{%
  \xeCJKDeclareCharClass{Default}{"2013, "2014, "2018, "2019, "201C, "201D}}
\setmainfont{lmroman10-regular.otf}[
  BoldFont      = lmroman10-bold.otf,
  ItalicFont    = lmroman10-italic.otf,
  BoldItalicFont= lmroman10-bolditalic.otf]
% A roll result is a die face, so it prints as a circled digit. LM Roman carries
% no U+2460..2465 and XeTeX does not fall back, so the mark is set explicitly:
% Segoe UI Symbol in a Latin body, SimSun in a Chinese one (where a Segoe circle
% would be the only sans-serif mark on the card).
\newfontfamily\pipfont[Path=C:/Windows/Fonts/]{seguisym.ttf}
\newfontfamily\pipsong[Path=C:/Windows/Fonts/,AutoFakeBold=2]{simsun.ttc}
% CJKglue only: it lets a Chinese line stretch between characters when justified.
% CJKecglue is deliberately NOT set -- xeCJK replaces the source space at a
% CJK/Latin boundary with it, so `CJKecglue={\hskip 0.15em}` printed a 0.15em
% sliver there while the same space on the Latin->CJK side came through intact.
% Left unset, the space typed in the CSV is what prints, on both sides.
\xeCJKsetup{CJKglue={\hskip 0pt plus 0.1\baselineskip}}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\hyphenpenalty=100
\tolerance=2000
\emergencystretch=1em
\newcommand{\cardfont}[2]{\fontsize{#1}{\dimexpr#1pt*#2\relax}\selectfont}
\newcommand{\klabel}[1]{{\color{black!50}\fontspec{lmromancaps10-regular.otf}[FakeBold=3.0]\addfontfeatures{Scale=1.06}\cardfont{8.0}{1.1}#1}}
\newcommand{\kw}[1]{{\fontspec{lmromancaps10-regular.otf}[FakeBold=3.0]\addfontfeatures{Scale=1.06}#1}}
\newcommand{\kcent}[1]{{\fontspec{lmromancaps10-regular.otf}[FakeBold=3.0]#1}}
\begin{document}
"""

# the small caps label above a stat/value ("ATK", "HP") rides on the same scale
PREAMBLE = PREAMBLE.replace(r"\cardfont{8.0}{1.1}#1",
                            r"\cardfont{%.1f}{1.1}#1" % (8.0 * SX))

# The sheet is one overlay picture anchored to the page corner: flow placement
# would shift it by the text baseline, and a card must land on a whole
# millimetre or the cut line misses.
PAGE_HEAD = (r"\begin{tikzpicture}[remember picture, overlay, x=1mm, y=1mm]"
             r"\begin{scope}[shift={(current page.north west)}]")
PAGE_TAIL = r"\end{scope}\end{tikzpicture}\clearpage"


def esc(text):
  """Escape the characters TeX would eat; ¢ and ½ pass through unharmed."""
  out = []
  for ch in text:
    if ch in "&%$#_{}":
      out.append("\\" + ch)
    elif ch == "~":
      out.append(r"\textasciitilde{}")
    elif ch == "^":
      out.append(r"\textasciicircum{}")
    elif ch == "\\":
      out.append(r"\textbackslash{}")
    elif ch in PIPS:
      # The body may already spell a die face as U+2460, the way the translation
      # sources do. Left bare it lands in the body font, which has no glyph and
      # prints an empty box, so it goes through the same face _mark uses.
      out.append(_face(PIPS.index(ch) + 1))
    elif ch == '"' and _STRAIGHT_QUOTE:
      # xeCJK prints an ASCII quote as U+201D whichever side of the word it
      # sits on, so `含"bomb"的牌` came out `含”bomb”的牌`: both marks closing,
      # and the opening one visibly wrong. The Chinese stacks ask for the
      # straight glyph by name; the English stacks keep the engine's default,
      # where the same character never appears in a body.
      out.append(r"\textquotedbl{}")
    else:
      out.append(ch)
  return "".join(out)


# The site punctuates a roll label three ways: `2:`, `3;` and `4.`, so the
# label is a number plus any of the three, and every entry prints as `N:`.
LABEL = re.compile(r"(?<![\d-])(\d+(?:-\d+)?)\s*[:;.]\s*")
# A die face prints as a circled digit, so a result reads as one even beside
# the numbers in its own text (`③ loot 3`).
PIPS = "\u2460\u2461\u2462\u2463\u2464\u2465"
_PIP_FONT = os.environ.get("CARD_PIP_FONT") or "pipfont"
LEVEL = re.compile(r"\s*(LV\d+)")
# A paid ability is written `[coin] <verb>: ...` on the site, and the coin glyph
# there is a marker, not money: `Gain 25¢.` keeps its cent sign. Only the
# verb-prefixed form is a marker, otherwise `gain ¢ until ...` loses its cent.
ABILITY_TAG = re.compile(r"(?<![\d])\u00a2\s+(?=(?:Destroy|Pay|Discard|Remove)\b)")
CHOOSE = re.compile(r"((?:Choose|\u9009\u62e9)\s*(?:one|\u4e00\u9879|\d+))\s*[-:]\s*")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
TRAILING = re.compile(r"(?:Each time|Whenever|If you|When this|When you|At the|This starts|You may)")
BULLET = "\u2022"
# the rulebook writes the paid ability tag as $, which on a card reads as a
# price; the deck drops the tag entirely and keeps the cost as plain words:
# `Destroy this: Steal all shop items.` says what it costs without a glyph
ABILITY_MARK = ""
PAR = "\\par "
SEP = " / "


 # `Loot 3.` is an amount, not the next result, so a label never follows one of
# the verbs a count attaches to. A label does follow a plain noun (`monster
# deck 3-4:`), which is why the test is a word list and not "any word at all".
AMOUNT_VERB = re.compile(
  r"(?i)^(loot|loots|gain|gains|take|takes|deal|deals|lose|loses|steal|steals|"
  r"heal|add|pay|discard|put|remove|give|choose|roll|rolls)$")


def _face(n):
  """One die face as LaTeX: U+2460 in the face that carries it."""
  ch = r"{\%s %s}" % (_PIP_FONT, PIPS[n - 1])
  # Segoe's circle is drawn at about 0.6 em, which reads as a stray mark beside
  # 10 pt body type; SimSun's circled digit is full width already.
  return r"\scalebox{1.2}[1.2]{%s}" % ch if _PIP_FONT == "pipfont" else ch


def _mark(m):
  """`1:` -> circled 1, `3-4:` -> circled 3 to circled 4."""
  return "-".join(_face(int(n)) for n in m.group(1).split("-")) + ": "


def _roll_chunks(tail):
  """Cut the roll table at its result labels.

  A label is a dice result, so it stays inside 1..6. Gaps are normal — a room
  may only print 3-4, 5 and 6 — so labels are not required to run 1, 2, 3.
  """
  starts = []
  for m in LABEL.finditer(tail):
    if any(not 1 <= int(n) <= 6 for n in m.group(1).split("-")):
      continue
    before = re.search(r"(\S+)\s*$", tail[:m.start()])
    if before and AMOUNT_VERB.match(before.group(1).strip(".,;:")):
      continue
    # A period separates results only when it closes a previous result. A
    # number that merely ends a sentence (`expand monster slots by 1.`) also
    # matches LABEL, and reading it as a result splits the line and prints a
    # stray `/` in front of the number.
    if "." in m.group(0):
      prev = tail[:m.start()].rstrip()
      if prev and prev[-1] not in ".!?:/-\u2014\u2013" and not re.search(
          r"(?i)\brolls?$", prev):
        continue
    starts.append(m.start())
  if not starts:
    return []
  bounds = starts + [len(tail)]
  chunks = [tail[a:b] for a, b in zip(bounds[:-1], bounds[1:])]
  return [LABEL.sub(_mark, c.strip(), count=1) for c in chunks]


def _circle_labels(text):
  """Circled faces for a roll table written without a `Roll —` head.

  `Discard a LOOT card: Roll. If ... roll 3x instead — 1-4: Deal 1 DAMAGE...`
  has its results in the middle of prose, so the head split never sees them.
  The whole body is swept instead, with the same guards the split uses: a
  label is a die result (1..6, or a range inside it), it never follows an
  amount verb (`LOOT 3`), and a period only closes the previous result.
  """
  def repl(m):
    nums = m.group(1).split("-")
    if any(not 1 <= int(n) <= 6 for n in nums):
      return m.group(0)
    before = re.search(r"(\S+)\s*$", text[:m.start()])
    if before and AMOUNT_VERB.match(before.group(1).strip(".,;:")):
      return m.group(0)
    if "." in m.group(0):
      prev = text[:m.start()].rstrip()
      if prev and prev[-1] not in ".!?:/-\u2014\u2013" and not re.search(
          r"(?i)\brolls?$", prev):
        return m.group(0)
    return _mark(m)

  return LABEL.sub(repl, text)


def _roll_lines(text):
  """Roll results separated by /, the way the reward box separates its entries."""
  # 掷骰 is how the Chinese body names the same thing, and its dash arrives as
  # the typographic em dash, so both spellings and all three marks are head.
  m = re.search(r"(rolls?|Rolls?|\u63b7\u9ab0)\s*[-:\u2014]+", text)
  if not m:
    return text
  # `Roll-` and `Roll:` both read as a label, so both take the em dash the
  # Choose-one line uses: a hyphen here looks like a range (roll -1), and the
  # cards never print the site's colon anywhere else.
  head = text[:m.start()] + m.group(1) + " ---"
  tail = text[m.end():].strip()
  chunks = _roll_chunks(tail)
  if not chunks:
    return (head + " " + tail).strip() if tail else head
  lines = [(head + " " + chunks[0]).strip()]
  lines.extend(chunks[1:])
  return SEP.join(lines)


def _curse_lines(text):
  """A curse's own name already says what it is, so the body drops the `Curse:`
  label instead of printing it as a dash-prefixed heading."""
  return re.sub(r"(?i)^\s*curse\s*[:;\-\u2014\u2013]\s*", "", text)


def _cent_words(text):
  """One card spells the coin as a word (`lose x cents`); every card prints the
  symbol, and the symbol is what the keyword style picks up."""
  text = re.sub(r"(?i)(?<=[0-9x])\s+cents?\b", "\u00a2", text)
  return re.sub(r"(?i)\bcents?\b", "\u00a2", text)


def _choose_options(text):
  """The options after `Choose one` run together; separate them with /."""
  m = CHOOSE.search(text)
  if not m:
    return text
  head = (text[:m.start()] + m.group(1) + " ---").rstrip()
  tail = text[m.end():].strip()
  if not tail:
    return head
  if BULLET in tail or SEP in tail:
    return head + " " + tail
  sents = [s.strip() for s in SENTENCE.split(tail) if s.strip()]
  opts, extra = [], []
  for s in sents:
    if opts and TRAILING.match(s):
      extra.append(s)
    elif extra:
      extra.append(s)
    else:
      opts.append(s)
  out = head + " " + SEP.join(opts) if opts else head + " " + tail
  if extra:
    out += PAR + " ".join(extra)
  return out


# A term needs a word boundary; the cent glyph does not, because it is welded
# to its amount (`25¢`) and to a variable (`x¢`), and both must still print as
# a term rather than as the surrounding body face.
#
# The list is the fourteen nouns the cards keep in the caps face; every one of
# them also takes its plural, because a plural is the same term (`souls`,
# `loots`, `bosses`) and the cards print them as one word, not as a term plus
# a stray letter. The alternation is built longest first so `bosses` wins over
# `boss`.
TERMS = ("loot", "hp", "atk", "dice", "tap", "soul", "treasure",
         "damage", "room", "boss", "dc", "eternal", "counter", "ability",
         # `reward` is the box at the bottom of a monster card and a rule card
         # explains it, so it is marked like the rest (2026-11-17, user's call)
         "reward",
         # the keyword lines the real cards print above their text: each one has
         # a rule card, so the word is marked wherever it appears
         "indomitable", "trinket", "ambush", "curse", "guppy",
         # `item` is the umbrella over every treasure card in play, and the cards
         # say `every item they control`; a rule card defines it (2026-11-18)
         "item")


# The rule deck names the game's vocabulary, and its cards refer to each other
# by those names (`the stack`, `priority`, `monster slot`). Those references are
# worth marking, but only inside the rule deck: `turn`, `card` and `player` are
# ordinary English, and outside the rule deck a term like `stack` never appears
# at all, so a global entry would be dead config that also speckled the cards.
RULE_TERMS = ("start phase", "action phase", "end phase", "slot", "crowd slot",
              "purchase", "death", "win", "stack", "priority")

_DECK = ""
# Both marks are per stack in build_tex; the flip builder renders through
# card() without ever calling it, so it states its language here instead.
_STRAIGHT_QUOTE = os.environ.get("CARD_STRAIGHT_QUOTE") == "1"
_KEYWORD_RE = {}


def _plural(t):
  """The term's own plural, printed as one unit with the term.

  `ability` and `counter` do not take a plain `s`: the cards spell `abilities`,
  and a term plus a leftover letter was exactly the fault that put the plural
  inside the caps face in the first place.
  """
  if t.endswith("y"):
    return t[:-1] + "ies"
  if t.endswith(("s", "x", "z", "ch", "sh")):
    return t + "es"
  return t + "s"


def _term_forms(terms):
  forms = []
  for t in terms:
    t = t.replace(" ", r"\s+")
    forms.append(t)
    forms.append(_plural(t))
  return "|".join(sorted(forms, key=len, reverse=True))


def _keywords():
  """The body's keyword pattern; the rule deck has its own extra vocabulary."""
  bucket = "rule" if _DECK in ("rule", "cnrule") else "card"
  if bucket not in _KEYWORD_RE:
    terms = TERMS + RULE_TERMS if bucket == "rule" else TERMS
    _KEYWORD_RE[bucket] = re.compile(
        r"(?i)(?<![A-Za-z])(" + _term_forms(terms) + r")(?![A-Za-z])|\u00a2")
  return _KEYWORD_RE[bucket]



def style_keywords(text):
  """Body: the term is the point, so it is bold and full black.

  The match is lowercased first: the caps face only turns lowercase letters
  into small caps, so an already upper case term came out as full block
  capitals at body size and towered over the words around it.
  """
  def wrap(m):
    token = (m.group(1) or "\u00a2").lower()
    # a term is a unit: letting TeX hyphenate it split TREASURE as `TREA-`
    # `SURE` on a narrow card, so each one is boxed and never breaks. The
    # plural is part of the unit: `loots` was once `kw{loot}` + plain `s`, which
    # printed a lowercase s next to small caps and broke the word in two; the
    # s now takes the caps face with the rest of the term, as `souls` already
    # did.
    if token == "\u00a2":
      return r"\mbox{\kcent{%s}}" % token
    return r"\mbox{\kw{%s}}" % token

  return _keywords().sub(wrap, text)


def style_labels(text):
  """Stat line and reward line: the label steps back so its value reads first.

  The match is lowercased before it reaches the caps face, which is what makes
  it print as small caps rather than as full block capitals. A literal em dash
  becomes `---` for the same reason as in the body: xeCJK eats the space after
  U+2014.
  """
  return _keywords().sub(
      lambda m: "\\klabel{%s}" % (m.group(1) or "\u00a2").lower(),
      (text or "").replace("\u2014", "---"))


def format_body(text):
  """Lay a card's effect out the way the printed card does.

  The site writes option lists and roll tables as one run of prose; the card
  puts each option and each result on its own entry, separated by / like the
  reward box. Choose N takes an em dash. The coin glyph the scrape picked up is
  the "$" ability tag, not money: it marks an activated ability without a tap.

  A literal U+2014 from the data is rewritten to TeX's `---`, the same shape the
  renderer emits for `Roll` and `Choose one`. xeCJK classifies U+2014 as CJK
  punctuation and swallows the space after it, so `instead — 1-4:` printed as
  `instead —1-4:`; the ligature is typed as three hyphens and keeps its space.
  """
  # a real line break in the data (a stat badge above its ability) must not
  # become a `/`: the slash means "or" on these cards, and a badge and an
  # ability are both on. The newline is parked on a token the option join
  # cannot touch and restored as a paragraph break at the end.
  text = text.replace("\r", "").replace("\n", "\x00")
  text = text.replace("\u2014", "---")
  text = re.sub(r"\s*[" + chr(183) + BULLET + r"]\s*", lambda m: PAR + BULLET + " ", text)
  text = ABILITY_TAG.sub(
      lambda m: PAR + ABILITY_MARK + " "
      if m.start() and text[:m.start()].rstrip()[-1:] in ".!?"
      else ABILITY_MARK + " ",
      text)
  text = _roll_lines(text)
  if re.search(r"(?i)\brolls?\b|\u63b7\u9ab0", text):
    text = _circle_labels(text)
  text = _curse_lines(text)
  text = _cent_words(text)
  # a level-up item steps through LV4, LV8, LV10 as separate blocks, the way a
  # stat badge sits above its ability. The marker is parked on the newline token
  # rather than on \par, because the option join below turns every \par into
  # " / " and that slash would print as if the next level were an alternative.
  text = LEVEL.sub(lambda m: "\x00" + m.group(1).strip(), text)
  parts = [_choose_options(p) for p in text.split(PAR)]
  # a boundary is a line break, not a slash: `/` on these cards means "or", so
  # the second of two abilities printed after a slash read as an alternative to
  # the first. Only the option list and the roll table keep the slash, and both
  # join with SEP inside their own pass; the boundary parks on the newline token
  # and comes back as \par below.
  text = "\x00".join(p.strip() for p in parts if p.strip())
  text = re.sub(r"(?: / )+", " / ", text)
  text = re.sub(r" {2,}", " ", text).strip()
  return text.replace("\x00", PAR).strip()


def box(x, y, w, h, body, anchor="north west"):
  """A tikz node at (x, y), width w, height h, top aligned."""
  return (
    r"\node[anchor=%s,inner sep=0pt,outer sep=0pt,text width=%.2fmm,"
    r"minimum height=%.2fmm,align=flush center] at (%.3f,%.3f) {%s};"
    % (anchor, w, h, x, y, body)
  )


_MEASURE = {}


def _lm_bold():
  """The bold face of the title, read once, for real advance widths."""
  if "font" not in _MEASURE:
    from fontTools.ttLib import TTFont
    path = "D:/MiKTeX/fonts/opentype/public/lm/lmroman10-bold.otf"
    if not os.path.exists(path):
      _MEASURE["font"] = None
    else:
      f = TTFont(path)
      _MEASURE["font"] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
  return _MEASURE["font"]


def text_width(text, size):
  """Width of a run of text in points, from the font's own advance widths."""
  face = _lm_bold()
  if not face:
    return len(text) * 0.5 * size
  cmap, metrics, upem = face
  total = 0.0
  for ch in text:
    name = cmap.get(ord(ch))
    advance = metrics[name][0] if name and name in metrics else upem * 0.5
    total += advance
  return total * size / upem


BODY_BOTTOM = 80.6  # the text may run down to here: footer starts at 81.4


def text_top_for(row):
  """Where the effect text starts, in mm from the card top.

  A stat line sits in its own band. Without one the text takes that band back,
  but not the whole way: the subtitle's descenders end at 19.8, and starting
  at 19.4 printed the type line and the effect as one block. A 2.6mm gap
  matches what a card with a stat line shows between its two blocks.
  """
  if row.get("stats", "").strip():
    return Y_BODY
  return Y_STATS + 2.6


def text_bottom_for(row):
  """Where the effect text has to stop, in mm from the card top.

  The footer band exists on every card, whether or not something is printed in
  it. Giving the space back to a card without a reward line made its text
  block sit lower than the rest: Eden, which has no starting item, was the only
  card whose body was not on the same centre as its neighbours.
  """
  return BODY_BOTTOM


def title_lines(text, size):
  """How many lines the title wraps to at this size, by real widths."""
  width = IN_W * 72.0 / 25.4  # mm -> pt
  space = text_width(" ", size)
  cur, lines = 0.0, 1
  for word in text.split():
    w = text_width(word, size)
    if cur == 0.0:
      cur = w
    elif cur + space + w <= width:
      cur += space + w
    else:
      lines += 1
      cur = w
  return lines


def title_shift(name, size):
  """Millimetres to push the subtitle and the text down for a three line title.

  Two lines fit the 11 mm slot. Three do not, and only the long keyword
  reference cards get there, so those give up 5 mm of text area instead of
  shrinking the name: every card name stays the same size.
  """
  return 5.0 * SY if title_lines(name, size) >= 3 else 0.0


def fit_title(text, base, max_lines=2):
  """The title size: always base.

  One size for every card name, which is what a deck should look like. A name
  too long for two lines does not shrink; it takes a third line and pushes the
  text down (title_shift). Kept as a function so the call sites never change.
  """
  return base


def card(r, c, row, sizes):
  xl = X0 + CARD_W * c
  yt = Y0 + CARD_H * r  # distance from the page top to the card top

  title = sizes.get("title", 12.0 * SX)
  sub = sizes.get("sub", 7.5 * SX)
  stats = sizes.get("stats", 8.0 * SX)
  body = sizes.get("body", 10.0 * SX)
  foot = sizes.get("foot", 8.0 * SX)

  # every face carries its own frame, drawn 0.2 pt on the trim line itself, so
  # the sheet is cut against the front. The grid sits inside the printable area
  # of A4 (9.75 / 15.15 mm of white), so this frame is ink the printer can hold;
  # the per-card frames together are the full set of cut lines, which is why no
  # separate grid hairlines are drawn any more.
  parts = [r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
           % (xl, -yt, xl + CARD_W, -(yt + CARD_H))]

  # the trim line stays put; only the type inside it moves, so the cut is still
  # taken on the front's border
  yt = yt + CONTENT_DY

  name = esc(row.get("name", ""))
  dy = 0.0
  if name:
    title = fit_title(name, title)
    dy = title_shift(name, title)
    parts.append(box(xl + INSET, -(yt + Y_TITLE), IN_W, H_TITLE + dy,
                     r"{\bfseries\cardfont{%.1f}{1.22}%s\par}" % (title, name)))

  subtitle = esc(row.get("subtitle", ""))
  if subtitle:
    parts.append(box(xl + INSET, -(yt + Y_SUB + dy), IN_W, H_SUB,
                     r"{\itshape\cardfont{%.2f}{1.25}%s\par}" % (sub, subtitle)))

  stat_line = esc(row.get("stats", ""))
  if stat_line:
    # the values are bold, like the item name on the reward line; the labels stay
    # medium grey so the number still reads first
    parts.append(box(xl + INSET, -(yt + Y_STATS + dy), IN_W, H_STATS,
                     r"{\bfseries\cardfont{%.2f}{1.3}%s\par}"
                     % (stats, style_labels(stat_line))))

  # a card without a stat line gives that space back to the text, so a short
  # effect does not sit in the top third of an otherwise empty card; a subtitle
  # still owns its band, and the text starts under it
  text_top = text_top_for(row) + dy
  text_h = text_bottom_for(row) - text_top

  text = format_body(esc(row.get("body", "")))
  if text:
    # the block is centred in its band rather than hung from the top: a three
    # line effect high on a card left a hole at the bottom, while a full card
    # looked pushed up against the subtitle. anchor=center centres the node's
    # own text box, so nothing is stretched and no minimum height is needed.
    parts.append(
      r"\node[anchor=center,inner sep=0pt,outer sep=0pt,text width=%.2fmm,"
      r"align=justify] at (%.3f,%.3f) "
      r"{\cardfont{%.2f}{1.42}%s\par};"
      % (IN_W, xl + INSET + IN_W / 2.0, -(yt + text_top + text_h / 2.0), body,
         style_keywords(text)))

  footer = esc(row.get("footer", ""))
  raw_footer = row.get("footer", "")
  # the two label lines read the same way: a quiet label, a bold value, one line
  label_kind = None
  for prefix, label in (("STARTING ITEM:", "starting item"), ("REWARD:", "reward")):
    if footer and raw_footer.startswith(prefix):
      label_kind = (prefix, label)
      break

  if label_kind:
    prefix, label = label_kind
    value = esc(raw_footer[len(prefix):].strip())
    value_sz = 8.0 * SX
    # set in lowercase so the caps face turns it into small caps; measured from
    # the block-cap string at 0.72 of its width, which is what small caps take
    gap_pt = 1.0 * 72.0 / 25.4
    width = text_width(prefix[:-1], 8.0 * SX) * 1.06 * 0.72 + gap_pt \
            + text_width(raw_footer[len(prefix):].strip(), value_sz)
    scale = min(1.0, 140.0 * SX / width)
    line = (r"{\color{black!50}\fontspec{lmromancaps10-regular.otf}[FakeBold=3.0]"
            r"\addfontfeatures{Scale=1.06}\cardfont{%.2f}{1.1}%s}"
            r"\hspace{%.3fmm}{\bfseries\cardfont{%.1f}{1.3}%s}"
            % (8.0 * SX, label, 1.0, value_sz, value))
    parts.append(
      r"\node[anchor=north,inner sep=0pt,outer sep=0pt,text width=%.2fmm,"
      r"minimum height=%.2fmm,align=flush center] at (%.3f,%.3f) "
      r"{\scalebox{%.3f}[1]{%s}};"
      % (IN_W / scale, H_FOOT, xl + CARD_W / 2.0, -(yt + Y_FOOT), scale, line))
  elif footer:
    # one line always: a wrapped reward line moved the bands around, so a long
    # one is squeezed horizontally instead, exactly like the deck name on the
    # back. The node is widened by 1/scale so the squeezed text still lands on
    # the card centre.
    fscale = 1.0
    fwidth = text_width(raw_footer, foot)
    if fwidth > 140.0 * SX:
      fscale = 140.0 * SX / fwidth
    if fscale < 1.0:
      parts.append(
        r"\node[anchor=north,inner sep=0pt,outer sep=0pt,text width=%.2fmm,"
        r"minimum height=%.2fmm,align=flush center] at (%.3f,%.3f) "
        r"{\scalebox{%.3f}[1]{\bfseries\cardfont{%.2f}{1.32}%s}};"
        % (IN_W / fscale, H_FOOT, xl + CARD_W / 2.0, -(yt + Y_FOOT), fscale, foot, footer))
    else:
      parts.append(
        r"\node[anchor=north,inner sep=0pt,outer sep=0pt,text width=%.2fmm,"
        r"minimum height=%.2fmm,align=flush center] at (%.3f,%.3f) "
        r"{\bfseries\cardfont{%.2f}{1.32}%s\par};"
        % (IN_W, H_FOOT, xl + CARD_W / 2.0, -(yt + Y_FOOT), foot, footer))

  return "\n".join(parts)


def back_card(r, c, row):
  xl = X0 + CARD_W * c + BACK_DX
  yt = Y0 + CARD_H * r + BACK_DY
  stack = esc(row.get("back", ""))
  parts = []
  # frame back on: the interior cut lines now fix the trim, so a second pass
  # that misses by a millimetre is measured against the cut, not against ink.
  # 7.0mm in from the trim, which keeps it clear of the printer's dead edge and
  # lines up with the coin rim on the token backs.
  parts.append(
      r"\draw[line width=0.2pt,draw=black!70] (%.2f,%.2f) rectangle (%.2f,%.2f);"
      % (xl + 7.0 * SX, -(yt + 7.0 * SY), xl + CARD_W - 7.0 * SX,
         -(yt + CARD_H - 7.0 * SY)))
  parts.append(box(xl + INSET, -(yt + 17.5 * SY), IN_W, 5.0 * SY,
                   r"{\cardfont{%.2f}{1.2} THE BINDING OF ISAAC\par}" % (5.5 * SX)))
  parts.append(box(xl + INSET, -(yt + 22.1 * SY), IN_W, 6.0 * SY,
                   r"{\bfseries\cardfont{%.2f}{1.2} FOUR SOULS\par}" % (7.5 * SX)))
  # the stack name is what a player sorts by, so it takes the big line and the
  # brand drops to the size it has on the token and track backs. A two word
  # name (STARTING ITEM) is too wide at 20pt; keep the cap height and squeeze
  # the width only, the way Word's character scaling does, so every back still
  # has the same tall stack name instead of a smaller one.
  name_size = 20.0 * SX
  width = text_width(stack, name_size)
  scale = min(1.0, 130.0 * SX / width) if width else 1.0
  if scale < 1.0:
    # widen the box by 1/scale and squeeze the type by `scale`: the visual
    # width stays IN_W, so the label is still centred by the same node that
    # centres every other back, and keeping one line is what lets it stay 20pt
    w = IN_W / scale
    content = r"\scalebox{%.3f}[1]{\bfseries\cardfont{%.2f}{1.1}%s}" % (scale, name_size, stack)
    parts.append(box(xl + CARD_W / 2.0 - w / 2.0, -(yt + 39.5 * SY), w, 20.0 * SY, content))
  else:
    parts.append(box(xl + INSET, -(yt + 39.5 * SY), IN_W, 20.0 * SY,
                     r"{\bfseries\cardfont{%.2f}{1.1}%s\par}" % (name_size, stack)))
  # the short rule under the stack name, back again with the hairline frame:
  # on its own it looked stranded, but as part of the framed block it is what
  # makes the back read as a title area rather than floating type.
  parts.append(r"\draw[line width=0.12pt] (%.2f,%.2f) -- (%.2f,%.2f);"
               % (xl + 19.0 * SX, -(yt + 63.0 * SY), xl + CARD_W - 19.0 * SX,
                  -(yt + 63.0 * SY)))
  return "\n".join(parts)


def read_rows(path):
  if not os.path.exists(path):
    return []
  with open(path, "r", encoding="utf-8", newline="") as f:
    return list(csv.DictReader(f))


def cut_guides():
  """Hairlines on the interior grid only.

  The outer sides of the sheet coincide with the paper edge, where a printer
  cannot place ink, so only the inner cuts at 70 / 140 mm and 99 / 198 mm are
  drawn. They give the knife or the fold something to follow without adding a
  frame the trim would leave half printed.
  """
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


def build_tex(stack, mode):
  """One .tex per side: the front carries the card, the back carries the block.

  Separate files keep the same shape as the English pipeline, where merge_duplex
  expects build/cards_fronts_<kind>.pdf and build/cards_back_<kind>.pdf.
  """
  global _DECK, _STRAIGHT_QUOTE, _PIP_FONT
  _DECK = stack
  _STRAIGHT_QUOTE = stack.startswith("cn")
  _PIP_FONT = "pipsong" if stack.startswith("cn") else "pipfont"
  rows = stack_rows(stack, mode)
  if not rows:
    return None

  sizes = load_sizes(stack)
  preamble = PREAMBLE
  if stack.startswith("cn"):
    # A Chinese body reaches the margin far sooner than an English one, so the
    # few Latin words a translation keeps (attack, dice, a card name) were the
    # only thing left to hyphenate -- `pri-ority` split across two lines reads
    # as a typo between Chinese characters. The Chinese stacks simply do not
    # hyphenate; the slack goes into the spaces at the line ends.
    preamble = preamble.replace(r"\hyphenpenalty=100", r"\hyphenpenalty=10000")
  out = [preamble]
  for page_start in range(0, len(rows), PER_COL * PER_ROW):
    chunk = rows[page_start:page_start + PER_COL * PER_ROW]
    out.append(PAGE_HEAD)
    # no separate grid hairlines: each card's own frame already lies on the
    # trim line, and drawing both would put double ink on every cut
    for i, row in enumerate(chunk):
      r, c = divmod(i, PER_COL)
      if mode == "front":
        out.append(card(r, c, row, sizes.get(row["_key"], {})))
      else:
        out.append(back_card(r, c, row))
    out.append(PAGE_TAIL)
  out.append(r"\end{document}" + "\n")

  tex_dir = os.path.join(BUILD, "tex")
  os.makedirs(tex_dir, exist_ok=True)
  path = os.path.join(tex_dir, "cards_%s_%s.tex" % (
    "fronts" if mode == "front" else "back", stack))
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(out))
  return path


def compile_tex(path):
  """Run XeLaTeX twice: an overlay picture anchored to current page needs a
  second pass before it knows where the page edges are."""
  work = os.path.dirname(path)
  res = None
  for _ in range(2):
    res = subprocess.run(
      [XELATEX, "-interaction=nonstopmode", "-halt-on-error",
       os.path.basename(path)],
      cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
      break
  return res


def load_sizes(stack):
  import json
  if stack in MIX:
    # one cache per member stack, merged here; a mixed run must not move a card
    # onto a different body size than its own stack would have chosen
    sizes = {}
    for sub in MIX[stack]:
      path = os.path.join(BUILD, "sizes_%s.json" % sub)
      if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
          sizes.update(json.load(f))
    return sizes
  path = os.path.join(BUILD, "sizes_%s.json" % stack)
  if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_sizes(stack, sizes):
  import json
  if stack in MIX:
    for sub in MIX[stack]:
      part = {k: v for k, v in sizes.items() if k.split("#")[0] == sub}
      path = os.path.join(BUILD, "sizes_%s.json" % sub)
      with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(part, f, ensure_ascii=False, indent=1, sort_keys=True)
    return
  path = os.path.join(BUILD, "sizes_%s.json" % stack)
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(sizes, f, ensure_ascii=False, indent=1, sort_keys=True)


def back_name_of(sub):
  """The name printed on the back of one stack's cards ("LOOT", "灵魂" ...)."""
  rows = read_rows(os.path.join(HERE, "cards_back_%s.csv" % sub))
  return rows[0].get("back", "") if rows else ""


def stack_rows(stack, mode="front"):
  """The rows to print for this stack, one flat sequence.

  A plain stack reads its own csv. A mixed stack reads each member's fronts in
  order and tags every row with the size cache key and the stack it belongs to;
  in back mode it also writes that stack's back name into the row, so the back
  of a card never depends on where the card happened to land on the sheet.
  """
  if stack not in MIX:
    if mode == "front":
      rows = read_rows(os.path.join(HERE, "cards_fronts_%s.csv" % stack))
    else:
      rows = read_rows(os.path.join(HERE, "cards_back_%s.csv" % stack))
    for i, row in enumerate(rows):
      row["_key"] = "%s#%d" % (stack, i)
      row["_stack"] = stack
    return rows
  rows = []
  for sub in MIX[stack]:
    back = back_name_of(sub)
    for i, row in enumerate(read_rows(os.path.join(HERE, "cards_fronts_%s.csv" % sub))):
      row["_key"] = "%s#%d" % (sub, i)
      row["_stack"] = sub
      if mode == "back":
        row["back"] = back
      rows.append(row)
  return rows


def measure(pdf_path, rows):
  """Compare each card's text with its own text box; return overfull card indices.

  The PDF is in points and its origin is the top left corner, so every millimetre
  has to be converted before a span bbox can be compared with a card rectangle.
  """
  import pymupdf

  mm = 72.0 / 25.4
  doc = pymupdf.open(pdf_path)
  bad = []
  for idx, row in enumerate(rows):
    page = idx // 9
    slot = idx % 9
    if page >= doc.page_count:
      break
    rect_page = doc[page]
    r, c = divmod(slot, PER_COL)
    x0 = X0 + CARD_W * c
    card_top = PAGE_H - Y0 - CARD_H * (PER_ROW - r)
    has_stats = bool(row.get("stats", "").strip())
    dy = title_shift(row.get("name", ""), 12.0)
    top = text_top_for(row) + dy
    height = text_bottom_for(row) - top
    body_top = (card_top + top) * mm
    body_bottom = (card_top + top + height) * mm
    foot_top = (card_top + Y_FOOT) * mm
    has_footer = bool(row.get("footer", "").strip())
    lowest = 0.0
    for block in rect_page.get_text("dict")["blocks"]:
      for line in block.get("lines", []):
        for span in line["spans"]:
          b = pymupdf.Rect(span["bbox"])
          if not (x0 * mm - 0.8 < b.x0 < (x0 + CARD_W) * mm + 0.8):
            continue  # another card on the same page
          if b.y0 < body_top - 1.2:
            continue  # title and subtitle sit above their own boxes
          if b.y0 >= (card_top + CARD_H) * mm:
            continue  # a line that already starts below this card belongs to the next row
          if has_footer and b.y0 >= foot_top - 1.2:
            continue  # the reward line
          lowest = max(lowest, b.y1)
    if lowest > body_bottom + 0.6:
      # the node grows downward, so a card that does not fit simply keeps
      # printing past its own border: compare the lowest line with the box
      bad.append(idx)
  return sorted(set(bad))


def measure_titles(pdf_path, rows):
  """Card indices whose title runs outside its box or into the subtitle.

  fit_title estimates the line count from characters, which is close enough to
  choose a size but not to guarantee the box; this checks the compiled page.
  """
  import pymupdf

  mm = 72.0 / 25.4
  doc = pymupdf.open(pdf_path)
  bad = []
  for idx, row in enumerate(rows):
    page, slot = idx // 9, idx % 9
    if page >= doc.page_count:
      break
    r, c = divmod(slot, PER_COL)
    x0 = X0 + CARD_W * c
    card_top = PAGE_H - Y0 - CARD_H * (PER_ROW - r)
    dy = title_shift(row.get("name", ""), 12.0)
    title_box = pymupdf.Rect((x0 + INSET) * mm, (card_top + Y_TITLE - 1.0) * mm,
                             (x0 + CARD_W - INSET) * mm,
                             (card_top + Y_TITLE + H_TITLE + dy + 0.6) * mm)
    for block in doc[page].get_text("dict")["blocks"]:
      for line in block.get("lines", []):
        for span in line["spans"]:
          if "bold" not in span["font"].lower():
            continue
          b = pymupdf.Rect(span["bbox"])
          if b.x1 < x0 * mm or b.x0 > (x0 + CARD_W) * mm:
            continue  # another card on the same page
          if b.y0 < title_box.y0 or b.y0 > title_box.y1:
            continue
          if b.x0 < title_box.x0 - 0.8 or b.x1 > title_box.x1 + 0.8 or b.y1 > title_box.y1:
            bad.append(idx)
            break
  return sorted(set(bad))


def run(stack):
  tex = build_tex(stack, "front")
  if not tex:
    print("%-10s no cards" % stack)
    return
  rows = stack_rows(stack, "front")
  for attempt in range(12):
    tex = build_tex(stack, "front")  # sizes changed, re-emit
    res = compile_tex(tex)
    pdf = os.path.join(BUILD, "tex", os.path.splitext(os.path.basename(tex))[0] + ".pdf")
    if not os.path.exists(pdf):
      print(res.stdout[-800:])
      print("%-10s compile failed" % stack)
      return
    import pymupdf
    want = (len(rows) + PER_COL * PER_ROW - 1) // (PER_COL * PER_ROW)
    pages = pymupdf.open(pdf).page_count
    if pages < want:
      # a TeX error stops the run at the page that broke, and the leftover
      # PDF would otherwise be shipped as if the whole stack had compiled
      print("%-10s stopped at page %d of %d" % (stack, pages, want))
      print(res.stdout[-600:])
      return
    over = measure(pdf, rows)
    if not over:
      break
    sizes = load_sizes(stack)
    for idx in over:
      row = rows[idx]
      key = row["_key"]
      current = sizes.get(key, {})
      floor = MIN_BODY.get(row["_stack"], SIZE_BODY[1])
      current["body"] = max(floor, round(current.get("body", SIZE_BODY[0]) - 0.5, 2))
      sizes[key] = current
    save_sizes(stack, sizes)
    print("%-10s %d cards overfull, shrunk" % (stack, len(over)))
  else:
    print("%-10s still overfull: %s" % (stack, over))

  if stack == "rule":
    # one body size for the whole reference deck: the longest card picks it and
    # the rest follow, so the eight cards do not print at eight sizes. The size
    # is the largest that still fits every card.
    sizes = load_sizes(stack)
    body = None
    for candidate in [10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0]:
      for i in range(len(rows)):
        key = "%s#%d" % (stack, i)
        current = sizes.get(key, {})
        current["body"] = candidate
        sizes[key] = current
      save_sizes(stack, sizes)
      tex = build_tex(stack, "front")
      res = compile_tex(tex)
      pdf = os.path.join(BUILD, "tex",
                         os.path.splitext(os.path.basename(tex))[0] + ".pdf")
      if not os.path.exists(pdf):
        print(res.stdout[-800:])
        print("%-10s compile failed" % stack)
        return
      if not measure(pdf, rows):
        body = candidate
        break
    print("%-10s body %.2fpt on all %d cards" % (stack, body or 0.0, len(rows)))
  tight = measure_titles(pdf, rows)
  if tight:
    # reported, not auto-shrunk: the estimate already picked the size, and this
    # only tells a human which titles to look at
    print("%-10s title tight on %d cards: %s" % (stack, len(tight), tight[:8]))
  dest = os.path.join(BUILD, "cards_fronts_%s.pdf" % stack)
  if os.path.exists(dest):
    os.remove(dest)
  os.replace(pdf, dest)

  tex = build_tex(stack, "back")
  res = compile_tex(tex)
  pdf = os.path.join(BUILD, "tex", os.path.splitext(os.path.basename(tex))[0] + ".pdf")
  if not os.path.exists(pdf):
    print(res.stdout[-800:])
    print("%-10s back compile failed" % stack)
    return
  dest = os.path.join(BUILD, "cards_back_%s.pdf" % stack)
  if os.path.exists(dest):
    os.remove(dest)
  os.replace(pdf, dest)
  print("%-10s %3d cards -> fronts + back" % (stack, len(rows)))


def main():
  os.makedirs(BUILD, exist_ok=True)
  wanted = sys.argv[1:] or STACKS
  for stack in wanted:
    run(stack)


if __name__ == "__main__":
  main()
