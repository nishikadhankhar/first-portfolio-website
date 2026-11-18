#!/usr/bin/env python3
"""Build projects.json from the GitHub API + projects-meta.json (stdlib only)."""
import json, os, sys, urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "nishikadhankhar")
ROOT = Path(__file__).resolve().parent.parent


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def all_repos():
    page, out = 1, []
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def card(r, meta=None):
    meta = meta or {}
    return {
        "name": r["name"],
        "title": meta.get("title") or r["name"].replace("-", " ").replace("_", " "),
        "blurb": meta.get("blurb") or r.get("description") or "",
        "tags": meta.get("tags", []),
        "language": r.get("language"),
        "repo": r["html_url"],
        "live": meta.get("live") or r.get("homepage") or "",
        "pushed": r["pushed_at"][:10],
        "stars": r["stargazers_count"],
    }


def main():
    meta = json.loads((ROOT / "projects-meta.json").read_text())
    hidden = set(meta.get("hidden", []))
    repos = {r["name"]: r for r in all_repos() if not r["fork"] and not r["private"] and not r["archived"]}
    featured, used = [], set()
    for m in meta["featured"]:
        r = repos.get(m["repo"])
        if r:
            featured.append(card(r, m))
            used.add(r["name"])
        else:
            print(f"warning: featured repo {m['repo']} not found", file=sys.stderr)
    more = [card(r) for n, r in repos.items() if n not in used and n not in hidden]
    more.sort(key=lambda c: c["pushed"], reverse=True)
    data = {"featured": featured, "more": more}
    new = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path = ROOT / "projects.json"
    if not path.exists() or path.read_text() != new:
        path.write_text(new)
        print(f"projects.json updated: {len(featured)} featured, {len(more)} more")
    else:
        print("projects.json unchanged")


if __name__ == "__main__":
    main()
