import os
import re
from typing import Callable, Optional

try:
    from huggingface_hub import hf_hub_download as _hf_hub_download
except Exception:
    _hf_hub_download = None  # type: ignore[assignment]
hf_hub_download: Optional[Callable[..., str]] = _hf_hub_download

try:
    from mistral_common.tokens.tokenizers.mistral import MistralTokenizer  # type: ignore
    import mistral_common  # type: ignore
except Exception:
    MistralTokenizer = None
    mistral_common = None
import tiktoken

_token_model = os.getenv("TOKEN_MODEL", "devstral-small-2505")
if _token_model == "devstral-small-2505":
    if MistralTokenizer is None or mistral_common is None or hf_hub_download is None:
        raise RuntimeError(
            "mistral-common and huggingface_hub are required for devstral-small-2505"
        )
    tekken_file = hf_hub_download(
        repo_id="mistralai/Devstral-Small-2505",
        filename="tekken.json",
    )
    # Load the Tekken tokenizer per https://docs.mistral.ai/guides/tokenization/
    ENC = MistralTokenizer.from_file(tekken_file)
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


HDR = re.compile(r"^###\s+[A-Z_]+", re.M)


def extract_block(plan: str, header: str) -> str:
    """Return text under the *last* '### {header}' heading, ignoring <think>."""
    if "</think>" in plan:
        plan = plan.split("</think>", 1)[1]
    anchor = f"### {header}"
    start = plan.rfind(anchor)
    if start == -1:
        return ""
    chunk = plan[start + len(anchor):]
    nxt = HDR.search(chunk)
    return chunk[:nxt.start() if nxt else None].strip()


QUERY_RE = re.compile(r"^[A-Za-z0-9_ .+()\-|'\"^$*?\[\]]+$")
