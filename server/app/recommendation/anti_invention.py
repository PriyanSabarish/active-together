"""
Anti-invention rules (task B9), story 3.3.
"The explanation does not invent facilities, opening hours, cost or
 safety claims."
Any unavailable supporting value is identified as unavailable or
 omitted, never estimated."
"""
from __future__ import annotations
 
import re
 
# Grouped by the four things story 3.3 names. Terms are matched on word
# boundaries, so "cost" does not fire on "costume".
FORBIDDEN = {
    "facilities": (
        "toilet", "toilets", "restroom", "parking", "car park", "carpark",
        "bbq", "barbecue", "drinking fountain", "shelter", "shade sail",
        "changing room", "cafe", "kiosk", "ramp", "lighting", "floodlit",
        "fenced", "equipment",
    ),
    "hours": (
        "opening hours", "opens", "closes", "closed", "open until",
        "open from", "operating hours",
    ),
    "cost": (
        "free", "cost", "costs", "price", "priced", "fee", "fees",
        "ticket", "entry fee", "paid", "booking", "book ahead",
    ),
    "safety": (
        "safe", "unsafe", "safely", "safety", "dangerous", "danger",
        "hazard", "hazardous", "risk", "risky", "avoid", "warning",
        "suitable for", "unsuitable", "supervise", "supervision",
    ),
    "accessibility": (
        "accessible", "wheelchair", "pram", "step-free", "disabled access",
    ),
}
 
 
def find_violations(text: str) -> tuple[str, ...]:
    """Return "category: term" for every forbidden term found in the text."""
    lowered = text.lower()
    found = []
    for category, terms in FORBIDDEN.items():
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                found.append(f"{category}: {term}")
    return tuple(found)
 
 
def validate_text(text: str, label: str = "text") -> str:
    """Return the text unchanged, or raise listing every violation."""
    violations = find_violations(text)
    if violations:
        raise ValueError(
            f"{label} makes a claim story 3.3 forbids "
            f"({', '.join(violations)}): {text!r}"
        )
    return text