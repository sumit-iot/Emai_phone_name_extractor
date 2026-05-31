EMAIL_REGEX = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
_PATH = r"(?:/[-\w._~:/?#\[\]@!$&'()*+,;%=]*)?"
_TLD = r"(?:com|co|in|net|org|io|edu|gov|uk|us|au|ca|de|fr|info|biz)"

URL_REGEX = (
    r"(?:"
    # Full URLs with protocol
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+" + _PATH +
    r"|"
    # www. prefix without protocol
    r"www\.[-\w]{2,}(?:\.[-\w]{2,})*\." + _TLD + _PATH +
    r"|"
    # Bare domains — negative lookbehind for @ to avoid matching email hosts
    r"(?<!@)(?<!\.)\b[-\w]{2,}(?:\.[-\w]{2,})*\." + _TLD + _PATH +
    r")"
)
PHONE_REGEX = (
    r"(?<!\d)"
    r"(?:\+?1[-.\s]?)?"
    r"(?:\(?\d{3}\)?[-.\s]?)"
    r"\d{3}[-.\s]?\d{4}"
    r"(?!\d)"
)

SEPARATORS: dict[str, str] = {
    "New Line": "\n",
    "Comma": ", ",
    "Semicolon": "; ",
    "Space": " ",
    "Pipe": " | ",
    "Tab": "\t",
}

OUTPUT_FORMATS = ["Plain Text", "CSV", "JSON", "HTML", "TSV"]
EXTRACTION_TYPES = ["Emails", "URLs", "Phone Numbers", "Names", "All"]
