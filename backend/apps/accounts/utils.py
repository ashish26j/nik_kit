def normalize_phone(raw):
    """Normalize a phone to '[+]digits' so the same number is one identity.

    Keeps an optional leading '+', strips spaces/dashes/parens.
    """
    raw = (raw or "").strip()
    plus = raw.startswith("+")
    digits = "".join(ch for ch in raw if ch.isdigit())
    return ("+" if plus else "") + digits
