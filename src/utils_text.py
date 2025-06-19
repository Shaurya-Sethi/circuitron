import os
import tiktoken

ENC = tiktoken.encoding_for_model(os.getenv("TOKEN_MODEL", "devstral-128k"))
MAX_CTX_TOK = int(os.getenv("MAX_CTX_TOK", 40_000))
SAFETY_MARGIN = int(os.getenv("SAFETY_MARGIN", 2_000))


def trim_to_tokens(text: str, max_tokens: int = MAX_CTX_TOK) -> str:
    toks = ENC.encode(text)
    limit = max_tokens - SAFETY_MARGIN
    if len(toks) <= limit:
        return text
    return ENC.decode(toks[:limit])
