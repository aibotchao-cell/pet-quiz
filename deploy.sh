#!/usr/bin/env bash
# 把最新的 PET 單字測驗推上 GitHub Pages
set -e
SRC="/c/Users/YO/gh-pages/pet-quiz/index.html"
DEST="/c/Users/YO/gh-pages/pet-quiz"
export PATH="/c/Users/YO/bin/gh/bin:$PATH"
export GH_TOKEN=$(cat ~/.github_token | tr -d '\r\n')

cd "$DEST"
git add -A
if git diff --cached --quiet; then
  echo "(沒有任何變更)"
else
  git commit -m "update: $(date '+%Y-%m-%d %H:%M')" >/dev/null
  git push >/dev/null 2>&1
  echo "已推送 ✓  https://aibotchao-cell.github.io/pet-quiz/"
  echo "(GitHub Pages 大約 30~60 秒後生效)"
fi
