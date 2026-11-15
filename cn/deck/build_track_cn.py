"""The Chinese TRACK card: the same 8-to-0 ladder, the row labels in Chinese.

Numbers stay as digits; only the three row words and the two footnotes are
translated, because those are the only words on the face. The card name on the
back stays English (TRACK), like every other back in the set.

Geometry and layout come from the English builder: this file swaps the words and
the font only, so the two printings cut identically.
"""

import importlib.util, os, subprocess

CN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(CN, "..", "en", "deck")
BUILD = os.path.join(CN, "deck", "build")
TEX = os.path.join(BUILD, "tex")
PRINT = os.path.join(CN, "print")


def load(path, name):
  spec = importlib.util.spec_from_file_location(name, path)
  m = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(m)
  return m


bt = load(os.path.join(DECK, "build_track.py"), "build_track")

bt.WORD = {8: "开始", 7: "", 6: "", 5: "", 4: "", 3: "", 2: "", 1: "最后一步", 0: "失败"}
bt.FOOT = ["每回合减 1", "每有人死亡再减 1"]

PREAMBLE = bt.PREAMBLE.replace(
    r"\setCJKmainfont[Path=C:/Windows/Fonts/]{simhei.ttf}",
    r"\setCJKmainfont[Path=C:/Windows/Fonts/,AutoFakeBold=2]{simsun.ttc}")


def compile_tex(name, cell):
  out = [PREAMBLE, bt.PAGE_HEAD, cell, bt.PAGE_TAIL, r"\end{document}" + "\n"]
  os.makedirs(TEX, exist_ok=True)
  path = os.path.join(TEX, "track_cn%s.tex" % name)
  with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("".join(out))
  for _ in range(2):
    subprocess.run([bt.XELATEX, "-interaction=nonstopmode", "-halt-on-error",
                    os.path.basename(path)], cwd=TEX,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
  pdf = path.replace(".tex", ".pdf")
  dest = os.path.join(BUILD, "track_cn%s.pdf" % name)
  if os.path.exists(dest):
    os.remove(dest)
  os.replace(pdf, dest)
  return dest


def main():
  from pypdf import PdfReader, PdfWriter
  os.makedirs(BUILD, exist_ok=True)
  os.makedirs(PRINT, exist_ok=True)
  cells = [(c, r) for r in range(3) for c in range(3)]
  f = compile_tex("fronts", "".join(bt.front(c, r) for c, r in cells))
  b = compile_tex("back", "".join(bt.back(c, r) for c, r in cells))
  out = PdfWriter()
  out.add_page(PdfReader(f).pages[0])
  out.add_page(PdfReader(b).pages[0])
  target = os.path.join(PRINT, "cards_duplex_cntrack.pdf")
  with open(target, "wb") as fh:
    out.write(fh)
  print("cntrack      sheets   1  %5.2f MB  %s" % (
    os.path.getsize(target) / 1048576, os.path.basename(target)))


if __name__ == "__main__":
  main()
