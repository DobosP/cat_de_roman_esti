#!/usr/bin/env bash
# Construct a native executable allowlist without modifying installed runtimes.
set -euo pipefail
native_destination="$(realpath -m "${1:?Supply the native path directory under workspace scratch}")"
case "$native_destination" in "$(realpath -m "$HOME/work/_temp")/"*) ;; *) printf 'Native PATH must be under ~/work/_temp/\n' >&2; exit 2;; esac
mkdir -p "$native_destination"
# All lookups occur before PATH replacement; no credentials/environment files are read.
for native_command in bash sh env git go gofmt node npm npx gcc cc as ld mkdir dirname date realpath readlink ln rm mv cp cat chmod tee grep sed tail head find sort xargs uname seq sleep curl docker cksum tar gzip; do
  native_executable="$(command -v "$native_command" || true)"
  if [ -n "$native_executable" ]; then ln -sf "$native_executable" "$native_destination/$native_command"; fi
done
if PATH="$native_destination" command -v python python3 python3.12 python3.14 rustc cargo; then
  printf 'Native PATH unexpectedly exposes a legacy interpreter\n' >&2; exit 1
fi
printf '%s\n' "$native_destination"
