"""Bulk-draft candidate mission templates against the frozen schema.

Drafts land in missions/_candidates/ as status: draft. Nothing here is shippable.
The point is to turn authoring from writing into editing.

    # Groq
    $env:MISSION_MODEL_BASE_URL="https://api.groq.com/openai/v1"
    $env:MISSION_MODEL_NAME="llama-3.3-70b-versatile"
    $env:MISSION_MODEL_API_KEY="gsk_..."

    # local Ollama - no key needed
    $env:MISSION_MODEL_BASE_URL="http://localhost:11434/v1"
    $env:MISSION_MODEL_NAME="llama3.1:8b"

    python tools/draft_missions.py --category park_and_garden --mechanic move --count 4

Any OpenAI-compatible endpoint works: Groq, OpenAI, vLLM, llama.cpp server, Ollama, TGI.
Drafting is authoring, not runtime - it touches no user data, so a hosted API here does
not conflict with the decision to self-host everything the product itself runs on.
"""
import argparse, glob, json, os, re, sys, urllib.request, yaml

BASE = os.environ.get("MISSION_MODEL_BASE_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("MISSION_MODEL_NAME", "")
API_KEY = (os.environ.get("MISSION_MODEL_API_KEY")
           or os.environ.get("GROQ_API_KEY")
           or os.environ.get("OPENAI_API_KEY"))

if not MODEL:
    sys.exit("set MISSION_MODEL_NAME to the model you want to draft with")

ap = argparse.ArgumentParser()
ap.add_argument("--category", required=True)
ap.add_argument("--mechanic", required=True, choices=["find", "move", "count", "imagine", "sequence"])
ap.add_argument("--weather", default="any")
ap.add_argument("--bare-site", action="store_true", help="must work on open grass with a fence")
ap.add_argument("--count", type=int, default=3, help="families per batch; 3 is the practical ceiling")
ap.add_argument("--dry-run", action="store_true", help="print the prompt, call nothing")
args = ap.parse_args()

safety = yaml.safe_load(open("schema/safety_constraints.yaml", encoding="utf-8"))
vocab = yaml.safe_load(open("prompts/vocabulary.yaml", encoding="utf-8"))
schema = open("schema/mission_template.schema.yaml", encoding="utf-8").read()

# Only prompts that survived measurement may be used. Before measurement, none have.
usable = [p for p in vocab["prompts"] if p["status"] == "kept"]
if not usable:
    print("NOTE: no prompt has status 'kept' yet, so every step will be drafted as verify: self.")
    print("      Run the measurement (task B25) before drafting photo steps.\n")


def load_templates(path):
    """Tolerate both shapes: {templates: [...]} and a bare [...] list."""
    data = yaml.safe_load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("templates", [])
    if isinstance(data, list):
        return data
    return []


existing_titles, existing_openers = [], []
# Only the reviewed library informs a new draft. Candidates are not part of it.
for path in glob.glob("missions/*.yaml"):
    for t in load_templates(path):
        existing_titles.append(t["title"])
        if t["steps"]:
            existing_openers.append(t["steps"][0]["prompt_text"])

never_write = "\n".join(f"- {c['rule']}" for c in safety["constraints"])
prompt_list = "\n".join(f"- {p['id']}: {p['text']}" for p in usable) or "  (none yet)"

SYSTEM = (
    "You draft candidate mission templates for a children's outdoor activity app. "
    "A parent reads each step aloud; the child goes and does it. The child never holds the phone. "
    "Every step must be completable after hearing it once, must require physical movement or "
    "close looking, and must be written for the youngest age in its band. "
    "You are drafting for human review. Output YAML only, no commentary."
)

USER = f"""Draft {args.count} mission template families.

Category: {args.category}
Mechanic: {args.mechanic}
Weather tag: {args.weather}
{"Must be completable at a bare site - open grass and a fence, nothing else." if args.bare_site else ""}

Schema to follow exactly:
{schema}

STRUCTURE

Author each family at 60 minutes with 7 steps, ordered so the first 3 stand alone as a
20-minute mission and the first 5 stand alone as a 40-minute mission. Put the shared fields
at the top level and three wordings under a `bands` key: "5-7", "8-10", "11-12". Set
`variable: true` on every step - the runtime model rewrites wording, so it must be allowed to.
Do not emit a top-level `steps` list; the steps live inside each band.

THE BANDS ARE DIFFICULTY, NOT VOCABULARY

Wrong - this is a thesaurus, all three ask for the same thing:
  5-7:    "Ride to the tree and stop."
  8-10:   "Ride to the tree and halt."
  11-12:  "Pedal to the tree and come to a stop."

Right - the task itself changes:
  5-7:    "Ride to the big tree and come back."
  8-10:   "Ride to the big tree and back twice, counting each lap."
  11-12:  "Ride there and back twice, then try to beat your own time."

5-7 is one simple physical instruction under 12 words. 8-10 adds a count, a comparison or a
second attempt. 11-12 adds planning, self-measurement or a decision the child makes.

EACH FAMILY MUST BE A DIFFERENT IDEA

The most common failure is producing one mission {args.count} times with the nouns swapped.
Give each family a genuinely different spine. Some spines that differ from each other:
speed against yourself; a route you choose rather than one given; noticing what changed on
the way back; a sequence you build up step by step; a rhythm or pattern of movement; a
challenge that gets harder each round. Pick a different one per family.

ONLY REFERENCE WHAT IS ACTUALLY THERE

The app knows a place's category and nothing else. It does not know that a site has cones,
flags, painted lines, markers, signs, start lines, benches or equipment. Never invent them.
You may reference only: the path or track itself, grass, trees, a fence, the sky, the ground,
and whatever is listed in site_requirements. If a step needs a landmark, let the child choose
one - "pick a tree you can see and ride to it" - rather than naming one that may not exist.

EVERY STEP IS AN ACTIVITY

No step may be a greeting, a wave, a smile, a cheer, or a "well done". No step may exist only
to reach seven. If you cannot write seven real steps for a spine, pick a different spine.

SAFETY - never write a step that breaks any of these:
{never_write}

PHOTO STEPS

Verified prompts you may use as prompt_id, and nothing else:
{prompt_list}

Any step that cannot use one of those is verify: self with prompt_id: null.

DO NOT REPEAT

Existing titles:
{", ".join(existing_titles)}

Existing opening steps:
{chr(10).join("- " + s for s in existing_openers)}

Set review.author to "bulk-draft" and review.status to "draft". Emit complete YAML for all
{args.count} families - do not truncate. Output YAML only."""

if args.dry_run:
    print(USER); sys.exit(0)

body = json.dumps({
    "model": MODEL,
    "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}],
    "temperature": 1.0,
    "max_tokens": 12000,
}).encode()

headers = {
    "Content-Type": "application/json",
    # Some providers sit behind Cloudflare, which blocks the default urllib
    # user agent with a 403 "error code: 1010" before the API is reached.
    "User-Agent": "active-together-content-tools/1.0",
    "Accept": "application/json",
}
if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"

req = urllib.request.Request(f"{BASE}/chat/completions", data=body, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        text = json.load(r)["choices"][0]["message"]["content"]
except urllib.error.HTTPError as e:
    detail = e.read().decode("utf-8", "replace")[:600]
    if e.code == 401:
        sys.exit(f"401 unauthorised - check MISSION_MODEL_API_KEY.\n{detail}")
    if e.code == 404:
        sys.exit(f"404 - '{MODEL}' is probably not a model this endpoint serves.\n{detail}")
    if e.code == 403 and "1010" in detail:
        sys.exit("403 from Cloudflare, not the API - the request was blocked on user agent.\n"
                 "Update this script to the latest version, which sets one.")
    sys.exit(f"HTTP {e.code} from {BASE}\n{detail}")
except urllib.error.URLError as e:
    sys.exit(f"could not reach {BASE} - is the server running, or the URL right?\n{e.reason}")

text = re.sub(r"^```(?:yaml)?|```$", "", text.strip(), flags=re.M).strip()

# Models emit typographic punctuation. It breaks cp1252 on Windows and reads badly
# in text a parent speaks aloud, so fold it to plain ASCII before parsing.
TYPOGRAPHIC = {
    "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": " - ", "\u2015": "-",
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2026": "...", "\u00a0": " ", "\u202f": " ", "\u2009": " ",
}
for bad, good in TYPOGRAPHIC.items():
    text = text.replace(bad, good)
try:
    parsed = yaml.safe_load(text)
except yaml.YAMLError as e:
    print("model did not return parseable YAML:", e); sys.exit(1)

if isinstance(parsed, list):
    parsed = {"templates": parsed}
elif isinstance(parsed, dict) and "templates" not in parsed:
    sys.exit("model returned YAML without a 'templates' key:\n" + text[:400])

tag = f"{args.category}_{args.mechanic}_{args.weather}"
out = f"missions/_candidates/{tag}.yaml"
with open(out, "w", encoding="utf-8") as f:
    f.write(f"# CANDIDATE BATCH - {tag}. Drafted, not reviewed, not in the served library.\n")
    f.write("# Move a family into missions/<category>.yaml only after human review.\n\n")
    yaml.safe_dump(parsed, f, sort_keys=False, allow_unicode=True, width=110)

n = len(parsed.get("templates", []))
print(f"wrote {n} candidate families to {out}")
print("next: python schema/check_drafts.py  then review by hand")
