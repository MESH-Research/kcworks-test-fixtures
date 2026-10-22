#!/usr/bin/env bash
# Pull the shared fixtures submodule in every kcworks checkout except this one.
#
# Finds the kcworks monorepo by looking for site/kcworks/dependencies as a
# child of the current directory, then of each parent. No-ops if none is found.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Fixtures checkout that contains this script (exclude from updates).
THIS_FIXTURES="$(cd "$SCRIPT_DIR/.." && pwd -P)"

find_kcworks_root() {
  local dir
  dir="$(cd "$1" && pwd)"
  while true; do
    if [[ -d "$dir/site/kcworks/dependencies" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    local parent
    parent="$(dirname "$dir")"
    if [[ "$parent" == "$dir" ]]; then
      return 1
    fi
    dir="$parent"
  done
}

KCWORKS_ROOT=""
if KCWORKS_ROOT="$(find_kcworks_root "$(pwd)")"; then
  :
elif KCWORKS_ROOT="$(find_kcworks_root "$THIS_FIXTURES")"; then
  :
else
  echo "No kcworks monorepo found (no site/kcworks/dependencies); skipping peer updates."
  exit 0
fi

cd "$KCWORKS_ROOT"

ERRORS=0
SUCCESS_DIRS=()
FAILED_DIRS=()
SEEN=()

is_seen() {
  local candidate="$1"
  local s
  for s in "${SEEN[@]:-}"; do
    if [[ "$s" == "$candidate" ]]; then
      return 0
    fi
  done
  return 1
}

queue_dir() {
  local dir="$1"
  if [[ ! -e "$dir/.git" ]]; then
    return 0
  fi
  local resolved
  resolved="$(cd "$dir" && pwd -P)"
  if [[ "$resolved" == "$THIS_FIXTURES" ]]; then
    return 0
  fi
  if is_seen "$resolved"; then
    return 0
  fi
  SEEN+=("$resolved")
  update_dir "$resolved"
}

update_dir() {
  local dir="$1"
  if git -C "$dir" checkout main && git -C "$dir" pull; then
    SUCCESS_DIRS+=("$dir")
    echo "Successfully updated $dir"
  else
    echo "Failed to update $dir" >&2
    FAILED_DIRS+=("$dir")
    ((ERRORS++)) || true
  fi
}

# Parent (kcworks) fixtures instance.
queue_dir "tests/fixtures"

# Nested fixtures checkouts under dependency submodules.
while IFS= read -r dir; do
  [[ -z "$dir" ]] && continue
  queue_dir "$dir"
done < <(
  find site/kcworks/dependencies \
    -path '*/tests/fixtures' -type d -mindepth 3 -maxdepth 4 2>/dev/null || true
)

echo "Updated ${#SUCCESS_DIRS[@]} fixtures checkout(s):"
printf '  %s\n' "${SUCCESS_DIRS[@]:-}"

if ((ERRORS > 0)); then
  echo "Failed ${#FAILED_DIRS[@]} fixtures checkout(s):" >&2
  printf '  %s\n' "${FAILED_DIRS[@]}" >&2
  exit 1
fi
