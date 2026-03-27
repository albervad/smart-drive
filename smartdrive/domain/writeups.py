from smartdrive.infrastructure.settings import (
    WRITEUPS_MAX_ITEMS,
    WRITEUPS_MAX_TAGS,
    WRITEUPS_MAX_STEPS,
)


def sanitize_text(value, max_len: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("\x00", "").strip()
    if len(value) > max_len:
        return value[:max_len]
    return value


def normalize_text_list(value, max_items: int, max_len: int) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized_items = []
    for item in value[:max_items]:
        text = sanitize_text(item, max_len)
        if text:
            normalized_items.append(text)
    return normalized_items


def normalize_writeups_data(raw_data) -> list[dict]:
    if not isinstance(raw_data, list):
        return []

    writeups = []
    seen_ids = set()

    for row in raw_data[:WRITEUPS_MAX_ITEMS]:
        if not isinstance(row, dict):
            continue

        item_id = sanitize_text(row.get("id", ""), 80)
        machine = sanitize_text(row.get("machine", ""), 120)
        if not item_id or not machine:
            continue
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)

        writeups.append({
            "id": item_id,
            "machine": machine,
            "platform": sanitize_text(row.get("platform", "N/A"), 80),
            "difficulty": sanitize_text(row.get("difficulty", "N/A"), 40),
            "date": sanitize_text(row.get("date", "Sin fecha"), 40),
            "tags": normalize_text_list(row.get("tags", []), WRITEUPS_MAX_TAGS, 40),
            "summary": sanitize_text(row.get("summary", "Sin resumen."), 1200),
            "steps": normalize_text_list(row.get("steps", []), WRITEUPS_MAX_STEPS, 300),
            "mitigation": sanitize_text(row.get("mitigation", "Sin medidas definidas."), 1200),
        })

    return writeups
