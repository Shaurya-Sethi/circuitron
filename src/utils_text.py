import os
from pathlib import Path

try:
    from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
    import mistral_common
except Exception:
    MistralTokenizer = None
    mistral_common = None
import tiktoken

_token_model = os.getenv("TOKEN_MODEL", "devstral-128k")
if _token_model == "devstral-128k" and MistralTokenizer and mistral_common:
    try:
        tekken_path = Path(os.path.dirname(mistral_common.__file__)) / "data" / "tekken_240911.json"
        ENC = MistralTokenizer.from_file(str(tekken_path))
    except Exception:
        ENC = tiktoken.get_encoding("cl100k_base")
else:
    try:
        ENC = tiktoken.encoding_for_model(_token_model)
    except Exception:
        ENC = tiktoken.get_encoding("cl100k_base")
MAX_CTX_TOK = int(os.getenv("MAX_CTX_TOK", 40_000))
SAFETY_MARGIN = int(os.getenv("SAFETY_MARGIN", 2_000))


def trim_to_tokens(text: str, max_tokens: int = MAX_CTX_TOK) -> str:
    toks = ENC.encode(text)
    limit = max_tokens - SAFETY_MARGIN
    if len(toks) <= limit:
        return text
    return ENC.decode(toks[:limit])
