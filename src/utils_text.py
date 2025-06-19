import os

try:
    from huggingface_hub import hf_hub_download
except Exception:
    hf_hub_download = None

try:
    from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
    import mistral_common
except Exception:
    MistralTokenizer = None
    mistral_common = None
import tiktoken

_token_model = os.getenv("TOKEN_MODEL", "devstral-small-2505")
if _token_model == "devstral-small-2505":
    if not (MistralTokenizer and mistral_common and hf_hub_download):
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
