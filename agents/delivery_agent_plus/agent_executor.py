"""Executor wiring DeliveryAgentPlus to the A2A interface."""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role, TextPart

from .agent import root_agent, DeliveryAgentPlus


def _extract_text(context: RequestContext) -> str:
    if context.message and context.message.parts:
        texts = [getattr(part.root, "text", "") for part in context.message.parts if hasattr(part.root, "text")]
        return " ".join(filter(None, texts)).strip()
    return ""


class DeliveryPlusExecutor(AgentExecutor):
    """Minimal executor that delegates to DeliveryAgentPlus.handle."""

    def __init__(self, agent: DeliveryAgentPlus | None = None) -> None:
        self.agent = agent or root_agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        _ = _extract_text(context)  # Input currently unused but extracted for future use
        response = self.agent.handle()
        message = Message(
            role=Role.agent,
            parts=[Part(root=TextPart(text=response))],
            messageId=uuid4().hex,
        )
        await event_queue.enqueue_event(message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:  # pragma: no cover - no cancel flow
        return
