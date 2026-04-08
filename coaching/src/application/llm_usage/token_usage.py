"""Normalize provider usage dicts into input/output/total token counts."""


def normalize_token_counts(usage: dict[str, int]) -> tuple[int, int, int]:
    """Map mixed provider keys to (input_tokens, output_tokens, total_tokens)."""
    inp = int(
        usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or usage.get("input")
        or 0
    )
    out = int(
        usage.get("output_tokens")
        or usage.get("completion_tokens")
        or usage.get("output")
        or 0
    )
    total = int(usage.get("total_tokens") or usage.get("total") or (inp + out))
    if total == 0 and (inp > 0 or out > 0):
        total = inp + out
    return inp, out, total
