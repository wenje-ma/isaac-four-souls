import glob
import os
import time

import pymupdf

for f in sorted(glob.glob(r"print\cards_duplex_*.pdf")):
  d = pymupdf.open(f)
  print("%-34s %3d pages %9d B %s" % (
    os.path.basename(f), d.page_count, os.path.getsize(f),
    time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(f)))))
