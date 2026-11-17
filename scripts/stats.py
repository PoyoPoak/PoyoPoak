#!/usr/bin/env python3
"""Regenerate assets/dashboard.svg, the profile dashboard.

Stdlib only. Reads a token from GH_TOKEN. With a personal token the numbers
include private repositories; only aggregates are written, never private names.
Run: GH_TOKEN=$(gh auth token) python3 scripts/stats.py
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import stack
import terminal

USER = "PoyoPoak"
ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_LANGS = {"Jupyter Notebook", "Makefile", "PLpgSQL"}  # generated or vendored bytes, not hand-written code
OWNERS = {USER, "Ka-Technology"}  # count repositories under these owners only; other orgs are not my code
MIN_ORG_COMMITS = 5  # an organisation repository counts only with at least this many of my commits
EXCLUDE_REPOS = re.compile(r"^(osu-|chemeketa-|jos-labs)")  # coursework; skews languages toward C and C++
TOP_LANGS = 6
ACTIVITY_ROWS = 4
ACTIVITY_DAYS = 90  # how far back recent contributions look


def api(url, token, body=None):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "profile-stats"},
    )
    for attempt in range(3):  # GitHub returns the odd 502 on heavy GraphQL queries
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(10)


def graphql(query, token):
    out = api("https://api.github.com/graphql", token, {"query": query})
    if out.get("errors"):
        raise SystemExit(f"GraphQL error: {out['errors']}")
    return out["data"]["user"]


def my_commits(repos, token):
    """My commit count in each given repository, in order: the most on any one branch.

    Branches share history, so the per-branch maximum is used instead of a sum.
    Work that only exists on unmerged feature branches still counts.
    """
    if not repos:
        return []
    user_id = graphql('{user(login:"%s"){id}}' % USER, token)["id"]
    out = []
    # ponytail: 2 repositories per request and 100 branches each keeps the query under GitHub's time limit.
    for start in range(0, len(repos), 2):
        chunk = repos[start:start + 2]
        query = " ".join(
            'r%d:repository(owner:"%s",name:"%s"){refs(refPrefix:"refs/heads/",first:100){nodes{target{... on Commit'
            '{history(author:{id:"%s"}%s){totalCount}}}}}}' % (
                i, repo["owner"]["login"], repo["name"], user_id,
                f',since:"{repo["since"]}",until:"{repo["until"]}"' if "since" in repo else "",
            )
            for i, repo in enumerate(chunk)
        )
        data = api("https://api.github.com/graphql", token, {"query": "{%s}" % query}).get("data") or {}
        for i in range(len(chunk)):
            branches = ((data.get(f"r{i}") or {}).get("refs") or {}).get("nodes") or []
            out.append(max(((b.get("target") or {}).get("history", {}).get("totalCount", 0) for b in branches), default=0))
    return out


def select(nodes, org_commits):
    """Keep my own repositories, plus organisation ones in OWNERS with enough of my commits. Templates never count.

    org_commits maps "owner/name" to my commit count.
    """
    return [
        repo for repo in nodes
        if not repo.get("isTemplate")  # template repositories are scaffolding, not project work
        and (repo["owner"]["login"] == USER
             or org_commits.get(f'{repo["owner"]["login"]}/{repo["name"]}', 0) >= MIN_ORG_COMMITS)
    ]


def fetch(token):
    # ponytail: first:100 repositories, no pagination. Add a cursor loop past 100 repos.
    user = graphql(
        """{user(login:"%s"){
          pullRequests{totalCount}
          contributionsCollection{contributionYears contributionCalendar{totalContributions}}
          repositories(first:100,isFork:false,ownerAffiliations:[OWNER,ORGANIZATION_MEMBER,COLLABORATOR]){
            totalCount
            nodes{name isTemplate stargazerCount owner{login}
              languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
        % USER,
        token,
    )
    years = user["contributionsCollection"]["contributionYears"]
    per_year = graphql(
        '{user(login:"%s"){%s}}'
        % (
            USER,
            " ".join(
                'y%d:contributionsCollection(from:"%d-01-01T00:00:00Z",to:"%d-12-31T23:59:59Z")'
                "{totalCommitContributions}" % (y, y, y)
                for y in years
            ),
        ),
        token,
    )
    nodes = [r for r in user["repositories"]["nodes"] if r["owner"]["login"] == USER]
    org = []
    for owner in sorted(OWNERS - {USER}):  # the user listing misses organisation repositories, so ask the organisation
        data = api("https://api.github.com/graphql", token, {"query": """{organization(login:"%s"){
          repositories(first:100,isFork:false){nodes{name isTemplate stargazerCount owner{login}
            languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}""" % owner})
        org += ((data.get("data") or {}).get("organization") or {"repositories": {"nodes": []}})["repositories"]["nodes"]
    nodes += org
    org_commits = {f'{r["owner"]["login"]}/{r["name"]}': n for r, n in zip(org, my_commits(org, token))}
    repos = select(nodes, org_commits)
    numbers = {
        "Commits": sum(v["totalCommitContributions"] for v in per_year.values()),
        "Pull requests": user["pullRequests"]["totalCount"],
        "Contributions, past year": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "Repositories": len(repos),
        "Stars": sum(r["stargazerCount"] for r in repos if r["owner"]["login"] == USER),
    }
    return numbers, repos


def aggregate_languages(repos):
    """Return [(name, percent, color)] for the top languages by bytes."""
    sizes, colors = {}, {}
    for repo in repos:
        if EXCLUDE_REPOS.match(repo.get("name", "")):
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in EXCLUDE_LANGS:
                continue
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or terminal.MUTED
    top = sorted(sizes.items(), key=lambda item: -item[1])[:TOP_LANGS]
    total = sum(size for _, size in top)
    return [(name, 100 * size / total, colors[name]) for name, size in top]


def activity(token):
    """Recent commit contributions to public repositories: [(last day, "owner/repo", commits)], newest first."""
    since = (datetime.now(timezone.utc) - timedelta(days=ACTIVITY_DAYS)).strftime("%Y-%m-%dT00:00:00Z")
    rows = graphql(
        """{user(login:"%s"){contributionsCollection(from:"%s"){commitContributionsByRepository(maxRepositories:25){
          repository{name nameWithOwner isPrivate owner{login}}
          contributions(first:1,orderBy:{field:OCCURRED_AT,direction:DESC}){nodes{occurredAt}}}}}}"""
        % (USER, since),
        token,
    )["contributionsCollection"]["commitContributionsByRepository"]
    candidates = [
        {
            **row["repository"],
            "since": (day := row["contributions"]["nodes"][0]["occurredAt"]),
            "until": (datetime.fromisoformat(day) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for row in rows
        if not row["repository"]["isPrivate"]  # private repository names are never published
        and row["contributions"]["nodes"] and row["repository"]["nameWithOwner"] != f"{USER}/{USER}"
    ]
    recent = [
        (repo["since"][:10], repo["nameWithOwner"], commits)
        for repo, commits in zip(candidates, my_commits(candidates, token))
        if commits
    ]
    return sorted(recent, key=lambda item: (item[0], item[2]), reverse=True)[:ACTIVITY_ROWS]


def main():
    token = os.environ["GH_TOKEN"]
    numbers, repos = fetch(token)
    recent = [(day, name.split("/")[1], commits) for day, name, commits in activity(token)]
    svg = terminal.render(numbers, aggregate_languages(repos), recent, stack.sync())
    (ROOT / "assets" / "dashboard.svg").write_text(svg)
    print(numbers)


if __name__ == "__main__":
    main()
