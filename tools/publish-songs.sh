#!/bin/bash
# Отправляет изменения песен на сайт akkordy.zolotko.io.
# Запускается хуком после любой правки файлов в songs/ — см. .claude/settings.json.
# Работает молча: любые сбои не должны мешать работе сессии.
set -uo pipefail

cd /Users/Evgeniya/dev/accord || exit 0

# Менялось ли что-то в songs/ (включая новые файлы)?
if git diff --quiet HEAD -- songs/ 2>/dev/null && [ -z "$(git ls-files --others --exclude-standard songs/ 2>/dev/null)" ]; then
  exit 0
fi

# Над проектом работают несколько сессий сразу — ждём, если git занят соседней.
for _ in $(seq 1 15); do
  [ -f .git/index.lock ] || break
  sleep 1
done

git add songs/ 2>/dev/null || exit 0
git diff --cached --quiet -- songs/ && exit 0

changed=$(git diff --cached --name-only -- songs/ | sed 's|songs/||; s|\.txt$||' | paste -sd ', ' -)
git commit -q -m "Песни: ${changed}" || exit 0

# Соседняя сессия могла запушить раньше — тогда подбираем её коммиты и повторяем.
git push -q origin main 2>/dev/null || {
  git pull --rebase -q origin main 2>/dev/null && git push -q origin main 2>/dev/null
} || true

exit 0
