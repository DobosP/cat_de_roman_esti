#!/usr/bin/env bash
set -euo pipefail
export GIT_NO_LAZY_FETCH=1 GIT_OPTIONAL_LOCKS=0

if [[ $# -ne 1 || $1 == -* ]]; then
  printf 'Usage: %s WORKTREE\n' "$0" >&2
  exit 2
fi
root=$(cd -- "$1" && pwd -P)
if [[ $(git -C "$root" rev-parse --show-toplevel) != "$root" ]]; then
  printf 'Preflight requires the worktree root.\n' >&2
  exit 2
fi
disk=$(df -Pk "$root" "${TMPDIR:-/tmp}") || exit 2
printf '%s\n' "$disk"

# Read only the committed literal values. Never source .gate.env.
gate_env=$(git -C "$root" show HEAD:.gate.env)
tag=$(printf '%s\n' "$gate_env" | sed -n 's/^TOOLCHAIN_IMAGE=//p')
pin=$(printf '%s\n' "$gate_env" | sed -n 's/^TOOLCHAIN_DIGEST=//p')
if [[ ! $tag =~ ^roedu-toolchain:[a-z0-9][a-z0-9._-]{0,127}$ ||
      ! $pin =~ ^sha256:[a-f0-9]{64}$ ]]; then
  printf 'Preflight requires a pinned toolchain in committed .gate.env.\n' >&2
  exit 2
fi

# Explicit local Unix socket. Never contact a configured remote Docker context.
socket=${CAT_LANDING_DOCKER_SOCKET:-/var/run/docker.sock}
if [[ $socket != /* || ! -S $socket ]]; then
  printf 'Local Docker Unix socket unavailable.\n' >&2
  exit 1
fi
docker_local() { env -u DOCKER_CONTEXT -u DOCKER_HOST docker --host "unix://$socket" "$@"; }

rc=0
if id=$(docker_local image inspect --format '{{.Id}}' "$tag") && [[ $id == "$pin" ]]; then
  printf 'Pinned toolchain %s %s\n' "$tag" "$id"
else
  printf 'Pinned toolchain unavailable or mismatched for %s.\n' "$tag" >&2
  rc=1
fi

# A Compose project collision is actionable evidence for the operator. Listing
# by exact project label avoids sweeping sibling repos or worktrees.
repo=$(basename -- "$(dirname -- "$root")")
slug=$(basename -- "$root")
if [[ ! $repo =~ ^[a-z0-9_-]+$ || ! $slug =~ ^[a-z0-9_-]+$ ]]; then
  printf 'Cannot identify a portable gate project for this worktree.\n' >&2
  exit 2
fi
path_hash=$(python3 -IB -c 'import hashlib, os, sys; print(hashlib.sha256(os.fsencode(sys.argv[1])).hexdigest()[:12])' "$root")
project="gate-$repo-$slug-$path_hash"
if networks=$(docker_local network ls --filter "label=com.docker.compose.project=$project" --format '{{.Name}}'); then
  printf 'Docker networks for %s\n%s\n' "$project" "${networks:-none}"
else
  printf 'Docker network listing unavailable.\n' >&2
  rc=1
fi
exit "$rc"
