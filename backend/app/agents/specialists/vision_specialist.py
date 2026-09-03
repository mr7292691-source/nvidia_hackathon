"""
Vision specialist — wraps the Relay-governed vision NIM call
(app/nvidia_runtime/nim_vision.py) for the submitted field image, attaching
confidence and lineage per slide 5 step 3.
"""
from __future__ import annotations

from typing import Any

from app.agents.tools.evidence_tools import get_field_image


class VisionSpecialist:
    async def run(self, *, event_id: str) -> dict[str, Any]:
        image = await get_field_image(event_id=event_id)
        if image is None:
            return {"damage_assessment": None, "confidence": None, "note": "no field image submitted"}

        from app.nvidia_runtime.nim_vision import assess_flood_image

        result = await assess_flood_image(image_bytes=image, event_id=event_id)
        return result


def build_vision_specialist() -> VisionSpecialist:
    return VisionSpecialist()
