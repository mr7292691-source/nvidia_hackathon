"""
Shared pytest fixtures. Points DATABASE_URL at a fresh temp SQLite file per
test session (not the dev var/lifeshield.db) so tests never depend on or
pollute local dev state.
"""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("NVIDIA_API_KEY", "test-key")
os.environ.setdefault("LIFESHIELD_ENV", "dev")

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp_db.name}"
os.environ.setdefault("NEMO_RELAY_ATOF_OUTPUT_DIR", tempfile.mkdtemp())
