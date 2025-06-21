import re

HDR_RE = re.compile(r"^###\s+([A-Z_]+)", re.M)


def split_plan(raw: str):
    """Return (internal_blob, public_plan)."""
    if "<INTERNAL>" in raw and "</INTERNAL>" in raw:
        internal, public = raw.split("</INTERNAL>", 1)
        internal = internal.split("<INTERNAL>", 1)[1].strip()
        return internal, public.lstrip()
    return "", raw


def section(text: str, header: str) -> str:
    """
    Return the *last* block that starts with '### {header}' and ends at
    the next header.  Assumes <INTERNAL> has been stripped already.
    """
    hdr = f"### {header}"
    start = text.rfind(hdr)
    if start == -1:
        return ""
    block = text[start + len(hdr):]
    stop = HDR_RE.search(block)
    return block[: stop.start() if stop else None].strip()

