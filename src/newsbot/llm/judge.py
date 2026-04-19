from __future__ import annotations

import re


def judge_draft(draft: str, claims: dict) -> tuple[bool, str]:
    allowed_numbers = set(claims.get("numbers", []))
    draft_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", draft))
    if not draft_numbers.issubset(allowed_numbers):
        return False, "draft_contains_unseen_number"
    return True, "ok"
