"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.
Runs daily via GitHub Actions. Stdlib only, zero external dependencies.
"""
import calendar
import html
import json
import os
import urllib.request
from datetime import date, datetime, timezone

USER = "zxcvmh"
JOINED_YEAR = 2024
W = 44

# Clean circular portrait ASCII art without outer background noise
ART = r"""
                            -=+==--:----==---
                    -:--=++++-..+=+++=*-:=-+++=-
                  ---=+:=.....................=++=-
                  =+==...........................:++=
                -++.................................-
               -+.....................................
              =+.......................................
              +......=..................................
            -=+..........:...............................
            -=......-:....................................
            =...:................:.=..........:...........
            -+...............:..=...-+@.=.::.............
             +..:.:......:.....:-:.:==#..::..:...........
             +..........-.......--==-..+.=.:-............
             =:........:..=.-#=%**+++=:+--:.+*+.........
             -=.....#@.%..+@@@@@#*+-+*+#+@@+...:..*.....+
            -:=+...@#.*.+.-.....--=+++=::...-@+-+-#%...=
              -=...%++*%@%%*@%%*=====-==*#@#::.%#*+%..==
              %*@@.%===:..@...#:=+=++===+.-..@-..-=#.%%
             -#+#@.%====+++*%++=======--*+*+*==++==*-#*+
             -==*+.*===+++++++++++=++=-++=+++++++==+:=#.
              -#--:*=+++++++=+++-:-:-=-:=++===+++==+.:%#
              -@=#.======+=+++=:=+**+*++=-++++======.*-=
               -#%%=+=======+=-+*----=::+:-=++====+=#*#
               --%::*======++===::*+=++--=++====-=+.+@-
                 --==+======++++*#+++++#**++=-=-=++=.
                 ----**======++*=---:-:.-=+==-==+*==-
                    -=+====+-:--...::::.=.-====++=
                     -=====+=++-:==--+::-++===-=
                     -=#.--===-=++++++++=====-.*
                       -#+=.-=+++++++++++*++-.==#
                      -*=++=:.:==++***+--.:-+==*=
                      =*+==+++=--:.....:-======*=
                 -=+===+===+=++==+**#+++=======+.===
             -++++=..##====+=+=====----========+=*..+++=
        -=++++........@#*===++++++===+==========+%......++=
   -=++++...............@@%#+=++=+===========#%@*..........++++-
=+++.......................@@@@@@@@@@@@@@@@@@+.................=+++
""".strip("\n")

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""

def gh(url, payload=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Authorization": f"Bearer {token or TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-updater",
        },
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read().decode("utf-8") or "{}")

def graphql(query, variables=None, token=None):
    _, resp = gh("https://api.github.com/graphql", {"query": query, "variables": variables or {}}, token)
    if resp.get("errors"):
        raise RuntimeError(resp["errors"])
    return resp["data"]

def fetch_stats():
    if not TOKEN:
        try:
            req = urllib.request.Request(
                f"https://api.github.com/users/{USER}",
                headers={"User-Agent": "profile-updater", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(req) as r:
                u = json.loads(r.read().decode("utf-8"))
            return {
                "repos": u.get("public_repos", 5),
                "commits": 136,
            }
        except Exception as e:
            print(f"Fallback fetch error: {e}")
            return {"repos": 5, "commits": 136}

    try:
        current_year = datetime.now(timezone.utc).year
        yr_aliases = "\n".join(
            f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
            " { totalCommitContributions restrictedContributionsCount }"
            for y in range(JOINED_YEAR, current_year + 1)
        )
        contrib = graphql(f'query {{ user(login: "{USER}") {{ {yr_aliases} }} }}')["user"]
        commits = sum(
            v["totalCommitContributions"] + v["restrictedContributionsCount"]
            for v in contrib.values()
        )
        u = graphql(f"""
        query {{
          user(login: "{USER}") {{
            repositories(first: 100, ownerAffiliations: OWNER) {{
              totalCount
            }}
          }}
        }}""")["user"]
        return {
            "repos": u["repositories"]["totalCount"],
            "commits": commits,
        }
    except Exception as e:
        print(f"GraphQL fetch error: {e}")
        return {"repos": 5, "commits": 136}

PALETTES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "art": "#8b949e", "h": "#58a6ff",
        "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58", "g": "#3fb950", "r": "#f85149"
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "art": "#57606a", "h": "#0969da",
        "k": "#953800", "v": "#24292f", "d": "#afb8c1", "g": "#1a7f37", "r": "#cf222e"
    },
}

def kv(key, val, width=W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]

def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (W - len(label)), "d")]

def info_lines(s):
    n = lambda x: f"{x:,}"
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (W - len(USER) - 8), "d")],
        [],
        kv("OS", "Linux (CachyOS)"),
        kv("Host", "UIT - VNUHCM"),
        kv("Kernel", "CS Undergrad"),
        kv("IDE", "VS code, Antigravity"),
        [],
        kv("Languages.Code", "Python, C++"),
        kv("Languages.Real", "Vietnamese, English"),
        kv("Focus", "Information Retrieval, NLP, Agents"),
        [],
        rule("Contact"),
        kv("Email", "contact.hieuminhvu@gmail.com"),
        kv("LinkedIn", "in/minh-hieu-vu-681714381"),
        [],
        rule("GitHub Stats"),
        kv("Repos", str(s["repos"])),
        kv("Commits", n(s["commits"])),
    ]

def render(mode, stats):
    p = PALETTES[mode]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="860" height="520" viewBox="0 0 860 520" '
        f'font-family="Consolas, Menlo, Monaco, monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="859" height="519" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    # ASCII Art on left (38 lines, font size 10.5px, line height 12.5px)
    for i, line in enumerate(ART.split("\n")):
        out.append(f'<text x="20" y="{32 + i * 12.5}" font-size="10.5px" fill="{p["art"]}" xml:space="preserve">{html.escape(line)}</text>')
    # Specs info on right (starts at x="465")
    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(f'<text x="465" y="{42 + i * 21}" xml:space="preserve">{spans}</text>')
    out.append("</svg>")
    return "\n".join(out)

if __name__ == "__main__":
    stats = fetch_stats()
    print("Stats:", stats)
    for mode in PALETTES:
        with open(f"/home/zxcvmh/github-profile/{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("Regenerated dark_mode.svg and light_mode.svg successfully")
