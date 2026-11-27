"""Canonical education-stage labels shared by ranking and source retrieval."""

import re


_STAGES = (
    ("diploma", r"\b(diploma|dae|technical|vocational|vet|polytechnic|associate degree|short.cycle|post.secondary)\b"),
    ("senior_secondary", r"\b(intermediate|senior secondary|upper secondary|sixth form|a.level|high school senior|class (11|12)|hssc)\b"),
    ("school", r"\b(matric\w*|secondary|gcse|class 9|class 10|middle|high school|ssc)\b"),
    ("undergraduate", r"\b(bachelor\w*|undergraduate)\b"),
    ("postgraduate", r"\b(master\w*|graduate|postgraduate|doctoral|phd)\b"),
)


def education_stage(level):
    label = str(level or "").casefold()
    return next((stage for stage, pattern in _STAGES if re.search(pattern, label)), "exploring")
