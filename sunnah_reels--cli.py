import argparse, json, os, sys, datetime
from .render import Renderer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "ideas.json")


FILES = ["ideas.json", "series_qa.json", "series_myth.json"]
DDIR = os.path.dirname(DATA)

def load():
    out = []
    for f in FILES:
        p = os.path.join(DDIR, f)
        if os.path.exists(p):
            for x in json.load(open(p, encoding="utf-8")): x["_src"] = f; out.append(x)
    return out

def save(ideas):
    for f in FILES:
        part = [{k: v for k, v in x.items() if k != "_src"} for x in ideas if x["_src"] == f]
        if part: json.dump(part, open(os.path.join(DDIR, f), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def get(ideas, i):
    return next(x for x in ideas if x["id"] == i)

def parse_ids(s, ideas):
    out = []
    for part in s.split(","):
        if "-" in part: a, b = part.split("-"); out += range(int(a), int(b) + 1)
        else: out.append(int(part))
    return out

def cmd_list(a):
    for x in load():
        if a.status and x["status"] != a.status: continue
        if a.series and x.get("series", "sunnah") != a.series: continue
        print(f'{x["id"]:>3} {"✓" if x["status"]=="verified" else "·"} [{x["theme"]:<9}] {x["title"]}  —  {x["ref"]}')

def cmd_check(a):
    ideas = load(); bad = 0
    for x in ideas:
        for k in ("title", "lines", "quote_en", "ref", "template"):
            if not x.get(k): print("missing", k, "in", x["id"]); bad += 1
        if x["status"] == "verified" and not (x.get("arabic") and x.get("shamela")): print("verified but no arabic/shamela:", x["id"]); bad += 1
    v = sum(x["status"] == "verified" for x in ideas)
    print(f"{len(ideas)} ideas · {v} verified · {len(ideas)-v} need Shamela verification · {bad} problems")

def out_path(x, out):
    return os.path.join(out, f"{x['id']:03d}_{x['title'].lower().replace(' ', '_').replace('’','')}.mp4")

def post_text(x):
    url = (x.get("shamela") or {}).get("url", "")
    return (x.get("yt_title") or x["title"]) + "\n\n" + f"“{x['quote_en']}”\n{x['ref']}\n" + (f"Shamela: {url}\n" if url else "") + \
        "\n(Meaning translation — check the source.)\nSend this to someone who needs it.\n\n#sunnah #hadith #islam #shorts #reels\n"

def render_one(x, a, draft=False):
    r = Renderer(x, fps=a.fps, draft=draft, target=getattr(a, "target", None))
    path = out_path(x, a.out); print(f"#{x['id']} {x['title']}  ({r.tl['total']:.0f}s)")
    if r.tl["total"] > 60.5: print("  warning: longer than 60s - shorten lines/quote")
    r.render(path, music=getattr(a, "music", None))
    open(path[:-4] + ".txt", "w", encoding="utf-8").write(post_text(x)); print("  ->", path, "+ .txt (title/description for posting)")

def cmd_new(a):
    """One command = one finished reel. Give the brief, get video + post text."""
    ideas = load(); base = 101 if a.series == "qa" else 201
    nid = max([x["id"] for x in ideas if x.get("series") == a.series] + [base - 1]) + 1
    if a.series == "qa":
        lines = [f"{a.who} asked the Prophet ﷺ:", f"“{a.text}”", "^" + (a.hook or "Listen to the answer.")]; tpl = "ask"
    else:
        vl = dict(sahih="Yes — it is authentic.", hasan="Yes — it is authentic (hasan).", weak="Hadith scholars graded it weak.")[a.verdict]
        lines = ["Everyone says:", f"“{a.text}”", "Is it a real hadith?", "^" + (a.hook or vl)]; tpl = "myth"
    x = dict(id=nid, series=a.series, theme=a.series, template=tpl, title=a.title or a.text[:40], lines=lines, quote_en=a.quote, ref=a.ref,
             arabic=a.arabic or "", target=a.target or 40, status="unverified")
    if a.series == "myth": x["verdict"] = a.verdict
    if a.book_id and a.page_id:
        x["shamela"] = dict(book_id=a.book_id, page_id=a.page_id, url=f"https://shamela.ws/book/{a.book_id}/{a.page_id}", checked=str(datetime.date.today()))
        if x["arabic"]: x["status"] = "verified"
    x["_src"] = "series_qa.json" if a.series == "qa" else "series_myth.json"
    ideas.append(x); save(ideas); print("saved idea", nid, "·", x["status"])
    if not a.no_render: render_one(x, a, draft=x["status"] != "verified")

def cmd_daily(a):
    """Render the next verified, not-yet-rendered idea (run once a day)."""
    for x in load():
        if x["status"] == "verified" and x.get("series") in (a.series or ("qa", "myth")) and not os.path.exists(out_path(x, a.out)):
            a.target = a.target or 40; return render_one(x, a)
    print("Nothing left to render. Add a new idea:  python -m sunnah_reels new --help")

def cmd_render(a):
    ideas = load()
    for i in parse_ids(a.ids, ideas):
        x = get(ideas, i); draft = x["status"] != "verified"
        if draft and not a.draft:
            print(f"#{i} {x['title']}: source not verified on Shamela. Verify it (see README) or pass --draft."); continue
        r = Renderer(x, fps=a.fps, draft=draft, target=a.target)
        path = os.path.join(a.out, f"{i:03d}_{x['title'].lower().replace(' ', '_').replace('’','')}.mp4")
        if a.preview:
            os.makedirs(a.out, exist_ok=True)
            for k, f in enumerate([.12, .5, .8, .93]):
                r.frame(int(r.frames * f)).save(os.path.join(a.out, f"prev_{i:03d}_{k}.png"))
            print("previews saved"); continue
        print(f"#{i} {x['title']}  ({r.tl['total']:.0f}s)"); r.render(path, music=a.music); print("  ->", path)

def cmd_schedule(a):
    ideas = [x for x in load() if "day" in x]; d0 = datetime.date.fromisoformat(a.start)
    for x in ideas[:a.days]:
        d = d0 + datetime.timedelta(days=x["day"] - 1)
        print(f'Day {x["day"]:>2}  {d}  #{x["id"]:<3} {"✓" if x["status"]=="verified" else "⚠ verify"}  {x["title"]}')

def cmd_mark(a):
    ideas = load(); x = get(ideas, a.id)
    x.update(arabic=a.arabic, status="verified", shamela=dict(book_id=a.book_id, page_id=a.page_id, url=f"https://shamela.ws/book/{a.book_id}/{a.page_id}", checked=str(datetime.date.today())))
    save(ideas); print("marked verified:", a.id)

def main(argv=None):
    p = argparse.ArgumentParser(prog="sunnah-reels"); s = p.add_subparsers(required=True)
    q = s.add_parser("list"); q.add_argument("--status"); q.add_argument("--series", help="qa | myth"); q.set_defaults(f=cmd_list)
    q = s.add_parser("check"); q.set_defaults(f=cmd_check)
    q = s.add_parser("render"); q.add_argument("ids", help="e.g. 1  or 1-7  or 1,4,9"); q.add_argument("--out", default="out"); q.add_argument("--fps", type=int, default=30)
    q.add_argument("--music"); q.add_argument("--target", type=int, help="seconds, 30-60"); q.add_argument("--draft", action="store_true", help="allow unverified (watermarked)"); q.add_argument("--preview", action="store_true"); q.set_defaults(f=cmd_render)
    q = s.add_parser("schedule"); q.add_argument("--start", default=str(datetime.date.today())); q.add_argument("--days", type=int, default=60); q.set_defaults(f=cmd_schedule)
    q = s.add_parser("mark-verified"); q.add_argument("id", type=int); q.add_argument("--arabic", required=True); q.add_argument("--book-id", type=int, required=True); q.add_argument("--page-id", type=int, required=True); q.set_defaults(f=cmd_mark)
    q = s.add_parser("new"); q.add_argument("series", choices=["qa", "myth"]); q.add_argument("--text", required=True, help="qa: the question | myth: the claim")
    q.add_argument("--who", default="A companion"); q.add_argument("--quote", required=True, help="English meaning of the verified text"); q.add_argument("--ref", required=True)
    q.add_argument("--arabic"); q.add_argument("--book-id", type=int); q.add_argument("--page-id", type=int); q.add_argument("--verdict", default="sahih", choices=["sahih", "hasan", "weak"])
    q.add_argument("--hook"); q.add_argument("--title"); q.add_argument("--target", type=int); q.add_argument("--no-render", action="store_true"); q.add_argument("--out", default="out"); q.add_argument("--fps", type=int, default=30); q.add_argument("--music"); q.set_defaults(f=cmd_new)
    q = s.add_parser("daily"); q.add_argument("--series", nargs="*"); q.add_argument("--target", type=int); q.add_argument("--out", default="out"); q.add_argument("--fps", type=int, default=30); q.add_argument("--music"); q.set_defaults(f=cmd_daily)
    a = p.parse_args(argv); a.f(a)
