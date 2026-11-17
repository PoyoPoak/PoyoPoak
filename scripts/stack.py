"""Skills shown in the dashboard's stack box, mirrored from peterluey.com.

sync() reads the Skills section of the site's source (PersonalSite, app/page.tsx)
so the dashboard follows the site without edits here. SKILLS is the fallback used
when the site cannot be read or its markup no longer parses.
"""
import re
import urllib.request
from html import escape, unescape

SITE_SOURCE = "https://raw.githubusercontent.com/PoyoPoak/PersonalSite/main/app/page.tsx"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# Badge tiers from the site theme: tier -> (chip background, text colour).
TIERS = {"warning": ("#352800", "#F0C000"), "brand": ("#102A4C", "#369EFF"), "neutral": ("#27272A", "#E4E4E7")}
W, B, N = "warning", "brand", "neutral"
SKILLS = {
    "Languages": [("Python", W), ("C#", B), ("JavaScript", B), ("TypeScript", B), ("SQL", B),
                  ("C/C++", N), ("Java", N), ("HTML", N), ("CSS", N)],
    "Frontend": [("Claude Design", W), ("React", B), ("Next.js", B), ("Tailwind CSS", B),
                 ("Angular", N), ("Playwright", N), ("Figma", N)],
    "Backend": [("Flask", W), ("MySQL", W), ("FastAPI", W), ("Node.js", B), ("ASP.NET", B), ("OpenAPI", B),
                ("MongoDB", N), ("PostgreSQL", N), ("CORS", N), ("Redis", N), ("RabbitMQ", N), ("Express", N)],
    "Cloud & DevOps": [("Github/Github Actions", W), ("Railway", W), ("Docker", W), ("Azure DevOps", W),
                       ("Snowflake", W), ("AWS", B), ("dbt", B), ("Linux", B),
                       ("Jenkins CI/CD", N), ("Google Cloud", N), ("Bitbucket", N)],
    "AI": [("Claude Code", W), ("Copilot", W), ("Antigravity", W), ("MCP", B), ("OpenRouter", B),
           ("Codex", N), ("PyTorch", N)],
}

CHIP_H, CHIP_GAP, CHAR = 24, 8, 7.2  # 12px monospace, width forced with textLength


def parse(source):
    """Read {group: [(skill, tier)]} out of the site's Skills section. Empty dict if the markup changed."""
    start, end = source.find('id="skills"'), source.find('id="featured-projects"')
    if start < 0 or end < start:
        return {}
    groups, current = {}, None
    # A group title is a bare text line; a skill is a <Badge>. Badge's default variant is "brand".
    for title, variant, skill in re.findall(
        r'^\s*([A-Za-z][A-Za-z0-9 &;/+.-]*?)\s*$|<Badge(?:\s+variant="(\w+)")?\s*>([^<]+)</Badge>', source[start:end], re.M
    ):
        if skill:
            if current is not None and (variant or "brand") in TIERS:
                groups[current].append((unescape(skill.strip()), variant or "brand"))
        elif not unescape(title).startswith(">"):  # skip the "> Skills" section heading
            current = unescape(title)
            groups[current] = []
    return {group: skills for group, skills in groups.items() if skills}


def sync():
    """Skills from the live site source, or the SKILLS fallback."""
    try:
        with urllib.request.urlopen(SITE_SOURCE, timeout=20) as response:
            skills = parse(response.read().decode())
    except OSError:
        skills = {}
    if len(skills) < 3:  # fewer groups than the site has ever had means the parse went wrong
        print("stack: site source unreadable, using the built-in list")
        return SKILLS
    return skills


def chips(skills, x, y, max_width):
    """Wrapped row of site-coloured chips. Returns (svg fragment, height)."""
    out, cx, cy = "", x, y
    for name, tier in skills:
        background, colour = TIERS[tier]
        text_width = CHAR * len(name)
        width = text_width + 16
        if cx > x and cx + width > x + max_width:
            cx, cy = x, cy + CHIP_H + CHIP_GAP
        out += (
            f'<rect x="{cx:.1f}" y="{cy}" width="{width:.1f}" height="{CHIP_H}" rx="6" fill="{background}"/>'
            f'<text x="{cx + 8:.1f}" y="{cy + 16}" fill="{colour}" font-size="12" textLength="{text_width:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(name)}</text>'
        )
        cx += width + CHIP_GAP
    return out, cy + CHIP_H - y
