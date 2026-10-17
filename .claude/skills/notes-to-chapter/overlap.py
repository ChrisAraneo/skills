"""Report word n-grams shared between source texts and output pages (verbatim-copy check)."""
import re, sys, pathlib
N = int(sys.argv[1]); src_dir = pathlib.Path(sys.argv[2]); out_dir = pathlib.Path(sys.argv[3])
words = lambda t: re.findall(r"[a-ząćęłńóśźż0-9']+", t.lower())
grams = lambda w: {" ".join(w[i:i+N]) for i in range(len(w)-N+1)}
src = set()
for f in src_dir.glob("*.md"):
    src |= grams(words(f.read_text(encoding="utf-8")))
total = 0
for f in sorted(out_dir.glob("*.md")):
    hits = sorted(grams(words(f.read_text(encoding="utf-8"))) & src)
    total += len(hits)
    print(f"{f.name}: {len(hits)} shared {N}-grams")
    for h in hits[:30]: print("   ", h)
print("TOTAL", total)
