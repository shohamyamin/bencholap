"""Resolve user-supplied Trino target strings into runnable docker images.

Accepted forms (published images are preferred; nothing is built unless needed):

  484 | release:484 | trino:484          official image trinodb/trino:484
  latest                               newest numeric release tag on Docker Hub
  image:<ref>                          any image, e.g. image:ghcr.io/me/trino:pr-123
  tarball:<url-or-path>                trino-server-*.tar.gz overlaid on an official image
  github:<owner>/<repo>@<ref>          fork + branch/tag/commit
  git:<clone-url>@<ref>                any git repository + ref
  https://github.com/<owner>/<repo>/tree/<ref>   same, pasted from the browser
  pr:<n> | pr:<owner>/<repo>#<n>         head commit of a pull request (default repo trinodb/trino)
  pr-base:<n>                          merge base of that pull request (the fair baseline)

A git target whose repository is trinodb/trino and whose ref is a release tag resolves to
the published image. Anything else is built from source once and cached by commit.
"""

from __future__ import annotations

import os
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

import requests

from ...util import home, log, run
from ..base import ResolvedTarget

OFFICIAL_IMAGE = os.environ.get("BENCHOLAP_TRINO_IMAGE_REPO", "trinodb/trino")
UPSTREAM_REPOS = {"trinodb/trino"}


def version_number(version: str | None) -> int | None:
    m = re.match(r"^(\d+)", version or "")
    return int(m.group(1)) if m else None


def release_tags() -> list[int]:
    tags: list[int] = []
    url = f"https://hub.docker.com/v2/repositories/{OFFICIAL_IMAGE}/tags?page_size=100"
    for _ in range(3):  # newest ~300 tags is plenty
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        tags += [int(t["name"]) for t in data["results"] if t["name"].isdigit()]
        url = data.get("next")
        if not url:
            break
    return sorted(set(tags))


def latest_release() -> int:
    return release_tags()[-1]


def _image_exists_locally(image: str) -> bool:
    return run(["docker", "image", "inspect", image], check=False, capture=True).returncode == 0


def ensure_image(image: str) -> None:
    if not _image_exists_locally(image):
        log.info("pulling %s", image)
        run(["docker", "pull", "-q", image], capture=True)


def image_digest(image: str) -> str | None:
    out = run(["docker", "image", "inspect", "--format", "{{json .RepoDigests}} {{.Id}}", image],
              capture=True, check=False)
    return out.stdout.strip() if out.returncode == 0 else None


def image_trino_version(image: str) -> str | None:
    """Read the version from the trino-main jar name inside the image."""
    out = run(["docker", "run", "--rm", "--entrypoint", "sh", image, "-c",
               "ls /usr/lib/trino/lib | grep -E '^trino-main-.*\\.jar$'"], capture=True, check=False)
    m = re.search(r"trino-main-(.+)\.jar", out.stdout or "")
    return m.group(1) if m else None


def _release(n: int, spec: str) -> ResolvedTarget:
    image = f"{OFFICIAL_IMAGE}:{n}"
    ensure_image(image)
    return ResolvedTarget("trino", spec, image, str(n), n,
                          {"kind": "release", "image": image, "digest": image_digest(image)})


def _parse_git(spec: str) -> tuple[str, str, str | None] | None:
    """Return (clone_url, ref, owner/repo) for git-like specs."""
    m = re.match(r"^https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/(?:tree|commit)/(.+)$", spec)
    if m:
        return f"https://github.com/{m.group(1)}.git", m.group(2), m.group(1)
    if spec.startswith("github:"):
        repo, _, ref = spec[len("github:"):].partition("@")
        return f"https://github.com/{repo}.git", ref or "master", repo
    if spec.startswith("git:"):
        url, _, ref = spec[len("git:"):].rpartition("@")
        if not url:
            url, ref = ref, "master"
        m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
        return url, ref, m.group(1) if m else None
    return None


def _github_get(path: str) -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"https://api.github.com/{path}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def _pull_request(spec: str) -> tuple[str, int]:
    """'pr:123' (trinodb/trino) or 'pr:owner/repo#123'."""
    body = spec.split(":", 1)[1]
    repo, _, num = body.rpartition("#")
    return (repo or "trinodb/trino"), int(num)


