# SPDX-License-Identifier: Apache-2.0
"""Authenticated conversations and an OpenAI-compatible inference gateway."""

import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from container_api.config import settings
from container_api.database import get_db
from container_api.dependencies import get_current_user
from container_api.models import Conversation, ConversationMessage, User, utcnow
from container_api.schemas import (
    ChatCompletionRead,
    ChatCompletionRequest,
    ChatMessage,
    ConversationMessageRead,
    ConversationRead,
)

router = APIRouter(prefix="/chat", tags=["conversation"])


def owned_conversation(db: Session, user: User, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.get("/status")
def chat_status(user: User = Depends(get_current_user)) -> dict[str, object]:
    """Expose readiness without revealing provider credentials or endpoint secrets."""
    return {
        "configured": bool(settings.inference_base_url and settings.inference_model),
        "model": settings.inference_model or None,
        "mode": "openai-compatible",
    }


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Conversation]:
    """List only the signed-in user's recent conversations."""
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    return list(db.scalars(statement).all())


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ConversationMessageRead],
)
def list_conversation_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationMessage]:
    """Read messages from a conversation owned by the current user."""
    conversation = owned_conversation(db, user, conversation_id)
    statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.sequence_no.asc())
    )
    return list(db.scalars(statement).all())


@router.post("/completions", response_model=ChatCompletionRead)
def create_completion(
    payload: ChatCompletionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatCompletionRead:
    """Persist a user turn, call the configured model, and persist its reply."""
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
    if payload.conversation_id is None and len(payload.messages) != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A new conversation must begin with one user message.",
        )

    latest_user_message = payload.messages[-1]
    if payload.conversation_id:
        conversation = owned_conversation(db, user, payload.conversation_id)
    else:
        title = latest_user_message.content.strip().replace("\n", " ")[:120]
        conversation = Conversation(user_id=user.id, title=title or "New conversation")
        db.add(conversation)
        db.flush()

    previous_statement = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.sequence_no.desc())
        .limit(39)
    )
    previous_messages = list(db.scalars(previous_statement).all())
    previous_messages.reverse()
    last_sequence = db.scalar(
        select(func.max(ConversationMessage.sequence_no)).where(
            ConversationMessage.conversation_id == conversation.id
        )
    ) or 0

    model_messages = [
        {"role": item.role, "content": item.content}
        for item in previous_messages
    ]
    model_messages.append({"role": "user", "content": latest_user_message.content})
    if sum(len(item["content"]) for item in model_messages) > 100_000:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The saved conversation is too large for this request.",
        )

    endpoint = settings.inference_base_url.rstrip("/") + "/chat/completions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.inference_api_key:
        headers["Authorization"] = f"Bearer {settings.inference_api_key}"
    body = {
        "model": settings.inference_model,
        "messages": model_messages,
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
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The inference service timed out. Try again.",
        ) from exc
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured inference service could not complete this request.",
        ) from exc

    assistant_message = content[:24000]
    db.add_all(
        [
            ConversationMessage(
                conversation_id=conversation.id,
                sequence_no=last_sequence + 1,
                role="user",
                content=latest_user_message.content,
            ),
            ConversationMessage(
                conversation_id=conversation.id,
                sequence_no=last_sequence + 2,
                role="assistant",
                content=assistant_message,
                model=settings.inference_model,
            ),
        ]
    )
    conversation.updated_at = utcnow()
    db.commit()

    return ChatCompletionRead(
        conversation_id=conversation.id,
        message=ChatMessage(role="assistant", content=assistant_message),
        model=settings.inference_model,
    )


@router.post("/completions/stream")
async def stream_completion(
    payload: ChatCompletionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream an OpenAI-compatible response as SSE and persist the completed turn."""
    if not settings.inference_base_url or not settings.inference_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Container Intelligence is not connected to an inference service yet.",
        )
    if payload.messages[-1].role != "user":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The final conversation message must be from the user.",
        )
    if payload.conversation_id is None and len(payload.messages) != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A new conversation must begin with one user message.",
        )

    latest = payload.messages[-1]
    if payload.conversation_id:
        conversation = owned_conversation(db, user, payload.conversation_id)
    else:
        title = latest.content.strip().replace("\n", " ")[:120]
        conversation = Conversation(user_id=user.id, title=title or "New conversation")
        db.add(conversation)
        db.flush()

    prior = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.id)
            .order_by(ConversationMessage.sequence_no.desc())
            .limit(39)
        ).all()
    )
    prior.reverse()
    last_sequence = db.scalar(
        select(func.max(ConversationMessage.sequence_no)).where(
            ConversationMessage.conversation_id == conversation.id
        )
    ) or 0
    model_messages = [{"role": item.role, "content": item.content} for item in prior]
    model_messages.append({"role": "user", "content": latest.content})
    if sum(len(item["content"]) for item in model_messages) > 100_000:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The saved conversation is too large for this request.",
        )

    db.add(
        ConversationMessage(
            conversation_id=conversation.id,
            sequence_no=last_sequence + 1,
            role="user",
            content=latest.content,
        )
    )
    conversation.updated_at = utcnow()
    db.commit()
    conversation_id = conversation.id

    endpoint = settings.inference_base_url.rstrip("/") + "/chat/completions"
    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    if settings.inference_api_key:
        headers["Authorization"] = f"Bearer {settings.inference_api_key}"
    body = {"model": settings.inference_model, "messages": model_messages, "stream": True}
    client = httpx.AsyncClient(timeout=settings.inference_timeout_seconds)
    try:
        request = client.build_request("POST", endpoint, headers=headers, json=body)
        upstream = await client.send(request, stream=True)
        upstream.raise_for_status()
    except httpx.TimeoutException as exc:
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The inference service timed out. Try again.",
        ) from exc
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured inference service could not start a streaming response.",
        ) from exc

    async def event_stream():
        assembled = ""
        try:
            async for line in upstream.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                except (ValueError, KeyError, IndexError, TypeError):
                    continue
                if isinstance(delta, str) and delta and len(assembled) < 24000:
                    delta = delta[: 24000 - len(assembled)]
                    assembled += delta
                    yield "event: token\ndata: " + json.dumps({"content": delta}) + "\n\n"

            if assembled.strip():
                db.add(
                    ConversationMessage(
                        conversation_id=conversation_id,
                        sequence_no=last_sequence + 2,
                        role="assistant",
                        content=assembled,
                        model=settings.inference_model,
                    )
                )
                conversation.updated_at = utcnow()
                db.commit()
                yield "event: done\ndata: " + json.dumps(
                    {"conversation_id": conversation_id, "model": settings.inference_model}
                ) + "\n\n"
            else:
                db.rollback()
                yield "event: error\ndata: " + json.dumps(
                    {"detail": "The inference service returned an empty response."}
                ) + "\n\n"
        except Exception:
            db.rollback()
            yield "event: error\ndata: " + json.dumps(
                {"detail": "The streaming response was interrupted. Retry your message."}
            ) + "\n\n"
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
