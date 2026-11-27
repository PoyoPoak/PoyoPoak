"""The profile dashboard: boxed panels inside one terminal window, as a single SVG.

Animation is SMIL, so it plays when GitHub loads the file through <img>: a command
is typed into the blank terminal, then the panels load top to bottom. Links cannot
work inside an image, so the README puts its link buttons under the card.

Each *_panel function draws in its box's own coordinates (origin = box top-left)
and returns (svg, height); Dash places the boxes on the canvas.
"""
from html import escape

import stack

BG, BORDER, FG, MUTED, DIM, ACCENT, OK = "#09090B", "#27272A", "#FAFAFA", "#A1A1AA", "#71717A", "#0091FF", "#22C55E"
CHAR = 8.4  # px per character at 14px in the fonts used (narrower fonts only add slack)
LINE = 22
WIDTH, LEFT, FULL, GAP = 840, 24, 792, 20  # canvas width, margin, full box width, gap between boxes

# ---- Edit these by hand when they change ----
TAGLINE = "Software pioneer with a passion for saving time."
STATUS = ("open to full-time roles", "building ShiftWize · CIDA")  # right side of the whoami box
NOW = [
    "Building ShiftWize and CIDA at Ka Technology",
    "Taking on custom websites and software",
    "Open to full-time software engineering roles",
]
PROJECTS = [  # slug, where, one line (45 characters at most)
    ("realdoc", "realdoc.app", "Real estate CE certification automation"),
    ("doigetgas", "doigetgas.com", "Gas price outlook from crude oil futures"),
    ("camera-odometer", "github.com", "Camera business-use share from shutter counts"),
    ("personal-site", "peterluey.com", "Portfolio: experience, skills, projects"),
]
BOOT = "peter --dashboard"  # typed into the blank terminal before the panels load
TYPE = 0.06  # seconds per typed character

STAT_ROWS = [("commits", "Commits"), ("pull requests", "Pull requests"),
             ("contributions this year", "Contributions, past year")]


# ---------- primitives ----------

def spans(parts):
    if isinstance(parts, str):
        parts = [(parts, FG)]
    return "".join(f'<tspan fill="{color}">{escape(part)}</tspan>' for part, color in parts)


def text(x, y, parts, size=None, weight=None, anchor=None, length=None):
    attrs = (f' font-size="{size}"' if size else "") + (f' font-weight="{weight}"' if weight else "")
    attrs += f' text-anchor="{anchor}"' if anchor else ""
    attrs += f' textLength="{length}" lengthAdjust="spacingAndGlyphs"' if length else ""
    return f'<text x="{x}" y="{y}" xml:space="preserve"{attrs}>{spans(parts)}</text>'


def cursor(x, y):
    return (
        f'<rect x="{x}" y="{y - 13}" width="9" height="17" fill="{ACCENT}">'
        '<animate attributeName="opacity" calcMode="discrete" values="1;0" dur="1.1s" repeatCount="indefinite"/></rect>'
    )


def appear(inner, at, attrs=""):
    return f'<g opacity="0"{attrs}><set attributeName="opacity" to="1" begin="{at:.2f}s" fill="freeze"/>{inner}</g>'


def frame(height, title, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'font-family="{stack.FONT}" font-size="14" role="img" aria-label="{escape(label)}">'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M0.5 36.5h{WIDTH - 1}" stroke="{BORDER}"/>'
        + "".join(f'<circle cx="{22 + 20 * i}" cy="18" r="5.5" fill="#3F3F46"/>' for i in range(3))
        + f'<text x="{WIDTH / 2}" y="23" fill="{DIM}" font-size="12" text-anchor="middle">{escape(title)}</text>'
        f"{body}</svg>\n"
    )


def box(x, y, w, h, title, inner, at):
    """Bordered box with its title set into the top edge; fades in at `at` seconds."""
    return appear(
        f'<rect x="0.5" y="0.5" width="{w}" height="{h}" rx="6" fill="none" stroke="{BORDER}"/>'
        f'<rect x="14" y="-8" width="{CHAR * len(title) + 16:.0f}" height="16" fill="{BG}"/>'
        + text(22, 5, [(title, ACCENT)]) + inner,
        at, f' transform="translate({x} {y})"',
    )


def status_bar(y, windows, right="peterluey.com"):
    return (
        f'<rect x="8" y="{y}" width="{WIDTH - 16}" height="22" rx="4" fill="{ACCENT}"/>'
        + text(18, y + 15, [(windows, BG)], size=12, weight=600)
        + text(WIDTH - 18, y + 15, [(right, BG)], size=12, weight=600, anchor="end")
    )


def boot(start=0.5):
    """Blank terminal, the command typed out, then cleared. Returns (svg, time the panels may start)."""
    steps = ";".join(f"{CHAR * i:.1f}" for i in range(len(BOOT) + 1))
    cursor_steps = ";".join(f"{42 + CHAR * i:.1f}" for i in range(len(BOOT) + 1))
    typing = f'calcMode="discrete" begin="{start:.2f}s" dur="{TYPE * len(BOOT):.2f}s" fill="freeze"'
    done = start + TYPE * len(BOOT) + 0.45
    return (
        f'<g><set attributeName="opacity" to="0" begin="{done:.2f}s" fill="freeze"/>'
        f'<clipPath id="boot"><rect x="42" y="46" width="0" height="22">'
        f'<animate attributeName="width" {typing} values="{steps}"/></rect></clipPath>'
        f'<text x="24" y="62" fill="{ACCENT}">$</text>'
        + text(42, 62, BOOT, length=f"{CHAR * len(BOOT):.1f}").replace("<text ", '<text clip-path="url(#boot)" ', 1)
        + f'<rect x="42" y="49" width="9" height="17" fill="{ACCENT}">'
        f'<animate attributeName="x" {typing} values="{cursor_steps}"/></rect></g>'
    ), done + 0.1


