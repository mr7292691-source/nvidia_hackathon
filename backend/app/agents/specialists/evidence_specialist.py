"""
Evidence specialist — the only specialist that reads the raw EvidenceRecord
(via app/agents/tools/evidence_tools.py). Summarizes source agreement for the
supervisor; never touches adapters or the internet directly.
"""
from __future__ import annotations

from typing import Any

from app.agents.tools.evidence_tools import get_evidence_record
from app.nvidia_runtime.nim_reasoning import reasoning_call

SYSTEM_PROMPT = """\
You summarize a disaster event's evidence record for a supervising agent.
Only use the evidence_record tool. Never claim a source exists that isn't in
the tool's output. Flag disagreement between sources explicitly.
"""


class EvidenceSpecialist:
    async def run(self, *, event_id: str) -> dict[str, Any]:
        record = await get_evidence_record(event_id=event_id)
        # TODO: once deepagents is pinned, wrap this in a real sub-agent with
        # the evidence_tools as its tool list instead of a single direct call.
        response = await reasoning_call(
            event_id=event_id,
            scope_name="agents.evidence_specialist",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Evidence record: {record}"},
            ],
        )
        return {"summary": response.get("choices", [{}])[0].get("message", {}).get("content", "")}


def build_evidence_specialist() -> EvidenceSpecialist:
    return EvidenceSpecialist()
