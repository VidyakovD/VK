from dataclasses import dataclass

import tiktoken


@dataclass
class Chunk:
    text: str
    index: int
    token_count: int


# Use cl100k_base — same encoding used by GPT-4o, text-embedding-3-*.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def chunk_text(
    text: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 100,
) -> list[Chunk]:
    """
    Split text into overlapping chunks measured in LLM tokens.
    Returns empty list for empty/whitespace input.
    """
    text = text.strip()
    if not text:
        return []

    tokens = _ENCODING.encode(text)
    if not tokens:
        return []

    step = max(1, chunk_size_tokens - overlap_tokens)
    chunks: list[Chunk] = []
    idx = 0
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size_tokens, len(tokens))
        slice_tokens = tokens[start:end]
        chunks.append(
            Chunk(
                text=_ENCODING.decode(slice_tokens),
                index=idx,
                token_count=len(slice_tokens),
            )
        )
        if end >= len(tokens):
            break
        start += step
        idx += 1
    return chunks


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))
