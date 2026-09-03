"""
Central settings. LIFESHIELD_ENV picks the NVIDIA runtime target:

  dev  -> Switchyard route points at build.nvidia.com hosted NIM endpoints
  prod -> Switchyard route points at self-hosted NIM containers on the
          Curiosity B300 cluster (see infra/switchyard/routes.prod.toml)

Nothing in application code should ever hardcode a NIM URL — always go
through SWITCHYARD_BASE_URL so swapping environments is a config change.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    lifeshield_env: str = "dev"  # dev | prod

    # NVIDIA Build / dev NIM access
    nvidia_api_key: str = ""

    # Switchyard routing proxy (fronts all NIM traffic)
    switchyard_base_url: str = "http://localhost:8100/v1"
    switchyard_routes_file: str = "infra/switchyard/routes.dev.toml"

    # NeMo Relay
    nemo_relay_atof_output_dir: str = "./var/atof"
    nemo_relay_enable_guardrails: bool = True

    # OpenShell
    openshell_sandbox_name: str = "lifeshield-sandbox"
    # Leave empty for local dev (Docker Desktop running -> SDK's
    # from_active_cluster() reads ~/.config/openshell/active_gateway,
    # auto-created by the CLI on first `openshell sandbox create`).
    # Set to "host:port" on Curiosity v2 if the team stands up a
    # long-lived gateway job with a known address -- see
    # infra/CURIOSITY_V2_SETUP.md for what's actually verified vs. not.
    openshell_gateway_endpoint: str = ""

    # Prod-only direct targets (Switchyard config references these; app code
    # should not need them directly, kept here for infra scripts)
    b300_nim_vision_url: str = ""
    b300_nim_reasoning_url: str = ""

    # App
    database_url: str = "sqlite+aiosqlite:///./var/lifeshield.db"
    app_cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
