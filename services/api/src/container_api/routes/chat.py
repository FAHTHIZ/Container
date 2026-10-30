# SPDX-License-Identifier: Apache-2.0
"""Conversation-first chat gateway for configured OpenAI-compatible inference services."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from container_api.config import settings
from container_api.dependencies import get_current_user
from container_api.models import User
from container_api.schemas import ChatCompletionRead, ChatCompletionRequest, ChatMessage

router = APIRouter(prefix="/chat", tags=["conversation"])


@router.get("/status")
def chat_status(user: User = Depends(get_current_user)) -> dict[str, object]:
    """Expose readiness without revealing provider credentials or endpoint secrets."""
    return {
        "configured": bool(settings.inference_base_url and settings.inference_model),
        "model": settings.inference_model or None,
        "mode": "openai-compatible",
    }


@router.post("/completions", response_model=ChatCompletionRead)
def create_completion(
    payload: ChatCompletionRequest,
    user: User = Depends(get_current_user),
) -> ChatCompletionRead:
    """Forward a bounded conversation to the operator-configured inference gateway."""
    if not settings.inference_base_url or not settings.inference_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Container Intelligence is not connected to an inference service yet. "
                "Configure CONTAINER_INFERENCE_BASE_URL and CONTAINER_INFERENCE_MODEL."
            ),
        )
    if payload.messages[-1].role != "user":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The final conversation message must be from the user.",
        )

    endpoint = settings.inference_base_url.rstrip("/") + "/chat/completions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.inference_api_key:
        headers["Authorization"] = f"Bearer {settings.inference_api_key}"
    body = {
        "model": settings.inference_model,
        "messages": [message.model_dump() for message in payload.messages],
        "stream": False,
    }
    try:
        with httpx.Client(timeout=settings.inference_timeout_seconds) as client:
            response = client.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("The inference service returned an empty response.")
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The inference service timed out. Try again.",
        ) from exc
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured inference service could not complete this request.",
        ) from exc

    return ChatCompletionRead(
        message=ChatMessage(role="assistant", content=content[:24000]),
        model=settings.inference_model,
    )
