#!/usr/bin/env python3

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def repo_path(repo_local: pathlib.Path, group_id: str, artifact_id: str, version: str, extension: str) -> pathlib.Path:
    return repo_local.joinpath(*group_id.split("."), artifact_id, version, f"{artifact_id}-{version}.{extension}")


def parse_tree(tree_file: pathlib.Path) -> set[tuple[str, str, str]]:
    coords: set[tuple[str, str, str]] = set()
    pattern = re.compile(
        r"([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):(jar|pom|war|aar|bundle|eclipse-plugin):([^: \[]+):([A-Za-z0-9_.-]+)"
    )

    with tree_file.open(encoding="utf-8") as handle:
        for raw_line in handle:
            match = pattern.search(raw_line)
            if not match:
                continue

            group_id, artifact_id, packaging, version, scope = match.groups()
            if group_id.startswith(("org.apache.maven.plugins", "org.codehaus.mojo")):
                continue
            if scope == "test":
                continue
            if packaging == "pom" and artifact_id.endswith("-plugin"):
                continue

            coords.add((group_id, artifact_id, version))

    return coords


def parent_coord_from_pom(pom_file: pathlib.Path) -> tuple[str, str, str] | None:
    try:
        root = ET.parse(pom_file).getroot()
    except ET.ParseError:
        return None

    namespace = {"m": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    parent = root.find("m:parent", namespace) if namespace else root.find("parent")
    if parent is None:
        return None

    group_node = parent.find("m:groupId", namespace) if namespace else parent.find("groupId")
    artifact_node = parent.find("m:artifactId", namespace) if namespace else parent.find("artifactId")
    version_node = parent.find("m:version", namespace) if namespace else parent.find("version")
    if group_node is None or artifact_node is None or version_node is None:
        return None

    return (group_node.text.strip(), artifact_node.text.strip(), version_node.text.strip())


def resolve_command(args: argparse.Namespace) -> int:
    workdir = pathlib.Path(args.workdir)
    repo_local = pathlib.Path(args.repo_local)
    workdir.mkdir(parents=True, exist_ok=True)
    repo_local.mkdir(parents=True, exist_ok=True)

    pom_file = workdir / "pom.xml"
    tree_file = workdir / "tree.txt"
    coords_file = workdir / "coords.txt"

    pom_file.write_text(
        f'''<project xmlns="http://maven.apache.org/POM/4.0.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>mirror.bootstrap</groupId>
  <artifactId>playwright-mirror-bootstrap</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>com.microsoft.playwright</groupId>
      <artifactId>playwright</artifactId>
      <version>{args.version}</version>
    </dependency>
  </dependencies>
</project>
''',
        encoding="utf-8",
    )

    subprocess.run(
        [
            "mvn",
            "-B",
            "-q",
            "-f",
            str(pom_file),
            f"-Dmaven.repo.local={repo_local}",
            "dependency:go-offline",
            "dependency:tree",
            f"-DoutputFile={tree_file}",
            "-DappendOutput=false",
        ],
        check=True,
    )

    direct_coords = parse_tree(tree_file)
    resolved_coords: set[tuple[str, str, str]] = set()
    queue = list(direct_coords)

    while queue:
        group_id, artifact_id, version = queue.pop()
        coord = (group_id, artifact_id, version)
        if coord in resolved_coords:
            continue

        pom = repo_path(repo_local, group_id, artifact_id, version, "pom")
        if not pom.exists():
            continue

        resolved_coords.add(coord)
        parent_coord = parent_coord_from_pom(pom)
        if parent_coord is not None:
            parent_pom = repo_path(repo_local, parent_coord[0], parent_coord[1], parent_coord[2], "pom")
            if parent_pom.exists() and parent_coord not in resolved_coords:
                queue.append(parent_coord)

    coords_file.write_text("\n".join(f"{g}:{a}:{v}" for g, a, v in sorted(resolved_coords)) + "\n", encoding="utf-8")
    print(f"Prepared {len(resolved_coords)} Maven coordinates for publishing", file=sys.stderr)
    return 0


def publish_command(args: argparse.Namespace) -> int:
    coords_file = pathlib.Path(args.coords_file)
    repo_local = pathlib.Path(args.repo_local)
    target_url = args.target_url

    coords: list[tuple[str, str, str]] = []
    with coords_file.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            group_id, artifact_id, version = raw_line.split(":", 2)
            coords.append((group_id, artifact_id, version))

    for group_id, artifact_id, version in coords:
        artifact_dir = repo_path(repo_local, group_id, artifact_id, version, "pom").parent
        jar_file = artifact_dir / f"{artifact_id}-{version}.jar"
        pom_file = artifact_dir / f"{artifact_id}-{version}.pom"

        if jar_file.exists():
            subprocess.run(
                [
                    "mvn",
                    "--batch-mode",
                    "deploy:deploy-file",
                    "-DrepositoryId=github",
                    f"-Durl={target_url}",
                    f"-DgroupId={group_id}",
                    f"-DartifactId={artifact_id}",
                    f"-Dversion={version}",
                    "-Dpackaging=jar",
                    f"-Dfile={jar_file}",
                    f"-DpomFile={pom_file}",
                    "-DgeneratePom=false",
                ],
                check=True,
            )
            continue

        if pom_file.exists():
            subprocess.run(
                [
                    "mvn",
                    "--batch-mode",
                    "deploy:deploy-file",
                    "-DrepositoryId=github",
                    f"-Durl={target_url}",
                    f"-DgroupId={group_id}",
                    f"-DartifactId={artifact_id}",
                    f"-Dversion={version}",
                    "-Dpackaging=pom",
                    f"-Dfile={pom_file}",
                    "-DgeneratePom=false",
                ],
                check=True,
            )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--version", required=True)
    resolve.add_argument("--workdir", required=True)
    resolve.add_argument("--repo-local", required=True)
    resolve.set_defaults(func=resolve_command)

    publish = subparsers.add_parser("publish")
    publish.add_argument("--coords-file", required=True)
    publish.add_argument("--repo-local", required=True)
    publish.add_argument("--target-url", required=True)
    publish.set_defaults(func=publish_command)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())