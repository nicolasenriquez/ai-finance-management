"""Groq OpenAI-compatible chat-completions adapter for portfolio copilot."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import httpx

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class GroqChatCompletionsAdapterConfig:
    """Validated Groq adapter configuration for one copilot request."""

    api_key: str
    base_url: str
    model: str
    model_allowlist: frozenset[str]
    timeout_seconds: float
    max_retries: int


class GroqProviderError(ValueError):
    """Raised when Groq chat-completions request fails."""

    status_code: int | None
    provider_error_code: str | None
    error_type: str | None

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider_error_code: str | None = None,
        error_type: str | None = None,
    ) -> None:
        """Initialize provider error with normalized metadata."""

        super().__init__(message)
        self.status_code = status_code
        self.provider_error_code = provider_error_code
        self.error_type = error_type


def build_groq_chat_completions_adapter_config(
    *,
    settings: Settings | None = None,
) -> GroqChatCompletionsAdapterConfig:
    """Build one validated Groq adapter config from application settings."""

    active_settings = settings if settings is not None else get_settings()
    api_key = (
        active_settings.groq_api_key.strip()
        if isinstance(active_settings.groq_api_key, str)
        else ""
    )
    model = (
        active_settings.portfolio_ai_copilot_model.strip()
        if isinstance(active_settings.portfolio_ai_copilot_model, str)
        else ""
    )
    model_allowlist = frozenset(
        {
            model_id.strip()
            for model_id in active_settings.portfolio_ai_copilot_model_allowlist
            if model_id.strip()
        }
    )
    base_url = active_settings.portfolio_ai_copilot_groq_base_url.strip()

    if not api_key:
        raise GroqProviderError(
            "Missing required provider credential: GROQ_API_KEY.",
            status_code=500,
            provider_error_code="missing_api_key",
            error_type="ProviderConfigurationError",
        )
    if not model:
        raise GroqProviderError(
            "Missing required provider model id: PORTFOLIO_AI_COPILOT_MODEL.",
            status_code=500,
            provider_error_code="missing_model",
            error_type="ProviderConfigurationError",
        )
    if not model_allowlist:
        raise GroqProviderError(
            "Missing required provider model allowlist: PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST.",
            status_code=500,
            provider_error_code="missing_model_allowlist",
            error_type="ProviderConfigurationError",
        )
    if model not in model_allowlist:
        raise GroqProviderError(
            "Configured model is not included in PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST.",
            status_code=500,
            provider_error_code="model_not_allowlisted",
            error_type="ProviderConfigurationError",
        )
    if not base_url:
        raise GroqProviderError(
            "Missing required Groq base URL configuration.",
            status_code=500,
            provider_error_code="missing_base_url",
            error_type="ProviderConfigurationError",
        )

    return GroqChatCompletionsAdapterConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        model_allowlist=model_allowlist,
        timeout_seconds=active_settings.portfolio_ai_copilot_timeout_seconds,
        max_retries=active_settings.portfolio_ai_copilot_max_retries,
    )


async def request_groq_chat_completion(
    *,
    config: GroqChatCompletionsAdapterConfig,
    messages: Sequence[dict[str, str]],
) -> str:
    """Request one non-streaming completion from Groq chat-completions endpoint."""

    endpoint = f"{config.base_url.rstrip('/')}/openai/v1/chat/completions"
    payload: dict[str, object] = {
        "model": config.model,
        "messages": list(messages),
        "stream": False,
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
        for attempt_index in range(config.max_retries + 1):
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt_index < config.max_retries:
                    await asyncio.sleep(0.2 * float(attempt_index + 1))
                    continue
                raise GroqProviderError(
                    "Groq provider request failed due to transport timeout/unavailability.",
                    status_code=503,
                    provider_error_code="transport_unavailable",
                    error_type=type(exc).__name__,
                ) from exc

            should_retry = response.status_code in {429, 500, 502, 503, 504}
            if should_retry and attempt_index < config.max_retries:
                await asyncio.sleep(0.2 * float(attempt_index + 1))
                continue

            if response.status_code >= 400:
                raise _build_groq_provider_error_from_response(response=response)

            completion_text = _extract_completion_text(response=response)
            if completion_text.strip():
                return completion_text.strip()

            raise GroqProviderError(
                "Groq provider returned empty completion content.",
                status_code=502,
                provider_error_code="empty_completion",
                error_type="InvalidProviderResponse",
            )

    raise GroqProviderError(
        "Groq provider request failed after all retry attempts.",
        status_code=503,
        provider_error_code="retry_exhausted",
        error_type="ProviderRetryExhausted",
    )


def _build_groq_provider_error_from_response(*, response: httpx.Response) -> GroqProviderError:
    """Build one typed provider error from failing HTTP response payload."""

    error_code: str | None = None
    error_type: str | None = None
    error_message = response.text.strip() or "Groq provider returned an error response."

    try:
        response_body = response.json()
    except ValueError:
        response_body = None

    if isinstance(response_body, dict):
        typed_response_body = cast(dict[str, object], response_body)
        error_payload_candidate = typed_response_body.get("error")
        if isinstance(error_payload_candidate, dict):
            error_payload = cast(dict[str, object], error_payload_candidate)
            code_candidate = error_payload.get("code")
            type_candidate = error_payload.get("type")
            message_candidate = error_payload.get("message")
            if isinstance(code_candidate, str) and code_candidate.strip():
                error_code = code_candidate.strip()
            if isinstance(type_candidate, str) and type_candidate.strip():
                error_type = type_candidate.strip()
            if isinstance(message_candidate, str) and message_candidate.strip():
                error_message = message_candidate.strip()

    return GroqProviderError(
        error_message,
        status_code=response.status_code,
        provider_error_code=error_code,
        error_type=error_type,
    )


def _extract_completion_text(*, response: httpx.Response) -> str:
    """Extract completion content from one successful Groq response payload."""

    try:
        response_body = response.json()
    except ValueError as exc:
        raise GroqProviderError(
            "Groq provider returned non-JSON completion payload.",
            status_code=502,
            provider_error_code="invalid_json",
            error_type="InvalidProviderResponse",
        ) from exc

    if not isinstance(response_body, dict):
        raise GroqProviderError(
            "Groq provider returned invalid completion payload shape.",
            status_code=502,
            provider_error_code="invalid_payload_shape",
            error_type="InvalidProviderResponse",
        )

    typed_response_body = cast(dict[str, object], response_body)
    choices_candidate = typed_response_body.get("choices")
    if not isinstance(choices_candidate, list) or not choices_candidate:
        raise GroqProviderError(
            "Groq provider response is missing completion choices.",
            status_code=502,
            provider_error_code="missing_choices",
            error_type="InvalidProviderResponse",
        )

    typed_choices = cast(list[object], choices_candidate)
    first_choice = typed_choices[0]
    if not isinstance(first_choice, dict):
        raise GroqProviderError(
            "Groq provider response contains invalid choice payload.",
            status_code=502,
            provider_error_code="invalid_choice_payload",
            error_type="InvalidProviderResponse",
        )
    typed_first_choice = cast(dict[str, object], first_choice)
    message_candidate = typed_first_choice.get("message")
    if not isinstance(message_candidate, dict):
        raise GroqProviderError(
            "Groq provider response choice is missing message payload.",
            status_code=502,
            provider_error_code="missing_message_payload",
            error_type="InvalidProviderResponse",
        )
    typed_message = cast(dict[str, object], message_candidate)
    content_candidate = typed_message.get("content")
    if not isinstance(content_candidate, str):
        raise GroqProviderError(
            "Groq provider response message content is not a string.",
            status_code=502,
            provider_error_code="invalid_message_content",
            error_type="InvalidProviderResponse",
        )
    return content_candidate
