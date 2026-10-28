#!/usr/bin/env bash
# sync_mirrors.sh -- push the current site/ to the two domain-mirror repos, after any content update.
#   bash tools/sync_mirrors.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GHP="agifuturefoundation.github.io"
for entry in "agifellowship.church:www.agifellowship.church" "agi.lease:www.agi.lease"; do
  repo="${entry%%:*}"; cname="${entry##*:}"
  dir="$(mktemp -d)"
  rsync -a "$ROOT/site/" "$dir/"
  printf '%s\n' "$cname" > "$dir/CNAME"
  touch "$dir/.nojekyll"
  (cd "$dir" && git init -q -b main && git add -A &&
    git commit -qm "site mirror sync for $cname $(date -u +%FT%TZ)" &&
    git remote add origin "https://github.com/AGIFutureFoundation/${repo}.git" && git push -q --force origin main)
  echo "synced $cname <- site/ ($(du -sh "$dir" | cut -f1))"
  rm -rf "$dir"
done
echo "done. $GHP serves all three cnames; verify DNS + https after a few minutes."
