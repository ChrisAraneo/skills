---
name: notes-to-chapter
description: Turn a folder of copyrighted source notes (course transcripts, articles, glossaries) into an original, bilingual (English + Polish) VitePress chapter for beginners. Use when the user drops source .md files into the repo and asks for a new chapter, lesson, or set of pages built from them.
---

# Course notes → bilingual VitePress chapter

Goal: keep the **knowledge**, never the **expression**. You may reuse facts, ideas, and standard terms. You may not reuse the sources' sentences, examples, case studies, or glossary wording.

## Workflow

1. **Read everything.** Read every source file fully (use `offset`/`limit` for big files). Also read `.github/copilot-instructions.md` (style rules), `docs/.vitepress/config.mts`, and one existing page per locale.
2. **Outline by topic, not by source.** Sources repeat the same lesson as notes, transcripts, and glossaries. Merge the duplicates into 10–15 pages ordered from basic to advanced, plus an overview `index.md` and a glossary.
3. **Invent new examples.** Replace every source case study with one original running example and reuse it across the process pages (personas, user stories, sitemap, tests). Drop personal data such as certificate links, as well as interview transcripts and uncited statistics.
4. **Write the English pages yourself** in `docs/<chapter>/NN-slug.md`. Use simple words and short paragraphs, define each term on first use, and end each page with a `::: tip Key takeaway` box.
5. **Run the overlap check before translating** (see below). Rephrase every hit that isn't a standard term, URL, or well-known template. If you translate first, you will have to re-sync the translations.
6. **Translate in parallel.** Check `docs/pl` for established terms first, then spawn 2–3 background agents. Give each a fixed file list, a shared EN→PL terminology table, the exact H1 of every page (for cross-links and tables), and the style rules. When one agent reports a new term choice, relay it to the others with SendMessage.
7. **Wire up the site.** Add a sidebar for both locales in `config.mts`, link the chapter from both home pages, and update the README.
8. **Verify.** Compare heading and container counts between EN and PL, run `npm run docs:build` (it fails on dead links), run the overlap check on PL pages against PL sources, and read a few PL pages.

## Overlap check

Download the script into its own empty folder in the scratchpad (not the repo), read it, then run it with `-I`:

```sh
mkdir -p "<scratchpad>/overlap" && curl -fsSL -o "<scratchpad>/overlap/overlap.py" \
  https://raw.githubusercontent.com/ChrisAraneo/skills/refs/heads/master/.claude/skills/notes-to-chapter/overlap.py
# prints the n-word sequences each page shares with the sources (n=8 for EN, 7 for PL)
python -I "<scratchpad>/overlap/overlap.py" 8 "<sources dir>" docs/<chapter>
```

## Examples

**Example 1: new chapter from a course module**

User: "I put Module 5 notes in `5 Research/`. Create Chapter 2 in EN and PL."
→ read all files → outline `docs/research/01..09` → write EN with an original case study → overlap check and rephrase → 3 translation agents → sidebars + home links → build → PL overlap check.

**Example 2: rewriting a passage that is too close to the source**

Source: "A problem statement summarizes who the user is, what they need, and why."
Too close: "A problem statement summarizes who the user is, what they need, and why it matters."
Good: "A problem statement sums up the user, their need, and the reason the need matters." Follow it with your own example.

**Example 3: replacing a source case study**

The source used a bakery and an older customer persona who orders by phone. The replacement is a city library that adds 24/7 locker pickup, with a night-shift nurse persona and a retired-teacher persona. The concepts stay the same: business requirements → empathy map → persona → user story → problem statement → HMW → sitemap → tests.

## Style rules (from `.github/copilot-instructions.md`)

Use sentence-case headings. Use a list only when its items are longer than three words; otherwise write a sentence. Format list items as `**Key phrase** - explanation`. Don't use checkboxes, and don't put a bold label directly before a list; use a `### Question?` heading instead.
