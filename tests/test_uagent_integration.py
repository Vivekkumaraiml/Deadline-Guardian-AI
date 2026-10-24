"""Integration test verifying Fetch.ai uAgent instantiation with ACP."""
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from deadline_guardian.agent.uagent_app import create_deadline_guardian_agent


def test_create_deadline_guardian_agent():
    agent = create_deadline_guardian_agent(
        name="test_guardian_agent",
        seed="test_secret_seed_phrase_for_deadline_guardian_123",
        port=8099,
    )
    assert agent.name == "test_guardian_agent"
    assert agent.address is not None
    assert agent.address.startswith("agent1")
    # Verify that the chat protocol was included
    protocol_digests = [proto.digest for proto in agent.protocols.values()]
    assert len(protocol_digests) > 0


def test_chat_message_models():
    # Verify ACP ChatMessage structure conforms to uagents_core spec
    msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="Find internships in India")],
    )
    assert msg.msg_id is not None
    assert len(msg.content) == 1
    assert msg.content[0].text == "Find internships in India"

    ack = ChatAcknowledgement(
        timestamp=datetime.now(timezone.utc),
        acknowledged_msg_id=msg.msg_id,
        metadata={"status": "received"}
    )
    assert ack.acknowledged_msg_id == msg.msg_id
    assert ack.metadata["status"] == "received"
