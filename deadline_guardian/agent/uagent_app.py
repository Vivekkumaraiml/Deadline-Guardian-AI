"""
Fetch.ai uAgent Implementation for Deadline Guardian AI.
Implements the Agent Chat Protocol (ACP) for ASI:One interoperability and Agentverse hosting.
"""

from datetime import datetime, timezone
import logging
import socket
import sys
from typing import Optional, Union
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from deadline_guardian.agent.chat_adapter import ChatAdapter
from deadline_guardian.config import settings

logger = logging.getLogger(__name__)


def find_available_port(preferred_port: int, candidate_ports=(8000, 8001, 8008, 8080, 8088)) -> int:
    """Finds an available TCP port on 0.0.0.0 to prevent WinError 10048 port-lock issues."""
    candidates = [preferred_port] + [p for p in candidate_ports if p != preferred_port]
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    return preferred_port


def create_deadline_guardian_agent(
    name: Optional[str] = None,
    seed: Optional[str] = None,
    port: Optional[int] = None,
    mailbox: Optional[Union[bool, str]] = None,
) -> Agent:
    """
    Factory creating a Fetch.ai Agent configured with the Agent Chat Protocol.
    Supports both Agentverse Mailbox mode and local standalone mode.
    """
    agent_name = name or settings.AGENT_NAME
    agent_seed = seed or settings.AGENT_SEED

    # Port selection with Windows socket conflict avoidance
    raw_port = port or settings.AGENT_PORT
    agent_port = find_available_port(raw_port)

    # Multi-tier mailbox resolution with defense-in-depth:
    if mailbox is not None:
        agent_mailbox = mailbox
    elif "--mailbox" in sys.argv:
        agent_mailbox = True
    elif "--local" in sys.argv:
        agent_mailbox = False
    elif getattr(settings, "AGENT_MAILBOX", False):
        agent_mailbox = True
    elif settings.AGENTVERSE_MAILBOX_KEY:
        val = settings.AGENTVERSE_MAILBOX_KEY.strip()
        agent_mailbox = True if val.lower() in ("true", "1", "yes") else val
    else:
        agent_mailbox = False

    kwargs = {
        "name": agent_name,
        "seed": agent_seed,
        "port": agent_port,
    }
    if agent_mailbox:
        kwargs["mailbox"] = agent_mailbox

    agent = Agent(**kwargs)

    # Instantiate the chat protocol specification
    chat_proto = Protocol(spec=chat_protocol_spec)
    adapter = ChatAdapter()

    @chat_proto.on_message(ChatMessage)
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
        ctx.logger.info(f"Received message from {sender} [msg_id: {msg.msg_id}]")

        # 1. Send receipt acknowledgement back to sender
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id,
            metadata={"agent": agent_name, "status": "processing"},
        )
        await ctx.send(sender, ack)

        # 2. Extract text from message payload
        user_text = ""
        for item in msg.content:
            if isinstance(item, TextContent):
                user_text += item.text + " "

        user_text = user_text.strip()
        ctx.logger.info(f"User query extracted: '{user_text}'")

        # 3. Process via Deadline Guardian Service
        response_text = adapter.process_message(user_text)

        # 4. Formulate outbound ChatMessage response
        reply = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
        )
        await ctx.send(sender, reply)
        ctx.logger.info(f"Sent reply to {sender}")

    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_acknowledgement(ctx: Context, sender: str, ack: ChatAcknowledgement):
        ctx.logger.info(
            f"Received acknowledgement from {sender} for message {ack.acknowledged_msg_id}"
        )

    # Include the chat protocol with publish_manifest=True for Almanac discovery
    agent.include(chat_proto, publish_manifest=True)

    return agent
