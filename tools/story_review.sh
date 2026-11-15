#!/bin/bash
# Story-pass review (references/translation.md §Review) by codex exec, read-only, up to 4 at a time.
#   bash tools/story_review.sh [chapter-name ...]   (default: every work/qa/story/chapters/*.txt)
# Reports: work/qa/story/reports/<chapter>.md. Then write work/qa/story/verdicts/<chapter>.tsv from each Assessment.
cd "$(dirname "$0")/.."
if [ "$1" = "--one" ]; then
  g=$2
  BRIEF=$(python tools/skill.py)/assets/story-reviewer-brief.md
  PRIOR=""
  LAST=$(ls work/qa/story/reports/$g.r[0-9].md 2>/dev/null | sort | tail -1)
  if [ -n "$LAST" ]; then
    PRIOR=" This is a re-review: the previous round's report is $LAST and its findings were addressed in the text you now read. Check each was fixed well (or argue it should not have been), and review the whole chapter afresh, including the new wording."
  fi
  codex exec --skip-git-repo-check -s read-only --output-last-message "work/qa/story/reports/$g.md" "You are the story-pass reviewer for a Japanese->English fan translation of the GBA game Ghost Trap. Read-only: do not edit any file, no git. Follow the brief in $BRIEF (game: Ghost Trap, target language: English). There is no docs/style-reference.md: the style reference is the rulings at the top of glossary.md and its voice table (George/Alicia/Karol/Shinfa/Albino/Reaper); also read docs/synopsis.md and docs/decisions.md. Chapter file: work/qa/story/chapters/$g.txt. Each entry: '>> id | source table', then one line per text page, 'JP  speaker: text' and 'EN  speaker: text'. 「」 after a speaker are dropped on purpose; -san honorifics are kept on purpose (D1); George narrates in first person (D8); widths and control codes are already checked. Field chapters are many short examine/hint messages grouped by table, not one continuous scene: judge consistency of voice, names and recurring phrasing across them. Read ALL of the chapter file in several passes before judging. Return the report in the brief's format (Critical / Important / Minor, each 'id - JP gist - problem - suggested EN', then '### Assessment' with ok or issue) as your final message.$PRIOR" > "work/qa/story/reports/$g.log" 2>&1
  echo "$g: exit $?"
  exit 0
fi
mkdir -p work/qa/story/reports
if [ $# -eq 0 ]; then set -- $(cd work/qa/story/chapters && ls *.txt | sed 's/\.txt$//'); fi
printf '%s\n' "$@" | xargs -P 4 -I{} bash tools/story_review.sh --one {}
