# Maintaining the profile

`README.md` is the GitHub profile page. It shows one image, `assets/dashboard.svg`, a terminal-style dashboard drawn by `scripts/stats.py`, followed by link buttons and a view counter.

## What updates on its own

`.github/workflows/stats.yml` rebuilds the dashboard every day at 13:17 UTC and commits it when anything changed.

| Panel | Source |
|---|---|
| **stats** | GitHub API: all-time commits, pull requests, contributions in the past year, top languages |
| **recent contributions** | GitHub API: public repositories with commits in the last 90 days, with commit counts |
| **stack** | Skills section of peterluey.com, read from `app/page.tsx` in `PoyoPoak/PersonalSite` |
| **view counter** | komarev.com, live on every page view |

- **Stack fallback:** if the site source cannot be read or no longer parses, `SKILLS` in `scripts/stack.py` is used and the run logs `stack: site source unreadable`. The parser expects each group title on its own line and each skill as a `<Badge>` between `id="skills"` and `id="featured-projects"`.

## What to edit by hand

The constants at the top of `scripts/terminal.py`:

- `TAGLINE`, `STATUS`: the whoami box
- `NOW`: the now box
- `PROJECTS`: featured projects (one-line descriptions of 45 characters at most)
- `BOOT`: the command typed before the panels load

Then run the script locally (below) or trigger the workflow from the Actions tab.

## What the stats count

Set at the top of `scripts/stats.py`:

- **Repositories:** my own, plus repositories of the organisations in `OWNERS` where I have at least `MIN_ORG_COMMITS` commits on some branch.
- **Never counted:** repositories marked as templates on GitHub, and other people's organisations.
- **Languages:** coursework repositories (`EXCLUDE_REPOS`) and generated languages (`EXCLUDE_LANGS`) are left out.
- **Privacy:** only totals reach the image. Private repository names never appear; recent contributions lists public repositories only.

## Token

Private and organisation work is counted only when the workflow has a personal access token:

1. Create a **classic** token at <https://github.com/settings/tokens> with scopes `repo` and `read:org`. A fine-grained token covers one owner only, so it would miss either my repositories or Ka-Technology's.
2. Add it as a repository secret named `STATS_TOKEN`: `gh secret set STATS_TOKEN --repo PoyoPoak/PoyoPoak`.
3. When it expires, the workflow fails and GitHub emails me. Replace the secret the same way.

Without the secret the workflow still runs, warns, and draws public-only numbers.

## Run and check locally

```bash
python3 scripts/test_stats.py
GH_TOKEN=$(gh auth token) python3 scripts/stats.py
```

Then open `assets/dashboard.svg` in a browser to see the animation.
