"""
Vision NIM call — flood imagery -> grounded damage evidence.

Slide 2 "Today's Build": "Test a Build NVIDIA vision model on flood imagery
for grounded damage evidence."
Slide 5 step 3: "a Relay-governed vision call attaches confidence and lineage."

Route id "lifeshield-vision" is resolved by Switchyard:
  dev  -> a build.nvidia.com vision-capable NIM (e.g. a VLM such as
          nvidia/vila or similar — pick the specific model card once the
          team has tested candidates on real flood imagery; TODO)
  prod -> the equivalent NIM container self-hosted on the B300 node
"""
from __future__ import annotations

import base64
from typing import Any

from app.nvidia_runtime.relay.relay_runtime import relay_llm_call
from app.nvidia_runtime.switchyard_client import get_switchyard_client


async def assess_flood_image(
    *, image_bytes: bytes, event_id: str, prompt: str | None = None
) -> dict[str, Any]:
    """
    Returns a dict like:
      {"damage_assessment": str, "confidence": float, "raw_response": {...}}
    Wrapped in a NeMo Relay scope so the call is captured in the event's
    ATOF trajectory (see relay/relay_runtime.py) — this IS the "lineage" the
    deck refers to for the vision call.
    """
    b64 = base64.b64encode(image_bytes).decode("ascii")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt or (
                    "Assess flood damage severity in this image. Return a "
                    "brief structured description and do not speculate "
                    "beyond what is visible."
                )},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ],
        }
    ]

    async def _call() -> dict[str, Any]:
        client = get_switchyard_client()
        return await client.chat_completion(route="lifeshield-vision", messages=messages)

    raw = await relay_llm_call(
        scope_name="vision.flood_damage_assessment",
        event_id=event_id,
        call=_call,
    )

    # TODO: parse structured confidence out of the model response once the
    # team settles on a response schema / function-calling contract.
    text = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
    return {"damage_assessment": text, "confidence": None, "raw_response": raw}
