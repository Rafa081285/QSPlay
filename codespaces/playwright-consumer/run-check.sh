#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output_dir="$repo_root/target/classes"
source_file="$repo_root/src/main/java/example/CheckPlaywright.java"

jars=(
  "$HOME/.m2/repository/com/microsoft/playwright/playwright/1.53.0/playwright-1.53.0.jar"
  "$HOME/.m2/repository/com/microsoft/playwright/driver/1.53.0/driver-1.53.0.jar"
  "$HOME/.m2/repository/com/microsoft/playwright/driver-bundle/1.53.0/driver-bundle-1.53.0.jar"
  "$HOME/.m2/repository/com/google/code/gson/gson/2.12.1/gson-2.12.1.jar"
  "$HOME/.m2/repository/com/google/errorprone/error_prone_annotations/2.36.0/error_prone_annotations-2.36.0.jar"
  "$HOME/.m2/repository/org/opentest4j/opentest4j/1.3.0/opentest4j-1.3.0.jar"
)

for jar in "${jars[@]}"; do
  if [[ ! -f "$jar" ]]; then
    echo "Missing jar: $jar" >&2
    echo "Run ./install-playwright-from-gpr.sh first." >&2
    exit 1
  fi
done

classpath="$(IFS=:; echo "${jars[*]}")"
mkdir -p "$output_dir"

javac -cp "$classpath" -d "$output_dir" "$source_file"
java -cp "$output_dir:$classpath" example.CheckPlaywright