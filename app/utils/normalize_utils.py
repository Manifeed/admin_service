def normalize_file_extension(extension: str) -> str:
    normalized = extension.strip().lower()
    if not normalized:
        return ""
    return normalized if normalized.startswith(".") else f".{normalized}"
