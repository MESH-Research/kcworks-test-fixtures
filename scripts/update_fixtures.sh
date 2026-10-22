#!/usr/bin/env bash
# Pull the shared fixtures submodule in every kcworks checkout except this one.
#
# Finds the kcworks monorepo by looking for site/kcworks/dependencies as a
# child of the current directory, then of each parent. No-ops if none is found.
#
# For each peer fixtures checkout whose origin is kcworks-test-fixtures:
#   1. fetch origin and hard-reset main to origin/main (fails if dirty unless
#      UPDATE_FIXTURES_FORCE=1)
#   2. stage the updated gitlink in the enclosing git repo (dependency package
#      or kcworks monorepo) so the parent pointer matches the pulled SHA
#
# The script does not commit parent repos; commit those submodule bumps yourself.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Fixtures checkout that contains this script (exclude from updates).
THIS_FIXTURES="$(cd "$SCRIPT_DIR/.." && pwd -P)"
FORCE="${UPDATE_FIXTURES_FORCE:-0}"
EXPECTED_REMOTE_NEEDLE="kcworks-test-fixtures"

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

# Nearest ancestor (including dir) that has its own .git (file or directory).
enclosing_git_root() {
  local dir
  dir="$(cd "$1" && pwd -P)"
  while true; do
    if [[ -e "$dir/.git" ]]; then
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

is_fixtures_remote() {
  local dir="$1"
  local url
  url="$(git -C "$dir" remote get-url origin 2>/dev/null || true)"
  [[ "$url" == *"$EXPECTED_REMOTE_NEEDLE"* ]]
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
SKIPPED_DIRS=()
STAGED_PARENTS=()
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

record_skip() {
  local dir="$1"
  local reason="$2"
  SKIPPED_DIRS+=("$dir ($reason)")
  echo "Skipping $dir ($reason)"
}

queue_dir() {
  local dir="$1"
  if [[ ! -e "$dir/.git" ]]; then
    record_skip "$dir" "no .git"
    return 0
  fi
  local resolved
  resolved="$(cd "$dir" && pwd -P)"
  if [[ "$resolved" == "$THIS_FIXTURES" ]]; then
    record_skip "$resolved" "source checkout"
    return 0
  fi
  if is_seen "$resolved"; then
    return 0
  fi
  if ! is_fixtures_remote "$resolved"; then
    record_skip "$resolved" "origin is not $EXPECTED_REMOTE_NEEDLE"
    return 0
  fi
  SEEN+=("$resolved")
  update_dir "$resolved"
}

stage_parent_gitlink() {
  local fixtures_dir="$1"
  local parent_root path_from_parent
  # Walk from the parent of the fixtures dir so we stage in the superproject,
  # not inside the fixtures submodule itself.
  if ! parent_root="$(enclosing_git_root "$(dirname "$fixtures_dir")")"; then
    echo "Warning: no enclosing git root above $fixtures_dir; gitlink not staged" >&2
    return 0
  fi
  path_from_parent="${fixtures_dir#"$parent_root"/}"
  if [[ "$path_from_parent" == "$fixtures_dir" ]]; then
    echo "Warning: could not relativize $fixtures_dir under $parent_root" >&2
    return 0
  fi
  if git -C "$parent_root" add "$path_from_parent"; then
    STAGED_PARENTS+=("$parent_root:$path_from_parent")
    echo "Staged gitlink $path_from_parent in $parent_root (commit the parent repo separately)"
  else
    echo "Warning: failed to stage $path_from_parent in $parent_root" >&2
  fi
}

update_dir() {
  local dir="$1"
  local dirty
  dirty="$(git -C "$dir" status --porcelain 2>/dev/null || true)"
  if [[ -n "$dirty" && "$FORCE" != "1" ]]; then
    echo "Failed to update $dir (dirty working tree; set UPDATE_FIXTURES_FORCE=1 to reset --hard)" >&2
    FAILED_DIRS+=("$dir")
    ((ERRORS++)) || true
    return 0
  fi

  if git -C "$dir" fetch origin \
    && git -C "$dir" checkout main \
    && git -C "$dir" reset --hard origin/main; then
    SUCCESS_DIRS+=("$dir")
    echo "Successfully updated $dir -> $(git -C "$dir" rev-parse --short HEAD)"
    stage_parent_gitlink "$dir"
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
if ((${#SUCCESS_DIRS[@]} > 0)); then
  printf '  %s\n' "${SUCCESS_DIRS[@]}"
else
  echo "  (none)"
fi

if ((${#STAGED_PARENTS[@]} > 0)); then
  echo "Staged parent gitlink(s) (commit these repos when ready):"
  printf '  %s\n' "${STAGED_PARENTS[@]}"
fi

if ((${#SKIPPED_DIRS[@]} > 0)); then
  echo "Skipped ${#SKIPPED_DIRS[@]} path(s):"
  printf '  %s\n' "${SKIPPED_DIRS[@]}"
fi

if ((ERRORS > 0)); then
  echo "Failed ${#FAILED_DIRS[@]} fixtures checkout(s):" >&2
  printf '  %s\n' "${FAILED_DIRS[@]}" >&2
  exit 1
fi