def resolve(spec: str) -> ResolvedTarget:
    s = spec.strip()
    if s.startswith(("pr:", "pr-base:")):
        repo, num = _pull_request(s)
        pr = _github_get(f"repos/{repo}/pulls/{num}")
        if s.startswith("pr:"):
            url, sha = pr["head"]["repo"]["clone_url"], pr["head"]["sha"]
        else:
            cmp = _github_get(f"repos/{repo}/compare/{pr['base']['sha']}...{pr['head']['sha']}")
            url, sha = pr["base"]["repo"]["clone_url"], cmp["merge_base_commit"]["sha"]
        t = _from_source(url, sha, spec)
        t.source.update({"pull_request": f"{repo}#{num}", "pr_title": pr.get("title")})
        return t
    if s == "latest":
        return _release(latest_release(), spec)
    m = re.match(r"^(?:release:|trino:)?(\d+)$", s)
    if m:
        return _release(int(m.group(1)), spec)
    if s.startswith("image:"):
        image = s[len("image:"):]
        ensure_image(image)
        version = image_trino_version(image)
        return ResolvedTarget("trino", spec, image, version or "unknown", version_number(version),
                              {"kind": "image", "image": image, "digest": image_digest(image)})
    if s.startswith("tarball:"):
        return _from_tarball(s[len("tarball:"):], spec)
    git = _parse_git(s)
    if git:
        url, ref, repo = git
        if repo in UPSTREAM_REPOS and re.fullmatch(r"\d+", ref):
            return _release(int(ref), spec)
        return _from_source(url, ref, spec)
    raise ValueError(f"cannot understand Trino target {spec!r}; see `bencholap targets --help`")


# ---------------------------------------------------------------------------------------
# Overlay builds: put a custom trino-server (lib + plugin) on top of an official image so
# the JDK, launcher and default configs stay those of a real release.

def _cache() -> Path:
    p = home() / "cache" / "trino"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _base_image_for(version: str | None) -> str:
    """Closest release not newer than the build (N-SNAPSHOT builds on release N-1)."""
    n = version_number(version)
    tags = release_tags()
    if n is not None:
        older = [t for t in tags if t < n or (t == n and "SNAPSHOT" not in (version or ""))]
        if older:
            return f"{OFFICIAL_IMAGE}:{older[-1]}"
    return f"{OFFICIAL_IMAGE}:{tags[-1]}"


def _overlay(server_dir: Path, version: str, tag: str, base_image: str | None) -> str:
    base = base_image or os.environ.get("BENCHOLAP_TRINO_BASE_IMAGE") or _base_image_for(version)
    ensure_image(base)
    ctx = server_dir.parent
    (ctx / "Dockerfile").write_text(
        f"FROM {base}\n"
        "USER root\n"
        "RUN rm -rf /usr/lib/trino/lib /usr/lib/trino/plugin\n"
        f"COPY {server_dir.name}/lib /usr/lib/trino/lib\n"
        f"COPY {server_dir.name}/plugin /usr/lib/trino/plugin\n"
        "USER trino:trino\n"
    )
    log.info("building overlay image %s on %s", tag, base)
    run(["docker", "build", "-q", "-t", tag, str(ctx)], capture=True)
    return base


def _extract_server(tarball: Path, dest: Path) -> tuple[Path, str]:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with tarfile.open(tarball) as tar:
        tar.extractall(dest, filter="data")
    roots = [p for p in dest.iterdir() if p.is_dir() and p.name.startswith("trino-server-")]
    if len(roots) != 1:
        raise RuntimeError(f"{tarball} does not look like a trino-server tarball")
    return roots[0], roots[0].name[len("trino-server-"):]


MVND_VERSION = os.environ.get("BENCHOLAP_MVND_VERSION", "1.0.6")


def _mvnd() -> Path | None:
    """Download (once) the mvnd distribution for this architecture; None if unavailable."""
    arch = {"x86_64": "amd64", "aarch64": "aarch64", "arm64": "aarch64"}.get(os.uname().machine)
    if not arch or os.environ.get("BENCHOLAP_NO_MVND"):
        return None
    name = f"maven-mvnd-{MVND_VERSION}-linux-{arch}"
    root = _cache() / "mvnd"
    home_dir = root / name
    if (home_dir / "bin" / "mvnd").exists():
        return home_dir
    try:
        root.mkdir(parents=True, exist_ok=True)
        archive = root / f"{name}.tar.gz"
        for mirror in ("https://downloads.apache.org", "https://archive.apache.org/dist"):
            try:
                urllib.request.urlretrieve(f"{mirror}/maven/mvnd/{MVND_VERSION}/{name}.tar.gz", archive)
                break
            except OSError:
                continue
        with tarfile.open(archive) as tar:
            tar.extractall(root, filter="data")
        archive.unlink()
        return home_dir if (home_dir / "bin" / "mvnd").exists() else None
    except Exception as e:  # noqa: BLE001 - fall back to ./mvnw
        log.warning("mvnd not available (%s); using ./mvnw", e)
        return None


