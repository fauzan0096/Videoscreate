---
name: sunnah-reel-agent
description: >-
  Turn a one-line brief ("aaj ka reel: ...") into a finished, source-verified 30-60 s vertical reel
  plus title/description, using the Shamela connector and the sunnah_reels CLI. Use for any request to
  make, verify, queue or render a hadith / sunnah / hadith-myth reel.
---

# sunnah-reel-agent

The user gives ONLY the idea (a hadith, a question, a claim). You do the rest. Work in the repo root.

## 1. Pick the series
- **qa** ("Sahaba ne poocha"): a named companion asks a real question, the Prophet ﷺ answers.
- **myth** ("Hadith ya Afwah?"): a popular saying is checked against the books.
- If the idea is neither, add it as a plain idea (`data/ideas.json`) with an existing template.

## 2. Verify on Shamela BEFORE writing anything (never from memory)
1. `shamela_resolve` the book (Bukhari / Muslim ids: look them up, do not assume).
2. `shamela_verify_quote` the Arabic against that book. Verbatim or "differs only in tashkeel" = good.
   "partial"/"not_found" = the wording in your head is wrong: read the page text it returns and use THAT.
3. Record `book_id` + `page_id` (the page_id Shamela returns, not the printed page).
4. Hadith numbers differ between editions: say which edition (e.g. "no. 504 in al-Bagha ed.").
5. Note who narrated it and who actually asked (a narrator reporting a man's question is not the asker).
6. **myth**: never give your own grading. Find a named scholar's wording in a book (Bayhaqi, Saghani,
   al-Albani's Sahih/Da'if Sunan books...) and cite book + page. Use "weak chains" or "listed among
   fabricated sayings" exactly as the scholar said. Do not call a saying "fake" if the source only says weak,
   and note when part of it (e.g. 2nd half) has other routes.
7. If anything cannot be verified: STOP, tell the user, leave status "unverified" (video gets a DRAFT mark).

## 3. Build + render (one command)
```bash
python -m sunnah_reels new qa   --who "Ibn Mas‘ud" --text "Which deed is most beloved to Allah?" \
   --quote "Prayer at its proper time. Then kindness to parents. Then striving in the way of Allah." \
   --ref "Sahih al-Bukhari 527" --arabic "الصلاة على وقتها" --book-id 735 --page-id 884 --target 40
python -m sunnah_reels new myth --text "Seek knowledge, even in China." --verdict weak \
   --quote "Seek knowledge, even in China." --ref "al-Bayhaqi, al-Madkhal 2/663" --arabic "..." --book-id 39268 --page-id 753
```
Length is `--target` seconds (30-60). Output: `out/<id>_<title>.mp4` + `.txt` (title, description, source, hashtags).
Daily queue: `python -m sunnah_reels daily`.

## 4. Package
Add `yt_title` / `yt_thumb` to the idea (title <= 60 chars, subject in the first 40, thumbnail <= 3 words that do not
repeat the title; skills from youtube-agent-skill `/yt-package` and `title.py` apply). Run `python tools/export_web.py`.

## 5. Hand back
The mp4 path, the .txt text, the Shamela URL, and the ONE thing the user should eyeball before posting (the Arabic on screen).
Nothing is posted by you. Last line: **ship it, or change it?**
