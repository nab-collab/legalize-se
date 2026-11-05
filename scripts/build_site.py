#!/usr/bin/env python3
"""Build the static site into _site/: copies site/ and md/, and writes index.json."""
import json
import re
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "_site"
if out.exists():
    shutil.rmtree(out)
shutil.copytree(root / "site", out)
shutil.copytree(root / "md", out / "md")

index = []
for f in sorted((root / "md").glob("*.md")):
    head = f.read_text(encoding="utf-8").split("---", 1)[0]
    title = re.search(r"^#\s+(.+)$", head, re.M)
    sfs = re.search(r"\*\*SFS-nummer:\*\*\s*(.+?)\s*$", head, re.M)
    typ = re.search(r"\*\*Typ:\*\*\s*(.+?)\s*$", head, re.M)
    dept = re.search(r"\*\*Myndighet/Departement:\*\*\s*(.+?)\s*$", head, re.M)
    index.append({
        "id": f.stem,
        "t": title.group(1).strip() if title else f.stem,
        "n": sfs.group(1) if sfs else "",
        "y": typ.group(1) if typ else "",
        "d": dept.group(1) if dept else "",
    })

(out / "index.json").write_text(
    json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
)
(out / ".nojekyll").touch()
print(f"Built {len(index)} documents into {out}")
