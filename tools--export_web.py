"""Writes web/data.js from the JSON data files. Run after verifying/marking ideas."""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
keep = ("id", "series", "title", "lines", "quote_en", "arabic", "ref", "status", "verdict", "template", "chain")
out = []
for f in ("series_qa.json", "series_myth.json", "series_isnad.json"):
    out += [{k: x[k] for k in keep if k in x} for x in json.load(open(os.path.join(R, "data", f), encoding="utf-8"))]
open(os.path.join(R, "web", "data.js"), "w", encoding="utf-8").write("const IDEAS=" + json.dumps(out, ensure_ascii=False) + ";")
print("web/data.js:", len(out), "ideas")
