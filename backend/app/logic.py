import re
from difflib import SequenceMatcher

ROUTING = {
    "Academic": "Academic Bureau",
    "Infrastructure": "Public Grievance Redressal Cell",
    "Financial": "Finance Bureau",
    "Regulatory": "Regulation Bureau",
    "Harassment": "Public Grievance Redressal Cell",
    "Other": "Public Grievance Redressal Cell",
}
ACTIVE = ("Pending", "Under Process", "Escalated")

def route_category(category: str) -> str:
    return ROUTING.get(category, "Public Grievance Redressal Cell")

def normalize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower())}

def similarity(a: str, b: str) -> float:
    ta, tb = normalize(a), normalize(b)
    if not ta or not tb: return 0.0
    jaccard = len(ta & tb) / max(1, len(ta | tb))
    sequence = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return round(0.65 * jaccard + 0.35 * sequence, 3)
