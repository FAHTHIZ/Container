# SPDX-License-Identifier: Apache-2.0
"""Authenticated compute capability inventory."""

from fastapi import APIRouter, Depends

from container_api.dependencies import get_current_user
from container_api.hardware import collect_capabilities
from container_api.models import User

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/capabilities")
def system_capabilities(user: User = Depends(get_current_user)) -> dict[str, object]:
    """Report CPU, memory, and accelerators visible to this API worker."""
    return collect_capabilities()
