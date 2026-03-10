#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
METADATA_FILE="$ROOT/third-skills-metadata.json"

cd "$ROOT"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: $1 not installed"
    exit 1
  fi
}

require_cmd git
require_cmd jq
require_cmd rsync

REPO_COUNT=$(jq '.repos | length' "$METADATA_FILE")

get_json() {
  jq -r "$1" "$METADATA_FILE"
}

load_sparse_paths() {
  local index="$1"
  SPARSE_PATHS=()

  while IFS= read -r line; do
    SPARSE_PATHS+=("$line")
  done < <(jq -r ".repos[$index].sparse[]? // empty" "$METADATA_FILE")
}

sync_sparse_content() {
  local repo_dir="$1"
  local target_dir="$2"
  local sparse_path source_path destination_path parent_dir

  rm -rf "$target_dir"
  mkdir -p "$target_dir"

  for sparse_path in "${SPARSE_PATHS[@]}"; do
    source_path="$repo_dir/$sparse_path"
    destination_path="$target_dir/$sparse_path"

    if [[ ! -e "$source_path" ]]; then
      echo "ERROR: sparse path '$sparse_path' does not exist in $repo_dir"
      exit 1
    fi

    parent_dir=$(dirname "$destination_path")
    mkdir -p "$parent_dir"

    if [[ -d "$source_path" ]]; then
      rsync -a --delete "$source_path/" "$destination_path/"
    else
      rsync -a "$source_path" "$destination_path"
    fi
  done
}

update_commit_in_metadata() {
  local index="$1"
  local commit="$2"
  local tmp_file

  tmp_file=$(mktemp)
  jq \
    --arg commit "$commit" \
    ".repos[$index].commit = \$commit" \
    "$METADATA_FILE" >"$tmp_file"
  mv "$tmp_file" "$METADATA_FILE"
}

sync_repo() {
  local index="$1"
  local url branch path commit tmp_dir

  url=$(get_json ".repos[$index].url")
  branch=$(get_json ".repos[$index].branch")
  path=$(get_json ".repos[$index].path")

  load_sparse_paths "$index"
  if [[ ${#SPARSE_PATHS[@]} -eq 0 ]]; then
    echo "ERROR: .repos[$index].sparse must contain at least one path"
    exit 1
  fi

  tmp_dir=$(mktemp -d)

  echo "Syncing $path from $url@$branch"
  git clone \
    --depth 1 \
    --branch "$branch" \
    --single-branch \
    --filter=blob:none \
    --sparse \
    "$url" "$tmp_dir/repo" >/dev/null

  git -C "$tmp_dir/repo" sparse-checkout set --no-cone "${SPARSE_PATHS[@]}" >/dev/null

  sync_sparse_content "$tmp_dir/repo" "$path"

  commit=$(git -C "$tmp_dir/repo" rev-parse HEAD)
  update_commit_in_metadata "$index" "$commit"
  rm -rf "$tmp_dir"
}

for ((i = 0; i < REPO_COUNT; i++)); do
  sync_repo "$i"
done
