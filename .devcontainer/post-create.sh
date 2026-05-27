#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
consumer_dir="$repo_root/codespaces/playwright-consumer"
template="$consumer_dir/settings.github-packages.xml.template"
target_settings="$HOME/.m2/settings.xml"

mkdir -p "$HOME/.m2"

if [[ -n "${GH_PACKAGES_USER:-}" && -n "${GH_PACKAGES_TOKEN:-}" ]]; then
  sed \
    -e "s|__GH_USER__|${GH_PACKAGES_USER}|g" \
    -e "s|__GH_TOKEN__|${GH_PACKAGES_TOKEN}|g" \
    -e "s|__MIRROR_REPO__|${PLAYWRIGHT_MIRROR_REPO:-Rafa081285/QSPlay}|g" \
    "$template" > "$target_settings"

  echo "Generated $target_settings for GitHub Packages."
  echo "Installing mirrored Playwright artifacts into the local Maven repository..."
  bash "$consumer_dir/install-playwright-from-gpr.sh"
elif command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh_user="${GITHUB_ACTOR:-$(gh api user --jq .login)}"
  gh_token="$(gh auth token)"
  sed \
    -e "s|__GH_USER__|${gh_user}|g" \
    -e "s|__GH_TOKEN__|${gh_token}|g" \
    -e "s|__MIRROR_REPO__|${PLAYWRIGHT_MIRROR_REPO:-Rafa081285/QSPlay}|g" \
    "$template" > "$target_settings"

  echo "Generated $target_settings from gh auth."
  echo "Installing mirrored Playwright artifacts into the local Maven repository..."
  bash "$consumer_dir/install-playwright-from-gpr.sh"
else
  cat <<'EOF'
Codespaces secrets GH_PACKAGES_USER and GH_PACKAGES_TOKEN were not found, and gh auth is not available.
Create them in the repository or account Codespaces secrets, or sign in with gh inside the codespace.
EOF
fi

cat <<'EOF'

Next steps inside the codespace:
  cd codespaces/playwright-consumer
  ./run-check.sh

Optional strict Maven check:
  mvn -s $HOME/.m2/settings.xml -f pom.xml -q dependency:tree

Note: the strict Maven check may still require mirrored Maven plugins if you want zero access to Maven Central.
EOF