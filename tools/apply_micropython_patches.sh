#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
micropython_dir="$repo_root/lib/micropython"
expected_revision=78ff170de9e32c79db6e64d3e33d2bd60002bdcd
patch_dir="$repo_root/micropython/patches/v1.27.0"

if [[ ! -d "$micropython_dir/.git" && ! -f "$micropython_dir/.git" ]]; then
    echo "MicroPython submodule is not initialized: $micropython_dir" >&2
    exit 1
fi

actual_revision=$(git -C "$micropython_dir" rev-parse HEAD)
if [[ "$actual_revision" != "$expected_revision" ]]; then
    echo "Expected MicroPython $expected_revision, got $actual_revision" >&2
    exit 1
fi

for patch in "$patch_dir"/*.patch; do
    git -C "$micropython_dir" apply --check "$patch"
    git -C "$micropython_dir" apply "$patch"
done
