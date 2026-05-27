# GitHub Packages for Maven (Playwright mirror)

This repository includes a workflow to mirror Playwright artifacts into GitHub Packages.

## 1) Publish packages (one-time per version)

Run the workflow:

- `.github/workflows/bootstrap_github_packages_playwright.yml`

Inputs:

- `playwrightVersion`: version to mirror (default `1.53.0`)
- `targetRepository`: destination repository in GitHub Packages (for example `Rafa081285/kafdrop`)

Recommended secret:

- `GH_PACKAGES_TOKEN`: fine-grained token or PAT with package write permissions on the target repository.

If `GH_PACKAGES_TOKEN` is not present, the workflow falls back to `GITHUB_TOKEN`.

It publishes these coordinates to GitHub Packages:

- `com.microsoft.playwright:playwright:<version>`
- `com.microsoft.playwright:driver:<version>`
- `com.microsoft.playwright:driver-bundle:<version>`

At the moment the workflow also mirrors the transitive Playwright dependency closure plus the parent and imported POMs needed by those artifacts.

## 2) Maven repository configuration (consumer project)

Add this repository to `pom.xml`:

```xml
<repositories>
  <repository>
    <id>github</id>
    <url>https://maven.pkg.github.com/OWNER/REPO</url>
  </repository>
</repositories>
```

Replace `OWNER/REPO` with the repository that published the packages.

For your organization, this will typically be `Rafa081285/<repo>`.

## 3) settings.xml for local runs or non-GitHub CI

Use `${user.home}/.m2/settings.xml`:

```xml
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 https://maven.apache.org/xsd/settings-1.0.0.xsd">
  <servers>
    <server>
      <id>github</id>
      <username>GITHUB_USERNAME</username>
      <password>GITHUB_TOKEN_OR_PAT</password>
    </server>
  </servers>
</settings>
```

## 4) GitHub Actions consumers

In GitHub Actions, configure Maven auth with `actions/setup-java`:

```yaml
- uses: actions/setup-java@v5
  with:
    distribution: temurin
    java-version: "17"
    server-id: github
    server-username: GITHUB_ACTOR
    server-password: GITHUB_TOKEN
```

Then run Maven normally.

## 5) Codespaces smoke test

This repository includes a ready-to-run Codespaces sample under `codespaces/playwright-consumer`.

Required Codespaces secrets:

- `GH_PACKAGES_USER`
- `GH_PACKAGES_TOKEN`

When the codespace starts, `.devcontainer/post-create.sh` generates `~/.m2/settings.xml` and installs the mirrored Playwright artifacts into the local Maven repository directly from GitHub Packages.

To verify the mirrored jars without touching Maven Central for Playwright itself:

```bash
cd codespaces/playwright-consumer
./run-check.sh
```

If you want a strict Maven-only test, use:

```bash
mvn -s "$HOME/.m2/settings.xml" -f codespaces/playwright-consumer/pom.xml -q dependency:tree
```

Note: Azure Artifacts upstream caching is broader than this GitHub Packages mirror. A strict Maven-only run may still require Maven plugin artifacts that are not part of the Playwright dependency graph.
