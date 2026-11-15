#!/bin/sh
# Read-only review of tools/gfxsweep.py pages with codex exec, in chunks of 8 pages.
# sh tools/sweep_review.sh work/sweep   -> work/sweep/review_<n>.txt
dir=${1:-work/sweep}
prompt='You are a read-only visual reviewer for a Japanese-to-English game translation (GBA). The attached images are pages of decompressed 4bpp tile graphics, shown grayscale, 2x zoom. Each block starts with a yellow label "OFFSET SIZE" (ROM offset of the LZ77 block, hex). Tiles of one block may be in arbitrary order, so a word may be split across tiles. List every block that contains Japanese writing (hiragana, katakana, kanji) or English words/lettering drawn as graphics. One line per block: page file name, block OFFSET, what the text looks like (script, approx content if legible, e.g. "katakana logo ゴーストトラップ", "English menu labels USE DROP"), confidence high/med/low. Ignore noise, pictures, sprites of characters, UI frames without letters. If a page has no lettering write "<page>: none". Do not run any commands; just answer.'
n=0
set -- "$dir"/p*.png
while [ $# -gt 0 ]; do
  args=""
  names=""
  i=0
  while [ $# -gt 0 ] && [ $i -lt 8 ]; do
    args="$args -i $1"
    names="$names $(basename "$1")"
    shift
    i=$((i + 1))
  done
  codex exec --skip-git-repo-check -s read-only $args -- "$prompt Pages in this batch, in attachment order:$names" > "$dir/review_$n.txt" 2>&1
  echo "batch $n exit $?:$names"
  n=$((n + 1))
done
