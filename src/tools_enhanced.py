# src/tools_enhanced.py
import re
from typing import Optional

CURRENCY_RE = re.compile(r'([₹$€£]\s*\d+(?:[,.\d]*)|\d+\s*(?:INR|USD|EUR|GBP))', flags=re.I)

def extract_amounts(text: str):
    """
    Return list of currency-like matches e.g. ["$150", "150 INR"].
    """
    return CURRENCY_RE.findall(text or "")

def infer_priority_from_text(text: str) -> str:
    txt = (text or "").lower()
    if any(k in txt for k in ["urgent", "asap", "immediately", "important", "high priority"]):
        return "high"
    if any(k in txt for k in ["please", "when convenient", "whenever", "low", "minor"]):
        return "low"
    return "medium"

def polite_name_from_email(email: str) -> str:
    if not email:
        return ""
    name = email.split("@")[0]
    name = name.replace(".", " ").replace("_", " ").title()
    return name
