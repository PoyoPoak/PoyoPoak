"""Run: python3 scripts/test_stats.py"""
import xml.etree.ElementTree as ET

import stats

REPOS = [
    {"name": "osu-cs344", "languages": {"edges": [{"size": 9999, "node": {"name": "C", "color": "#555555"}}]}},
    {"languages": {"edges": [
        {"size": 600, "node": {"name": "Python", "color": "#3572A5"}},
        {"size": 100, "node": {"name": "Jupyter Notebook", "color": "#DA5B0B"}},
    ]}},
    {"languages": {"edges": [
        {"size": 300, "node": {"name": "TypeScript", "color": "#3178c6"}},
        {"size": 100, "node": {"name": "Python", "color": None}},
    ]}},
]

# Languages: excluded language and coursework repository dropped, sorted by size, percentages of the kept total.
langs = stats.aggregate_languages(REPOS)
assert [name for name, _, _ in langs] == ["Python", "TypeScript"], langs
assert round(langs[0][1]) == 70 and round(langs[1][1]) == 30, langs
assert stats.aggregate_languages([]) == []

# Repositories: my own always count, templates never, organisation ones need enough of my commits.
node = lambda owner, name, **extra: {"owner": {"login": owner}, "name": name, **extra}
nodes = [node("PoyoPoak", "a"), node("PoyoPoak", "template", isTemplate=True),
         node("Ka-Technology", "big"), node("Ka-Technology", "small"), node("Ka-Technology", "none")]
kept = stats.select(nodes, {"Ka-Technology/big": stats.MIN_ORG_COMMITS, "Ka-Technology/small": stats.MIN_ORG_COMMITS - 1})
assert [r["name"] for r in kept] == ["a", "big"], kept

# Stack: parsed from the site's JSX; a Badge without a variant is "brand".
SITE = """
<div id="skills" className="x">
  <span className="t">
    &gt; Skills
  </span>
  <span className="b">
    Languages
  </span>
  <div className="flex">
    <Badge variant="warning">Python</Badge>
    <Badge>C#</Badge>
    <Badge variant="neutral">C/C++</Badge>
  </div>
  <span className="b">
    Cloud &amp; DevOps
  </span>
  <Badge variant="warning">Github/Github Actions</Badge>
</div>
<div id="featured-projects">
  <Badge>Not a skill</Badge>
"""
assert stats.stack.parse(SITE) == {
    "Languages": [("Python", "warning"), ("C#", "brand"), ("C/C++", "neutral")],
    "Cloud & DevOps": [("Github/Github Actions", "warning")],
}, stats.stack.parse(SITE)
assert stats.stack.parse("<div>no skills section</div>") == {}

# Dashboard: well-formed XML with data, and with nothing to show.
for svg in (
    stats.terminal.render({"Commits": 1234, "Pull requests": 56, "Contributions, past year": 7}, langs,
                          [("2026-01-02", "repo <&>", 12), ("2026-01-01", "other", 1)], stats.stack.SKILLS),
    stats.terminal.render({"Commits": 1, "Pull requests": 2, "Contributions, past year": 3}, [], [], stats.stack.SKILLS),
):
    ET.fromstring(svg)

print("ok")
