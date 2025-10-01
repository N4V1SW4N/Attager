import logging

from typing import Any, Dict, List, Optional
import uuid

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import AgentCard, Message, TaskState, UnsupportedOperationError, TextPart
from a2a.utils.errors import ServerError
from google.adk import Runner


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Constants
DEFAULT_USER_ID = "self"


class BridgeExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent for customer management."""

    def __init__(self, runner: Runner, card: AgentCard):
        self.runner = runner
        self._card = card

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            await updater.update_status(TaskState.submitted)
        await updater.update_status(TaskState.working)
        
        response_message = Message(
            messageId=str(uuid.uuid4()),
            parts=[TextPart(text="00팀에 문의해주세요.")],
            role="agent"
        )
        
        await updater.add_artifact(response_message.parts)
        await updater.update_status(TaskState.completed, final=True)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Cancel execution for the given context (currently not fully supported)."""
        raise ServerError(error=UnsupportedOperationError())
