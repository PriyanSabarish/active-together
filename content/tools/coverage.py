"""Where the library is thin. Run before drafting so a batch fills gaps rather than
piling more onto whatever the last person felt like writing.

    python tools/coverage.py
    python tools/coverage.py --target 6
"""
import argparse, collections, glob, yaml

ap = argparse.ArgumentParser()
ap.add_argument("--target", type=int, default=6, help="families wanted per category")
args = ap.parse_args()

CATS = ["park_and_garden", "playground", "sports_ground", "walking_track",
        "cycling_track", "reserve_and_bushland", "waterway_and_foreshore", "any"]
MECHANICS = ["find", "move", "count", "imagine", "sequence"]
WEATHER = ["dry", "wet", "windy", "hot", "cold", "any"]

by_cat = collections.Counter()
by_cat_mech = collections.Counter()
by_cat_weather = collections.Counter()
bare_site = collections.Counter()


def load_templates(path):
    """Tolerate both shapes: {templates: [...]} and a bare [...] list."""
    data = yaml.safe_load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("templates", [])
    if isinstance(data, list):
        return data
    return []


for path in glob.glob("missions/*.yaml"):
    for t in load_templates(path):
        c = t["category"]
        by_cat[c] += 1
        by_cat_mech[(c, t["mechanic"])] += 1
        for w in t["weather_tags"]:
            by_cat_weather[(c, w)] += 1
        if "bare_site" in t["site_requirements"]:
            bare_site[c] += 1

print(f"{'category':<26}{'have':>6}{'target':>8}{'gap':>6}   missing mechanics")
print("-" * 90)
for c in CATS:
    have, gap = by_cat[c], max(0, args.target - by_cat[c])
    missing = [m for m in MECHANICS if by_cat_mech[(c, m)] == 0]
    print(f"{c:<26}{have:>6}{args.target:>8}{gap:>6}   {', '.join(missing) or '-'}")

print("\nWet-weather cover (a rainy afternoon is when this matters most)")
for c in CATS:
    n = by_cat_weather[(c, 'wet')] + by_cat_weather[(c, 'any')]
    flag = "" if n >= 2 else "   <- thin"
    print(f"  {c:<26}{n:>3}{flag}")

print("\nBare-site templates (the equity path for sparse councils)")
total_bare = sum(bare_site.values())
print(f"  {total_bare} total{'   <- want at least 6' if total_bare < 6 else ''}")
