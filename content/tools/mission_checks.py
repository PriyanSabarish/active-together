"""Shared content checks for authored families and final Mission step text."""

import re

from content.tools.activity_library import CONTENT_DIR, read_yaml


FILLER = ("wave to", "give a smile", "give a big grin", "cheer", "well done",
          "say goodbye", "high five", "clap for", "give a big smile")
INVENTED = ("cone", "flag", "painted line", "start line", "starting line", "marker",
            "sign", "finish line", "goal post", "chalk line", "bench")
WORD_FORMS = {
    "climb": ("climbs", "climbed", "climbing"),
    "wade": ("wades", "waded", "wading"),
    "swim": ("swims", "swam", "swimming"),
    "taste": ("tastes", "tasted", "tasting"),
    "lick": ("licks", "licked", "licking"),
    "dig": ("digs", "dug", "digging"),
}


def load_content_rules(content_dir=CONTENT_DIR):
    """Load actual safety rules and measured prompt status; fail on broken resources."""
    safety = read_yaml(content_dir / "schema/safety_constraints.yaml")
    vocab = read_yaml(content_dir / "prompts/vocabulary.yaml")
    constraints = safety.get("constraints") if isinstance(safety, dict) else None
    if not isinstance(constraints, list) or len(constraints) != 9:
        raise ValueError("Expected all nine safety constraints; review rule changes separately.")
    ids = set()
    for rule in constraints:
        if (not isinstance(rule, dict) or not isinstance(rule.get("id"), str)
                or rule["id"] in ids or not isinstance(rule.get("rule"), str)
                or not rule.get("rejects") or not isinstance(rule["rejects"], list)
                or not all(isinstance(item, str) and item.strip() for item in rule["rejects"])):
            raise ValueError("Invalid or duplicate safety constraint.")
        ids.add(rule["id"])
    prompts = vocab.get("prompts") if isinstance(vocab, dict) else None
    if not isinstance(prompts, list):
        raise ValueError("Prompt vocabulary must contain a list.")
    indexed = {}
    for prompt in prompts:
        if (not isinstance(prompt, dict) or not isinstance(prompt.get("id"), str)
                or prompt["id"] in indexed or not isinstance(prompt.get("text"), str)
                or not prompt["text"].strip()
                or prompt.get("status") not in ("candidate", "kept", "dropped")):
            raise ValueError("Invalid or duplicate prompt vocabulary entry.")
        indexed[prompt["id"]] = prompt
    return constraints, indexed


def contains_phrase(text, phrase):
    """Match whole words across spaces or punctuation, without matching signal as sign."""
    words = re.findall(r"\w+", phrase.casefold())
    pattern = r"(?<!\w)" + r"[\W_]+".join(re.escape(word) for word in words) + r"(?!\w)"
    return bool(re.search(pattern, text.casefold()))


def check_step_text(text, constraints):
    """Return coarse safety/filler errors and facility warnings, never a safety certificate."""
    errors, warnings = [], []
    for rule in constraints:
        for phrase in rule["rejects"]:
            # Word boundaries avoid treating "repeat the" as "eat the".
            forms = (phrase,) + WORD_FORMS.get(phrase.casefold(), ())
            if any(contains_phrase(text, form) for form in forms):
                errors.append(f"{rule['id']}: banned phrase '{phrase}'")
    for phrase in FILLER:
        if contains_phrase(text, phrase):
            errors.append("filler: " + phrase)
    for phrase in INVENTED:
        if contains_phrase(text, phrase):
            warnings.append("unverified_feature: " + phrase)
    return errors, warnings


def check_steps(steps, age_band, constraints, prompts):
    """Check ordered steps, short youngest-band text and photo vocabulary references."""
    errors, warnings = [], []
    for index, step in enumerate(steps, 1):
        location = f"{age_band} step {index}: "
        if step["sequence"] != index:
            errors.append(location + "sequence must be consecutive from one")
        if age_band == "5-7" and len(step["prompt_text"].split()) >= 12:
            errors.append(location + "instruction must be under 12 words")
        text_errors, text_warnings = check_step_text(step["prompt_text"], constraints)
        errors.extend(location + message for message in text_errors)
        warnings.extend(location + message for message in text_warnings)
        if step["verify_mode"] == "photo":
            prompt = prompts.get(step["prompt_id"])
            if not prompt or prompt["status"] != "kept":
                errors.append(location + "photo prompt must exist with status kept")
    return errors, warnings
