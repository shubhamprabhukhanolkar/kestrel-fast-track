import json
import time
from typing import Type
import httpx
from pydantic import BaseModel
from backend.config import settings
from backend.database import db, now
from pydantic import ValidationError


class ProviderUnavailable(RuntimeError):
    def __init__(self, code):
        self.status_code = code
        super().__init__(f"Provider unavailable ({code})")


class LLMRouter:
    """Backend-only provider calls. Every attempt, including failures, is metered."""

    @property
    def primary_provider(self):
        return settings.primary_provider

    @property
    def primary_model(self):
        return (
            settings.gemini_model_name
            if self.primary_provider == "gemini_api"
            else settings.vertex_model_name
        )

    def _primary(self, system, payload, schema):
        return (
            self._gemini_api if self.primary_provider == "gemini_api" else self._vertex
        )(system, payload, schema)

    def probe(self, include_backup=True):
        class Probe(BaseModel):
            status: str

        results = []
        providers = [(self.primary_provider, self._primary)]
        if include_backup:
            providers.append(("groq_backup", self._groq))
        for provider, call in providers:
            start = time.perf_counter()
            try:
                result, tokens = call(
                    'Return exactly {"status":"ok"}.',
                    {"purpose": "connectivity check; no borrower data"},
                    Probe,
                )
                if result["status"] != "ok":
                    raise ValueError("Unexpected connectivity response")
                self._log(
                    None, "ProviderCheck", provider, start, "success", False, tokens
                )
                results.append(
                    {
                        "provider": provider,
                        "connected": True,
                        "latency_ms": round((time.perf_counter() - start) * 1000),
                    }
                )
            except Exception as exc:
                code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                self._log(
                    None,
                    "ProviderCheck",
                    provider,
                    start,
                    f"error_{code or type(exc).__name__}",
                    False,
                    getattr(exc, "usage_tokens", (0, 0)),
                )
                results.append(
                    {
                        "provider": provider,
                        "connected": False,
                        "error": f"{code or type(exc).__name__}",
                        "location": settings.vertex_location
                        if provider == "vertex_gemini"
                        else ("provider-managed" if provider == "gemini_api" else None),
                    }
                )
        return results

    def _log(self, case_id, agent, provider, start, status, failover, tokens=(0, 0)):
        primary = provider != "groq_backup"
        rates = (
            (settings.vertex_input_inr, settings.vertex_output_inr)
            if primary
            else (settings.groq_input_inr, settings.groq_output_inr)
        )
        if provider == "gemini_api":
            rates = (settings.gemini_input_inr, settings.gemini_output_inr)
        cost = (tokens[0] * rates[0] + tokens[1] * rates[1]) / 1_000_000
        with db() as conn:
            conn.execute(
                "INSERT INTO agent_telemetry_logs(timestamp,case_id,agent_name,provider,model_name,input_tokens,output_tokens,latency_ms,cost_inr,status,failover_triggered,mode) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    now(),
                    case_id,
                    agent,
                    provider,
                    (
                        settings.gemini_model_name
                        if provider == "gemini_api"
                        else settings.vertex_model_name
                    )
                    if primary
                    else settings.groq_model,
                    tokens[0],
                    tokens[1],
                    (time.perf_counter() - start) * 1000,
                    cost,
                    status,
                    int(failover),
                    "demo_simulation" if settings.demo_mode else "live_estimate",
                ),
            )

    def _vertex(self, system, payload, schema):
        from google import genai
        from google.genai import types

        with genai.Client(
            vertexai=True,
            project=settings.gcp_project,
            location=settings.vertex_location,
            http_options=types.HttpOptions(
                timeout=int(settings.llm_timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        ) as client:
            return self._generate_google(
                client, settings.vertex_model_name, system, payload, schema
            )

    def _gemini_api(self, system, payload, schema):
        from google import genai
        from google.genai import types

        key = settings.gemini_api_key.get_secret_value()
        if not key and settings.gemini_secret_name:
            from google.cloud import secretmanager

            key = (
                secretmanager.SecretManagerServiceClient()
                .access_secret_version(name=settings.gemini_secret_name)
                .payload.data.decode()
            )
        if not key:
            raise RuntimeError(
                "Configure GEMINI_API_KEY or GEMINI_SECRET_NAME in the backend"
            )
        if not settings.allow_nonregional_inference:
            raise RuntimeError(
                "Gemini Developer API inference requires explicit nonregional authorization"
            )
        with genai.Client(
            vertexai=False,
            api_key=key,
            http_options=types.HttpOptions(
                timeout=int(settings.llm_timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        ) as client:
            return self._generate_google(
                client, settings.gemini_model_name, system, payload, schema
            )

    def _generate_google(self, client, model, system, payload, schema):
        from google.genai import types

        response = client.models.generate_content(
            model=model,
            contents=json.dumps(payload),
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_json_schema=schema.model_json_schema(),
                temperature=0.1,
                max_output_tokens=24576 if schema.__name__ == "Extraction" else 4096,
            ),
        )
        usage = response.usage_metadata
        tokens = (
            usage.prompt_token_count or 0,
            (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0),
        )
        try:
            return schema.model_validate_json(response.text).model_dump(), tokens
        except ValidationError as exc:
            exc.usage_tokens = tokens
            raise

    def _groq(self, system, payload, schema):
        from groq import Groq

        key = settings.groq_api_key
        if not key and settings.groq_secret_name:
            from google.cloud import secretmanager

            key = (
                secretmanager.SecretManagerServiceClient()
                .access_secret_version(name=settings.groq_secret_name)
                .payload.data.decode()
            )
        if not key:
            raise RuntimeError(
                "Groq backup unavailable: configure GROQ_API_KEY or GROQ_SECRET_NAME"
            )
        with Groq(
            api_key=key, timeout=settings.llm_timeout_seconds, max_retries=0
        ) as client:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": system
                        + "\nReturn only JSON matching this schema: "
                        + json.dumps(schema.model_json_schema()),
                    },
                    {"role": "user", "content": json.dumps(payload)},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_completion_tokens=24576
                if schema.__name__ == "Extraction"
                else 4096,
            )
        usage = response.usage
        tokens = (usage.prompt_tokens, usage.completion_tokens)
        try:
            return schema.model_validate_json(
                response.choices[0].message.content
            ).model_dump(), tokens
        except ValidationError as exc:
            exc.usage_tokens = tokens
            raise

    def call(
        self,
        case_id: str,
        agent: str,
        system: str,
        payload: dict,
        schema: Type[BaseModel],
        demo_factory,
    ):
        with db() as conn:
            flags = json.loads(
                conn.execute(
                    "SELECT value FROM settings WHERE key='failover'"
                ).fetchone()[0]
            )
        provider = self.primary_provider
        failover = False
        for _ in range(2):
            start = time.perf_counter()
            try:
                if provider != "groq_backup" and (
                    flags["simulate_503"] or flags["simulate_429"]
                ):
                    raise ProviderUnavailable(503 if flags["simulate_503"] else 429)
                if settings.demo_mode:
                    result = schema.model_validate(demo_factory()).model_dump()
                    tokens = (
                        max(1, len(json.dumps(payload)) // 4),
                        max(1, len(json.dumps(result)) // 4),
                    )
                else:
                    result, tokens = (
                        self._primary if provider != "groq_backup" else self._groq
                    )(system, payload, schema)
                self._log(case_id, agent, provider, start, "success", failover, tokens)
                return result
            except Exception as exc:
                code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                retryable = (
                    code in (429, 500, 503, 504)
                    or isinstance(exc, (TimeoutError, httpx.TimeoutException))
                    or type(exc).__name__
                    in ("APITimeoutError", "DeadlineExceeded", "ReadTimeout")
                )
                will_failover = provider != "groq_backup" and retryable
                self._log(
                    case_id,
                    agent,
                    provider,
                    start,
                    f"error_{code or type(exc).__name__}",
                    will_failover or failover,
                    getattr(exc, "usage_tokens", (0, 0)),
                )
                if not will_failover:
                    raise
                provider, failover = "groq_backup", True
        raise RuntimeError("Both providers unavailable")


llm = LLMRouter()
