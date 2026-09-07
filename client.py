"""Thin wrapper so the harness stays provider-agnostic.

This is the only file that imports a vendor SDK. Swap the marked block for your
provider's chat-completions call and nothing else in the harness changes.
"""

import os
import time


def complete(model: str, system: str, user: str, temperature: float = 0.0) -> dict:
    """Return {text, in_tokens, out_tokens, latency_s} for one completion."""
    start = time.perf_counter()

    # --- provider-specific block: any chat-completions SDK drops in here -------
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["LLM_API_KEY"])
    resp = client.messages.create(
        model=model,
        system=system,
        max_tokens=1024,
        temperature=temperature,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text
    in_tokens, out_tokens = resp.usage.input_tokens, resp.usage.output_tokens
    # --- end provider-specific block -----------------------------------------

    return {
        "text": text,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "latency_s": time.perf_counter() - start,
    }
