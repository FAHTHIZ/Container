# SPDX-License-Identifier: Apache-2.0
"""Safe metadata-only inspection for public Hugging Face model repositories."""

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from container_api.dependencies import get_current_user
from container_api.models import User

router = APIRouter(prefix="/model-sources", tags=["model sources"])


class ModelSourceRequest(BaseModel):
    url: str = Field(min_length=12, max_length=1000)


@router.post("/inspect")
def inspect_model_source(
    payload: ModelSourceRequest,
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Inspect a public Hugging Face repository without downloading or executing files."""
    parsed = urlparse(payload.url.strip())
    segments = [part for part in parsed.path.strip("/").split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.hostname != "huggingface.co"
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(segments) != 2
        or any(part in {".", ".."} for part in segments)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Use a public Hugging Face model URL in the form huggingface.co/owner/model.",
        )

    model_id = "/".join(segments)
    api_url = f"https://huggingface.co/api/models/{model_id}"
    try:
        response = httpx.get(api_url, headers={"Accept": "application/json"}, timeout=15.0)
        response.raise_for_status()
        metadata = response.json()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The model repository did not respond in time.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        detail = (
            "This repository is private, gated, or unavailable."
            if code in {401, 403, 404}
            else "The model repository could not be inspected."
        )
        raise HTTPException(
            status_code=code if code in {401, 403, 404} else 502,
            detail=detail,
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model repository returned invalid metadata.",
        ) from exc

    siblings = metadata.get("siblings") or []
    files = [
        item.get("rfilename")
        for item in siblings[:200]
        if isinstance(item, dict) and isinstance(item.get("rfilename"), str)
    ]
    card = metadata.get("cardData") or {}
    return {
        "source": "huggingface",
        "model_id": metadata.get("id") or model_id,
        "name": (metadata.get("id") or model_id).split("/")[-1],
        "pipeline_tag": metadata.get("pipeline_tag"),
        "library_name": metadata.get("library_name"),
        "license": card.get("license"),
        "downloads": metadata.get("downloads"),
        "likes": metadata.get("likes"),
        "gated": metadata.get("gated", False),
        "private": metadata.get("private", False),
        "files": files,
        "file_count": len(siblings),
        "inspection_only": True,
        "note": "Metadata inspected only. No model files were downloaded or executed.",
    }
