from __future__ import annotations


def compose_post(claims: dict) -> str:
    headline = claims.get("headline", "Breaking update")
    entities = claims.get("entities", [])
    numbers = claims.get("numbers", [])

    entity_part = ", ".join(entities[:3]) if entities else "multiple tracked entities"
    number_part = f" Key figures: {', '.join(numbers[:3])}." if numbers else ""
    return (
        f"BREAKING: {headline}\n"
        f"Confirmed by monitored sources. Entities: {entity_part}.{number_part}"
    )
