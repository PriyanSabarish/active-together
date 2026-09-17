"""Pre-review check over the content library.

Not the production validator (task B22). This catches what a bulk draft gets wrong,
so a human reviewer spends their time on judgement rather than on counting steps.

    python schema/check_drafts.py

Errors must be fixed. Warnings are expected while things are drafts.
"""
import glob, sys, yaml
from pathlib import Path

# Migrated families use the shared checks, including measured photo vocabulary.
# Keep the older mission batches on their original checks for comparison.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from content.tools.mission_library import load_mission_families

STEPS_FOR = {20: 3, 40: 5, 60: 7}
BANDS = ["5-7", "8-10", "11-12"]
EVERYDAY = {"bicycle", "helmet", "ball", "chalk", "water bottle"}
INVENTED = ["cone", "flag", "painted line", "start line", "starting line", "marker",
            "sign", "finish line", "goal post", "chalk line"]
FILLER = ["wave to", "give a smile", "give a big grin", "cheer", "well done",
          "say goodbye", "high five", "clap for", "give a big smile"]

safety = yaml.safe_load(open("schema/safety_constraints.yaml", encoding="utf-8"))
vocab = yaml.safe_load(open("prompts/vocabulary.yaml", encoding="utf-8"))
known_prompts = {p["id"] for p in vocab["prompts"]}
kept_prompts = {p["id"] for p in vocab["prompts"] if p["status"] == "kept"}
weak_prompts = {p["id"] for p in vocab["prompts"] if p.get("expect") == "weak"}

errors, warnings = [], []

try:
    migrated, migrated_warnings = load_mission_families(preview=True)
    warnings.extend(migrated_warnings)
    warnings.extend(t["template_id"] + ": draft - not shippable"
                    for t in migrated if t["review"]["status"] != "reviewed")
except ValueError as error:
    errors.append("Migrated mission collection: " + str(error))


def load_templates(path):
    data = yaml.safe_load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("templates") or []
    return data if isinstance(data, list) else []


def norm(t):
    return " ".join(sorted(w.strip(".,!?").lower() for w in t.split()))


seen_shapes = {}
paths = sorted(glob.glob("missions/*.yaml")) + sorted(glob.glob("missions/_candidates/*.yaml"))

