#!/usr/bin/env bash
set -euo pipefail

mirror_repo="${PLAYWRIGHT_MIRROR_REPO:-Rafa081285/QSPlay}"
coords_file="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/playwright-1.53.0.coords.txt"
m2_repo="${M2_REPO:-$HOME/.m2/repository}"

if [[ -z "${GH_PACKAGES_USER:-}" || -z "${GH_PACKAGES_TOKEN:-}" ]]; then
  echo "GH_PACKAGES_USER and GH_PACKAGES_TOKEN are required." >&2
  exit 1
fi

mkdir -p "$m2_repo"

download_artifact() {
  local group_id="$1"
  local artifact_id="$2"
  local version="$3"
  local extension="$4"
  local group_path target_dir target_file url

  group_path="${group_id//./\/}"
  target_dir="$m2_repo/$group_path/$artifact_id/$version"
  target_file="$target_dir/$artifact_id-$version.$extension"
  url="https://maven.pkg.github.com/$mirror_repo/$group_path/$artifact_id/$version/$artifact_id-$version.$extension"

  mkdir -p "$target_dir"
  curl --fail --silent --show-error --location \
    --retry 3 \
    --user "$GH_PACKAGES_USER:$GH_PACKAGES_TOKEN" \
    "$url" \
    --output "$target_file"
}

while IFS=: read -r group_id artifact_id version packaging; do
  [[ -n "$group_id" ]] || continue

  download_artifact "$group_id" "$artifact_id" "$version" "pom"
  if [[ "$packaging" == "jar" ]]; then
    download_artifact "$group_id" "$artifact_id" "$version" "jar"
  fi
done < "$coords_file"

echo "Installed mirrored Playwright artifacts into $m2_repo"