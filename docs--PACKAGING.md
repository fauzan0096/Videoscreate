# Packaging (title + thumbnail) — linted with youtube-agent-skill `title.py`
Fields `yt_title` / `yt_thumb` live in `data/series_*.json`. Rules used: title <= 60 chars, subject in the first 40,
thumbnail <= 3 words and never repeats the title, a number or a name where honest.

| id | title | thumbnail |
|----|-------|-----------|
| 101 | Ibn Mas‘ud Asked About the 3 Deeds Allah Loves Most | WHICH FIRST? |
| 102 | 3 Times Mother. Who Did the Prophet ﷺ Name 4th? | THEN WHO? |
| 103 | 1 Question, 6 Words: Sufyan's Answer in Islam | SAY THIS |
| 104 | Feed People, Greet Everyone: The Prophet's ﷺ Answer | 1 MEAL + SALAM |
| 201 | Is 'Cleanliness Is Half of Faith' a Real Hadith? | CHECKED |
| 202 | ‘Seek Knowledge Even in China’: Real Hadith? | WEAK? |
| 203 | ‘Love of Homeland Is Faith’: Real Hadith? | WHO GRADED IT? |
| 204 | ‘Paradise Is at Mothers’ Feet’: The Real Wording | WORDS CHANGED |

Honesty rules: myth titles stay as a QUESTION until you have verified the grading on Shamela. Never put a verdict
("FAKE", "SAHIH") on a thumbnail that the reel body does not source. "6 words" in #103 is the English wording; recount
if you change the translation. Re-run: `python3 skills/yt-package/title.py --title "..." --thumb "..."`.
