from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator, SecretStr
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    gcp_project: str = "slabspro-slabsuser37"
    gcp_region: str = "asia-south1"
    vertex_location: str = "asia-south1"
    vertex_model_name: str = "gemini-3.5-flash-lite"
    primary_provider: Literal["vertex_gemini", "gemini_api"] = "gemini_api"
    gemini_model_name: str = "gemini-2.5-flash-lite"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_secret_name: str = ""
    allow_nonregional_inference: bool = True
    # Illustrative Flash-Lite paid-tier estimates at assumed INR 90/USD, not a live FX quote.
    gemini_input_inr: float = 9
    gemini_output_inr: float = 36
    groq_api_key: SecretStr = SecretStr("")
    groq_secret_name: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # Offline simulation is explicit, never a fallback for missing credentials.
    demo_mode: bool = False
    auth_mode: Literal["password", "iap", "demo"] = "password"
    app_env: Literal["local", "production"] = "local"
    seed_sample_cases: bool = True
    seed_telemetry: bool = False
    database_url: str = ""
    documents_bucket: str = ""
    task_backend: Literal["worker", "cloud_tasks"] = "worker"
    tasks_queue: str = "kestrel-pipeline"
    task_service_account: str = ""
    service_url: str = ""
    job_lease_seconds: int = 600
    job_max_attempts: int = 3
    job_retry_delay_seconds: int = 15
    enable_job_worker: bool = True
    secure_cookies: bool = False
    allow_groq_egress: bool = False
    database_path: str = "data/kestrel.db"
    document_dir: str = "data/documents"
    static_dir: str = "frontend/dist"
    session_secret: str = ""
    iap_audience: str = ""
    iap_role_map: dict[str, str] = {}
    llm_timeout_seconds: float = 60
    extraction_max_output_tokens: int = 12288
    # Explicit estimated rates, INR per million tokens; configure to contracted prices.
    vertex_input_inr: float = 44
    vertex_output_inr: float = 264
    groq_input_inr: float = 13.5
    groq_output_inr: float = 54

    @field_validator("vertex_model_name")
    @classmethod
    def approved_model(cls, value):
        if value not in {
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3-flash-preview",
        }:
            raise ValueError(
                "Use an explicitly configured model: gemini-3.5-flash-lite, gemini-2.5-flash-lite or gemini-3-flash-preview. GCP organization policy must also allow it."
            )
        return value

    @field_validator("gcp_region", "vertex_location")
    @classmethod
    def approved_region(cls, value):
        if value != "asia-south1":
            raise ValueError(
                "This lab requires asia-south1; cross-region inference is not permitted"
            )
        return value

    @model_validator(mode="after")
    def acknowledged_provider_boundary(self):
        if (
            self.primary_provider == "gemini_api"
            and not self.allow_nonregional_inference
        ):
            raise ValueError(
                "Gemini Developer API requires ALLOW_NONREGIONAL_INFERENCE=true; it has no asia-south1 inference endpoint"
            )
        return self


settings = Settings()
ROOT = Path(__file__).resolve().parent.parent