def _from_tarball(location: str, spec: str, base_image: str | None = None) -> ResolvedTarget:
    work = _cache() / "tarball" / re.sub(r"[^A-Za-z0-9._-]", "_", location)[-80:]
    work.mkdir(parents=True, exist_ok=True)
    local = work / "trino-server.tar.gz"
    if re.match(r"^https?://", location):
        if not local.exists():
            log.info("downloading %s", location)
            urllib.request.urlretrieve(location, local)
    else:
        local = Path(location).expanduser().resolve()
    server_dir, version = _extract_server(local, work / "ctx")
    tag = f"bencholap/trino:tarball-{version}-{abs(hash(location)) % 10**8}"
    base = _overlay(server_dir, version, tag, base_image)
    return ResolvedTarget("trino", spec, tag, version, version_number(version),
                          {"kind": "tarball", "location": location, "base_image": base, "image": tag})


def _from_source(url: str, ref: str, spec: str) -> ResolvedTarget:
    out = run(["git", "ls-remote", url, ref, f"refs/heads/{ref}", f"refs/tags/{ref}"], capture=True)
    lines = [ln.split() for ln in out.stdout.splitlines() if ln.strip()]
    if lines:
        commit = lines[0][0]
    elif re.fullmatch(r"[0-9a-f]{7,40}", ref):
        commit = ref
    else:
        raise ValueError(f"ref {ref!r} not found in {url}")
    tag = f"bencholap/trino:git-{commit[:12]}"
    source = {"kind": "git", "repo": url, "ref": ref, "commit": commit, "image": tag}
    if _image_exists_locally(tag):
        version = image_trino_version(tag)
        return ResolvedTarget("trino", spec, tag, version or "unknown", version_number(version), source)

    src = _cache() / "src" / commit[:12]
    if not (src / "pom.xml").exists():
        src.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q", str(src)])
        run(["git", "-C", str(src), "fetch", "-q", "--depth", "1", url, commit])
        run(["git", "-C", str(src), "checkout", "-q", "FETCH_HEAD"])
    pom = (src / "pom.xml").read_text()
    m = re.search(r"<artifactId>trino-root</artifactId>\s*<version>([^<]+)</version>", pom)
    version = m.group(1) if m else "unknown"
    base = os.environ.get("BENCHOLAP_TRINO_BASE_IMAGE") or _base_image_for(version)
    ensure_image(base)
    m2 = _cache() / "m2"
    m2.mkdir(exist_ok=True)
    log.info("building Trino %s from %s@%s (%s) inside %s; this takes a while", version, url, ref,
             commit[:12], base)
    # Build with the JDK of the base release image so the result runs on it. mvnd (the Maven
    # daemon, parallel by default) is used when it can be installed; plain ./mvnw otherwise.
    mvnd = _mvnd()
    goals = ("-B -Dmaven.repo.local=/m2 -DskipTests -Dair.check.skip-all=true -Dmaven.javadoc.skip=true "
             "-Dmaven.source.skip=true -pl :trino-server -am package")
    build = (f"/mvnd/bin/mvnd -Dmvnd.noBuffering=true {goals}" if mvnd else f"./mvnw -T 1C {goals}")
    mounts = ["-v", f"{mvnd}:/mvnd:ro"] if mvnd else []
    log.info("building with %s", "mvnd" if mvnd else "./mvnw")
    run(["docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
         "-e", "MAVEN_OPTS=-Xmx3g", "-e", "HOME=/tmp", "-e", "MVND_DAEMON_STORAGE=/tmp/mvnd",
         "-v", f"{src}:/src", "-v", f"{m2}:/m2", *mounts, "-w", "/src", "--entrypoint", "bash", base,
         "-c", build])
    tarballs = list((src / "core" / "trino-server" / "target").glob("trino-server-*.tar.gz"))
    if not tarballs:
        raise RuntimeError("source build finished but no trino-server tarball was produced")
    server_dir, version = _extract_server(tarballs[0], _cache() / "overlay" / commit[:12])
    source["base_image"] = _overlay(server_dir, version, tag, base)
    return ResolvedTarget("trino", spec, tag, version, version_number(version), source)
