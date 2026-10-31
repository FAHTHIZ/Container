# SPDX-License-Identifier: Apache-2.0
"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=256)
    display_name: str = Field(min_length=1, max_length=80)
    workspace_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=256)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    display_name: str
    created_at: datetime


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class JobCreate(BaseModel):
    kind: Literal["demo.echo", "demo.delay", "eval_run"] = "demo.echo"
    message: str = Field(default="Container worker is ready.", max_length=2000)
    delay_seconds: float = Field(default=0, ge=0, le=5)
    model_id: str | None = Field(default=None, min_length=1, max_length=36)
    eval_path: str | None = Field(default=None, min_length=1, max_length=1024)
    eval_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    kind: str
    status: str
    payload: dict
    result: dict | None
    error_message: str | None
    progress: int
    attempts: int
    cancel_requested: bool
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class JobEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    job_id: str
    event_type: str
    payload: dict
    created_at: datetime


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str
    created_at: datetime



class RegisteredModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    model_family: str | None = Field(default=None, max_length=120)
    origin: Literal["imported", "adapted", "custom"] = "imported"


class RegisteredModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    name: str
    description: str | None
    model_family: str | None
    origin: str
    created_at: datetime
    updated_at: datetime


class ModelVersionCreate(BaseModel):
    version_label: str = Field(min_length=1, max_length=80)
    artifact_id: str | None = None
    format: Literal["gguf", "safetensors", "pytorch", "onnx", "other"] = "other"
    quantization: str | None = Field(default=None, max_length=80)
    source_uri: str | None = Field(default=None, max_length=2000)
    base_model_reference: str | None = Field(default=None, max_length=255)
    license_id: str | None = Field(default=None, max_length=120)
    details: dict[str, object] = Field(default_factory=dict)


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    model_id: str
    artifact_id: str | None
    version_label: str
    format: str
    quantization: str | None
    source_uri: str | None
    base_model_reference: str | None
    license_id: str | None
    details: dict
    created_at: datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=24000)


class ChatCompletionRequest(BaseModel):
    conversation_id: str | None = None
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ChatCompletionRead(BaseModel):
    conversation_id: str
    message: ChatMessage
    model: str


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    sequence_no: int
    role: Literal["user", "assistant"]
    content: str
    model: str | None
