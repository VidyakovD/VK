import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AgentRole = Literal["consultant", "sales", "lead_qualifier", "support"]
AgentTone = Literal["formal", "friendly", "expert"]
LLMProvider = Literal["openai", "anthropic"]
FallbackAction = Literal["transfer_operator", "static_message"]


class AgentCreate(BaseModel):
    community_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    role: AgentRole
    system_prompt: str | None = None
    tone: AgentTone | None = None
    llm_provider: LLMProvider = "openai"
    llm_model: str | None = None
    temperature: Decimal = Field(default=Decimal("0.7"), ge=0, le=2)
    confidence_threshold: Decimal = Field(default=Decimal("0.6"), ge=0, le=1)
    fallback_action: FallbackAction | None = "transfer_operator"


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: AgentRole | None = None
    system_prompt: str | None = None
    tone: AgentTone | None = None
    llm_provider: LLMProvider | None = None
    llm_model: str | None = None
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    confidence_threshold: Decimal | None = Field(default=None, ge=0, le=1)
    fallback_action: FallbackAction | None = None
    is_active: bool | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    community_id: uuid.UUID
    name: str
    role: str
    system_prompt: str | None
    tone: str | None
    llm_provider: str
    llm_model: str | None
    temperature: Decimal
    confidence_threshold: Decimal
    fallback_action: str | None
    is_active: bool
    created_at: datetime


# --- Knowledge base -----------------------------------------------------------
DocumentSourceType = Literal["file", "url", "manual", "wall_post"]


class DocumentUploadFromURL(BaseModel):
    url: str = Field(min_length=1)


class DocumentUploadManual(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_text: str = Field(min_length=1)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    source_type: str
    source_url: str | None
    file_name: str | None
    file_size: int | None
    chunks_count: int | None
    qdrant_collection: str | None
    indexed_at: datetime | None
    created_at: datetime


# --- Chat ---------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatSource(BaseModel):
    text: str
    score: float
    document_id: str
    chunk_index: int


class ChatResponse(BaseModel):
    text: str
    sources: list[ChatSource]
    confidence: float
    tokens_in: int
    tokens_out: int
    credits_spent: Decimal
    model: str
    provider: str
    fallback_triggered: bool
    conversation_id: uuid.UUID
