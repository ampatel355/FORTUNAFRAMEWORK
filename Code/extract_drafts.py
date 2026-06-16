"""Pull the ```latex fenced blocks from the drafting workflow output into files."""
import json
import re
from pathlib import Path

OUT = Path("/private/tmp/claude-501/-Users-aryanpatel-Desktop-FCRI/"
           "bd95f954-ccea-4326-8324-7899274a92b8/tasks/wde5myj4b.output")
DST = Path("/Users/aryanpatel/Desktop/Fortuna/Code/drafts")
DST.mkdir(exist_ok=True)

data = json.loads(OUT.read_text())["result"]

for key in ("theory", "measure", "intro", "condense"):
    text = data[key]
    m = re.search(r"```latex\n(.*?)```", text, re.DOTALL)
    if not m:
        print(f"!! no latex block in {key}")
        continue
    body = m.group(1).rstrip() + "\n"
    (DST / f"{key}.tex").write_text(body)
    print(f"{key:10s} -> {len(body.splitlines())} lines")
