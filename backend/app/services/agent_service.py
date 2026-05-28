import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIAgent, Community, KnowledgeBaseDocument, User
from app.schemas.agent import AgentCreate, AgentUpdate


async def assert_user_owns_community(
    session: AsyncSession, user: User, community_id: uuid.UUID
) -> Community:
    community = await session.get(Community, community_id)
    if community is None or community.user_id != user.id:
        raise PermissionError("Community not found or not owned by user")
    return community


async def assert_user_owns_agent(
    session: AsyncSession, user: User, agent_id: uuid.UUID
) -> AIAgent:
    agent = await session.get(AIAgent, agent_id)
    if agent is None:
        raise PermissionError("Agent not found")
    community = await session.get(Community, agent.community_id)
    if community is None or community.user_id != user.id:
        raise PermissionError("Agent not owned by user")
    return agent


async def list_agents_for_user(session: AsyncSession, user: User) -> list[AIAgent]:
    stmt = (
        select(AIAgent)
        .join(Community, Community.id == AIAgent.community_id)
        .where(Community.user_id == user.id)
        .order_by(AIAgent.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_agent(session: AsyncSession, user: User, body: AgentCreate) -> AIAgent:
    await assert_user_owns_community(session, user, body.community_id)
    agent = AIAgent(
        community_id=body.community_id,
        name=body.name,
        role=body.role,
        system_prompt=body.system_prompt,
        tone=body.tone,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        temperature=body.temperature,
        confidence_threshold=body.confidence_threshold,
        fallback_action=body.fallback_action,
    )
    session.add(agent)
    await session.flush()
    return agent


async def update_agent(
    session: AsyncSession, user: User, agent_id: uuid.UUID, body: AgentUpdate
) -> AIAgent:
    agent = await assert_user_owns_agent(session, user, agent_id)
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(agent, k, v)
    await session.flush()
    return agent


async def list_documents(
    session: AsyncSession, user: User, agent_id: uuid.UUID
) -> list[KnowledgeBaseDocument]:
    await assert_user_owns_agent(session, user, agent_id)
    stmt = (
        select(KnowledgeBaseDocument)
        .where(KnowledgeBaseDocument.agent_id == agent_id)
        .order_by(KnowledgeBaseDocument.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
