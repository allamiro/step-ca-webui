def validate_common_name(common_name: str) -> str:
    common_name = common_name.strip()
    if not common_name or len(common_name) > 255:
        raise ValueError("Invalid common_name length")
    if any(ch in common_name for ch in (";", "|", "&", "$", "`")):
        raise ValueError("Invalid character in common_name")
    return common_name


def validate_sans(sans: list[str]) -> list[str]:
    if len(sans) > 20:
        raise ValueError("Too many SAN entries")
    cleaned = []
    for san in sans:
        item = san.strip()
        if not item:
            continue
        if any(ch in item for ch in (";", "|", "&", "$", "`")):
            raise ValueError("Invalid SAN entry")
        cleaned.append(item)
    return list(dict.fromkeys(cleaned))