for path in paths:
    if Path(path).stem.startswith("activity_"):
        continue  # Already checked by the migration loader above.
    for t in load_templates(path):
        tid = t.get("template_id", f"<no id in {path}>")

        for field in ["title", "category", "duration_bucket", "mechanic", "bands"]:
            if field not in t:
                errors.append(f"{tid}: missing required field '{field}'")
        if "bands" not in t or not isinstance(t["bands"], dict) or not t["bands"]:
            errors.append(f"{tid}: no bands - a family needs at least one age band")
            continue
        if "age_band" in t or "steps" in t:
            errors.append(f"{tid}: old shape - top-level age_band/steps, expected bands only")

        bucket = t.get("duration_bucket")
        if bucket not in STEPS_FOR:
            errors.append(f"{tid}: duration_bucket {bucket} must be 20, 40 or 60")
            continue
        want = STEPS_FOR[bucket]

        for item in t.get("equipment") or []:
            if item not in EVERYDAY:
                errors.append(f"{tid}: equipment '{item}' not in the everyday allowlist")

        counts, per_band = {}, {}
        for band, spec in t["bands"].items():
            if band not in BANDS:
                errors.append(f"{tid}: unknown band '{band}'")
                continue
            steps = (spec or {}).get("steps") or []
            counts[band] = len(steps)
            texts = []

            if len(steps) != want:
                errors.append(f"{tid} [{band}]: {len(steps)} steps, bucket {bucket} wants {want}")

            for i, st in enumerate(steps, 1):
                if not isinstance(st, dict) or "prompt_text" not in st:
                    errors.append(f"{tid} [{band}] step {i}: malformed or truncated")
                    continue
                text, low = st["prompt_text"], st["prompt_text"].lower()
                texts.append(text)

                if st.get("sequence") != i:
                    warnings.append(f"{tid} [{band}] step {i}: sequence is {st.get('sequence')}")
                if st.get("variable") is False:
                    warnings.append(f"{tid} [{band}] step {i}: variable: false blocks runtime variation")

                for c in safety["constraints"]:
                    for phrase in c["rejects"]:
                        if phrase in low:
                            errors.append(f"{tid} [{band}] step {i}: hits {c['id']} via '{phrase}'")
                for word in FILLER:
                    if word in low:
                        errors.append(f'{tid} [{band}] step {i}: filler, not an activity - "{text[:46]}"')
                for word in INVENTED:
                    if word in low:
                        warnings.append(f'{tid} [{band}] step {i}: invents a site feature - "{word}"')

                if st.get("verify_mode") == "photo":
                    pid = st.get("prompt_id")
                    if not pid:
                        errors.append(f"{tid} [{band}] step {i}: photo step with no prompt_id")
                    elif pid not in known_prompts:
                        errors.append(f"{tid} [{band}] step {i}: unknown prompt_id {pid}")
                    else:
                        if pid not in kept_prompts:
                            warnings.append(f"{tid} [{band}] step {i}: prompt {pid} not yet measured")
                        if pid in weak_prompts:
                            warnings.append(f"{tid} [{band}] step {i}: prompt {pid} expected to fail measurement")
                elif st.get("prompt_id"):
                    errors.append(f"{tid} [{band}] step {i}: self step carries a prompt_id")

                if band == "5-7" and len(text.split()) > 12:
                    errors.append(f"{tid} [{band}] step {i}: {len(text.split())} words, over the 5-7 limit")

            per_band[band] = [norm(x) for x in texts]

        if len(set(counts.values())) > 1:
            errors.append(f"{tid}: bands have different step counts {counts}")

        present = [b for b in BANDS if b in per_band]
        for a, b in zip(present, present[1:]):
            xa, xb = per_band[a], per_band[b]
            if not xa or len(xa) != len(xb):
                continue
            same = sum(1 for x, y in zip(xa, xb)
                       if len(set(x.split()) & set(y.split())) >= len(x.split()) * 0.6)
            if same >= len(xa) * 0.8:
                warnings.append(f"{tid}: bands {a} and {b} differ only by wording, not difficulty")
        if len(present) < 3:
            warnings.append(f"{tid}: only covers {', '.join(present)} - {3 - len(present)} band(s) unwritten")

        first = present[0] if present else None
        if first:
            shape = tuple(s[:24] for s in per_band[first])
            if shape and shape in seen_shapes:
                errors.append(f"{tid}: same step shape as {seen_shapes[shape]} - one idea drafted twice")
            elif shape:
                seen_shapes[shape] = tid

        if (t.get("review") or {}).get("status") != "reviewed":
            warnings.append(f"{tid}: status '{(t.get('review') or {}).get('status')}' - not shippable")

for path in sorted(glob.glob("combos/*.yaml")):
    data = yaml.safe_load(open(path, encoding="utf-8"))
    for c in data["combos"]:
        total = sum(b["minutes"] for b in c["blocks"])
        if total != c["duration_bucket"]:
            errors.append(f"{c['combo_id']}: blocks sum to {total}, bucket is {c['duration_bucket']}")
        if not 2 <= len(c["blocks"]) <= 5:
            errors.append(f"{c['combo_id']}: {len(c['blocks'])} blocks, must be 2-5")

print(f"errors: {len(errors)}")
for e in errors:
    print("  ERROR  ", e)
print(f"warnings: {len(warnings)}")
for w in warnings[:15]:
    print("  warn   ", w)
if len(warnings) > 15:
    print(f"  ... and {len(warnings) - 15} more")
sys.exit(1 if errors else 0)
