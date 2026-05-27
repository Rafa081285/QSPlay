# Playwright Consumer Codespace

This folder verifies that the mirrored Playwright artifacts can be consumed from GitHub Packages without downloading Playwright dependencies from Maven Central.

## Required Codespaces secrets

- `GH_PACKAGES_USER`: optional if the Codespace is already authenticated with `gh`
- `GH_PACKAGES_TOKEN`: optional if the Codespace is already authenticated with `gh`

If those secrets are not set, the post-create step falls back to `gh auth token` and your signed-in GitHub identity.

The post-create step generates `~/.m2/settings.xml` and downloads the mirrored artifacts into the local Maven repository.

## Verify inside the codespace

```bash
cd codespaces/playwright-consumer
./run-check.sh
```

That command compiles and runs a small Java class directly against the jars installed from GitHub Packages.

## Optional Maven-only check

```bash
cd codespaces/playwright-consumer
mvn -s "$HOME/.m2/settings.xml" -f pom.xml -q dependency:tree
```

This settings file mirrors `central` to GitHub Packages. If Maven asks for plugins that are not mirrored, the command can still fail even though the Playwright dependency graph itself is complete.
