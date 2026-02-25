from __future__ import annotations

from typing import Sequence

from zomato_ai.phase2.models import Restaurant, UserPreference


def build_recommendation_prompt(
    *,
    preferences: UserPreference,
    candidates: Sequence[Restaurant],
    limit: int,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for Groq LLM.

    The model is instructed to ONLY recommend from the provided candidates and
    to output strict JSON.
    """
    system_prompt = (
        "You are a restaurant recommendation assistant. "
        "You MUST ONLY recommend restaurants from the candidate list provided. "
        "Do not invent restaurants or details. "
        "Return STRICT JSON only, no markdown, no extra text."
    )

    prefs_lines: list[str] = []
    if preferences.location:
        prefs_lines.append(f"- location contains: {preferences.location}")
    if preferences.min_rating is not None:
        prefs_lines.append(f"- minimum rating: {preferences.min_rating}")
    if preferences.min_price is not None:
        prefs_lines.append(f"- minimum price: {preferences.min_price}")
    if preferences.max_price is not None:
        prefs_lines.append(f"- maximum price: {preferences.max_price}")
    if preferences.preferred_cuisines:
        prefs_lines.append(f"- preferred cuisines: {', '.join(preferences.preferred_cuisines)}")

    prefs_text = "\n".join(prefs_lines) if prefs_lines else "- (no explicit filters)"

    # Keep candidate context compact.
    candidate_lines: list[str] = []
    for r in candidates:
        candidate_lines.append(
            f"{r.id} | {r.name} | loc={r.location or ''} | cuisines={r.cuisines or ''} | "
            f"price={r.price_range if r.price_range is not None else ''} | "
            f"rating={r.rating if r.rating is not None else ''}"
        )

    candidates_text = "\n".join(candidate_lines)

    user_prompt = (
        "User preferences:\n"
        f"{prefs_text}\n\n"
        "Candidate restaurants (ID | name | location | cuisines | price | rating):\n"
        f"{candidates_text}\n\n"
        "Task:\n"
        f"- Select the best {limit} restaurants from the candidates.\n"
        "- Explain briefly why each one matches the preferences.\n"
        "- Output STRICT JSON with this schema:\n"
        '{\n'
        '  "summary": "string",\n'
        '  "recommendations": [\n'
        '    { "id": 123, "reason": "string" }\n'
        "  ]\n"
        "}\n"
    )

    return system_prompt, user_prompt