# ---------- panels: (svg in box coordinates, height) ----------

def whoami_panel(w=FULL):
    headline, detail = STATUS
    return (
        text(20, 44, "Peter Luey", size=26, weight=700, length=150) + cursor(176, 42)
        + text(20, 72, [(TAGLINE, MUTED)])
        + f'<circle cx="{w - 34 - CHAR * len(headline):.0f}" cy="39" r="4" fill="{OK}"/>'
        + text(w - 20, 44, headline, anchor="end") + text(w - 20, 72, [(detail, MUTED)], anchor="end")
    ), 92


def featured_panel(w=FULL):
    """One row per project: slug, description, where."""
    return "".join(
        text(20, 32 + LINE * i, [(slug, ACCENT)]) + text(180, 32 + LINE * i, desc)
        + text(w - 20, 32 + LINE * i, [(where, DIM)], anchor="end")
        for i, (slug, where, desc) in enumerate(PROJECTS)
    ), 32 + LINE * (len(PROJECTS) - 1) + 20


def now_panel():
    return "".join(text(20, 34 + 26 * i, [("• ", ACCENT), (item, FG)]) for i, item in enumerate(NOW)), 126


def contributions_panel(recent, w, rows=4):
    """Recent contributions: last day, repository (or "private"), commit count."""
    out = "".join(
        text(20, 32 + LINE * i, [(day[5:] + "  ", DIM), (repo[:18], FG)])
        + text(w - 20, 32 + LINE * i, [(f"+{commits:,} ", FG), ("commits" if commits != 1 else "commit ", DIM)], anchor="end")
        for i, (day, repo, commits) in enumerate(recent[:rows])
    ) or text(20, 32, [("no recent commits", DIM)])
    return out, 126


def stack_panel(skills, w=FULL, columns=2, gap=14):
    """Site-coloured chips under a subheader per group."""
    column = (w - 40 - 28 * (columns - 1)) // columns
    groups, out, y = list(skills.items()), "", 34
    for i in range(0, len(groups), columns):
        tallest = 0
        for j, (group, names) in enumerate(groups[i:i + columns]):
            x = 20 + j * (column + 28)
            fragment, height = stack.chips(names, x, y + 12, column)
            out += text(x, y, [(group.upper(), DIM)], size=11, weight=700) + fragment
            tallest = max(tallest, height + 22)
        y += tallest + gap
    return out, y - gap + 4


def stats_panel(numbers, langs, w=FULL):
    """Stats on one line, then a full-width language bar with its legend."""
    parts, bar, legend, pos, legend_x = [], "", "", 20.0, 20.0
    for label, key in STAT_ROWS:
        parts += [(("    " if parts else "") + label + " ", MUTED), (f"{numbers[key]:,}", FG)]
    for name, percent, color in langs:
        share = f"{percent:.0f}%"
        bar += f'<rect x="{pos:.1f}" y="46" width="{(w - 40) * percent / 100:.1f}" height="8" fill="{color}"/>'
        pos += (w - 40) * percent / 100
        legend += f'<circle cx="{legend_x + 4:.1f}" cy="72" r="4" fill="{color}"/>'
        legend += text(round(legend_x + 14, 1), 76, [(name + " ", FG), (share, MUTED)], size=12)
        legend_x += 14 + (len(name) + len(share) + 1) * 7.2 + 18
    return text(20, 32, parts) + bar + legend, 92


# ---------- layout ----------

class Dash:
    """Stacks rows of boxes down the window, after the boot command has been typed."""

    def __init__(self):
        self.y = 60
        self.body, self.at = boot()

    def row(self, *boxes):
        """boxes: (x, w, title, (svg, height)). Boxes in a row share the tallest height."""
        height = max(panel[1] for _, _, _, panel in boxes)
        for x, w, title, (svg, _) in boxes:
            self.body += box(x, self.y, w, height, title, svg, self.at)
            self.at += 0.2
        self.y += height + GAP

    def svg(self, label, windows):
        self.body += appear(status_bar(self.y - 4, windows), self.at)
        return frame(self.y + 32, "peter@luey: ~", self.body, label)


def render(numbers, langs, recent, skills):
    """numbers: {label: int}; langs: [(name, percent, colour)]; recent: [(day, repo, commits)]; skills: {group: [(name, tier)]}."""
    dash = Dash()
    dash.row((LEFT, FULL, "whoami", whoami_panel()))
    dash.row((LEFT, FULL, "featured projects", featured_panel()))
    dash.row((LEFT, 424, "now", now_panel()), (464, 352, "recent contributions", contributions_panel(recent, 352)))
    dash.row((LEFT, FULL, "stack", stack_panel(skills)))
    dash.row((LEFT, FULL, "stats", stats_panel(numbers, langs)))
    return dash.svg(
        "Peter Luey. " + TAGLINE + " Now: " + "; ".join(NOW) + ". Featured projects: "
        + ", ".join(slug for slug, *_ in PROJECTS) + ". Stack: "
        + "; ".join(f"{group}: {', '.join(name for name, _ in names)}" for group, names in skills.items()) + ".",
        "[profile] 0:dashboard*",
    )
