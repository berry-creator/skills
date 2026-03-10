#!/usr/bin/env bash
set -euo pipefail

########################################
# Locate repo root
########################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
CONFIG="$ROOT/deps.json"

cd "$ROOT"

########################################
# Check dependency
########################################

if ! command -v jq >/dev/null; then
  echo "ERROR: jq not installed"
  exit 1
fi

########################################
# Read config
########################################

REPO_COUNT=$(jq '.repos | length' "$CONFIG")

get_json() {
  jq -r "$1" "$CONFIG"
}

########################################
# Configure sparse checkout
########################################

setup_sparse() {
  local path="$1"
  local index="$2"
  local sparse_count
  sparse_count=$(get_json ".repos[$index].sparse | length")

  if [[ "$sparse_count" == "0" ]]; then
    return
  fi

  pushd "$path" >/dev/null
  git sparse-checkout init --cone
  local dirs
  dirs=$(get_json ".repos[$index].sparse[]" | tr '\n' ' ')
  git sparse-checkout set $dirs
  popd >/dev/null
}

########################################
# Configure commit lock
########################################

checkout_commit() {
  local path="$1"
  local commit="$2"

  if [[ -n "$commit" && "$commit" != "null" ]]; then
    git -C "$path" checkout "$commit"
  fi
}

########################################
# Init repo
########################################

init_repo() {
  local index="$1"
  local url path depth commit

  url=$(get_json ".repos[$index].url")
  path=$(get_json ".repos[$index].path")
  depth=$(get_json ".repos[$index].depth // empty")
  commit=$(get_json ".repos[$index].commit // empty")

  if [[ ! -d "$path" ]]; then
    echo "Adding submodule $path"

    git submodule add "$url" "$path"
  fi

  if [[ -n "$depth" ]]; then
    git submodule update --init --depth "$depth" "$path"
  else
    git submodule update --init "$path"
  fi

  checkout_commit "$path" "$commit"

  setup_sparse "$path" "$index"
}

########################################
# Update repo
########################################

update_repo() {
  local index="$1"
  local path
  path=$(get_json ".repos[$index].path")

  echo "Updating $path"

  git submodule update --remote "$path"

  setup_sparse "$path" "$index"
}

########################################
# Lock commit
########################################

lock_repos() {
  local tmp
  tmp=$(mktemp)
  cp "$CONFIG" "$tmp"

  for ((i = 0; i < REPO_COUNT; i++)); do
    local path
    path=$(get_json ".repos[$i].path")

    if [[ -d "$path/.git" ]]; then
      local commit
      commit=$(git -C "$path" rev-parse HEAD)
      local tmp2
      tmp2=$(mktemp)
      jq ".repos[$i].commit=\"$commit\"" "$tmp" >"$tmp2"
      mv "$tmp2" "$tmp"
    fi
  done

  mv "$tmp" "$CONFIG"
  echo "deps.json updated"
}

########################################
# Status
########################################

status_repos() {
  printf "%-35s %-12s %-12s\n" "PATH" "LOCAL" "LOCKED"

  for ((i = 0; i < REPO_COUNT; i++)); do
    local path
    path=$(get_json ".repos[$i].path")
    local locked
    locked=$(get_json ".repos[$i].commit // \"-\"")
    local local_commit

    if [[ -d "$path/.git" ]]; then
      local_commit=$(git -C "$path" rev-parse --short HEAD)
    else
      local_commit="-"
    fi

    printf "%-35s %-12s %-12s\n" "$path" "$local_commit" "$locked"
  done
}

########################################
# Clean
########################################

clean_repos() {
  echo "Cleaning third_party..."
  rm -rf "$ROOT/third_party"/*
  rm -rf "$ROOT/.git/modules"/* 2>/dev/null || true
}

########################################
# Sync
########################################

sync_repos() {
  git submodule sync
  git submodule update --init --recursive
}

########################################
# Main
########################################

MODE=${1:-}

case "$MODE" in
  init)
    for ((i = 0; i < REPO_COUNT; i++)); do
      init_repo "$i"
    done
    ;;
  update)
    for ((i = 0; i < REPO_COUNT; i++)); do
      update_repo "$i"
    done
    ;;
  lock)
    lock_repos
    ;;
  status)
    status_repos
    ;;
  clean)
    clean_repos
    ;;
  sync)
    sync_repos
    ;;

  *)
    echo "Usage:"
    echo "  ./deps.sh init"
    echo "  ./deps.sh update"
    echo "  ./deps.sh lock"
    echo "  ./deps.sh status"
    echo "  ./deps.sh clean"
    echo "  ./deps.sh sync"
    exit 1
    ;;

esac