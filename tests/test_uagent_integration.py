"""Integration test verifying Fetch.ai uAgent instantiation and ACP protocol handling."""
from datetime import datetime, timezone
import sys
from typing import Any
from uuid import uuid4
import pytest
from uagents import Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
)

from deadline_guardian.agent.uagent_app import create_deadline_guardian_agent
from deadline_guardian.config import settings
from run_agent import build_agent_from_args, parse_args


def test_create_deadline_guardian_agent():
    agent = create_deadline_guardian_agent(
        name="test_guardian_agent",
        seed="test_secret_seed_phrase_for_deadline_guardian_123",
        port=8099,
        mailbox=False,
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
        metadata={"status": "received"},
    )
    assert ack.acknowledged_msg_id == msg.msg_id
    assert ack.metadata["status"] == "received"


def test_agent_mailbox_configuration():
    agent = create_deadline_guardian_agent(
        name="test_mailbox_agent",
        seed="test_secret_seed_phrase_for_deadline_guardian_mailbox_123",
        port=8098,
        mailbox=True,
    )
    assert agent._use_mailbox is True
    assert len(agent._endpoints) == 1
    assert "mailbox" in agent._endpoints[0].url


def test_run_agent_cli_mailbox_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_agent.py", "--mailbox"])
    args = parse_args()
    assert args.mailbox is True

    agent, is_mailbox = build_agent_from_args(args)
    assert is_mailbox is True
    assert agent._use_mailbox is True


def test_run_agent_cli_local_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_agent.py", "--local"])
    args = parse_args()
    assert args.local is True

    agent, is_mailbox = build_agent_from_args(args)
    assert is_mailbox is False
    assert agent._use_mailbox is False


def test_run_agent_cli_defaults_to_local_when_no_credentials(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_agent.py"])
    monkeypatch.setattr(settings, "AGENT_MAILBOX", False)
    monkeypatch.setattr(settings, "AGENTVERSE_MAILBOX_KEY", None)
    args = parse_args()

    agent, is_mailbox = build_agent_from_args(args)
    assert is_mailbox is False
    assert agent._use_mailbox is False


@pytest.mark.anyio
async def test_acp_chat_message_handler_end_to_end():
    agent = create_deadline_guardian_agent(
        name="test_handler_agent",
        seed="test_secret_seed_phrase_for_acp_handler_123",
        port=8096,
        mailbox=False,
    )

    digest = Model.build_schema_digest(ChatMessage)
    assert digest in agent._signed_message_handlers
    handler = agent._signed_message_handlers[digest]

    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    class MockContext:
        def __init__(self):
            self.logger = MockLogger()
            self.sent_messages: list[tuple[str, Any]] = []

        async def send(self, destination: str, message: Any):
            self.sent_messages.append((destination, message))

    ctx = MockContext()
    sender_addr = "agent1qtestsenderaddress1234567890abcdef"
    incoming_query = "I am a 2nd year CS student in India looking for hackathons"
    incoming_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=incoming_query)],
    )

    # Directly invoke the registered async ACP handler
    await handler(ctx, sender_addr, incoming_msg)

    # 1. Assert acknowledgement was sent
    assert len(ctx.sent_messages) == 2
    ack_dest, ack_payload = ctx.sent_messages[0]
    assert ack_dest == sender_addr
    assert isinstance(ack_payload, ChatAcknowledgement)
    assert ack_payload.acknowledged_msg_id == incoming_msg.msg_id

    # 2. Assert response message was sent
    reply_dest, reply_payload = ctx.sent_messages[1]
    assert reply_dest == sender_addr
    assert isinstance(reply_payload, ChatMessage)
    assert len(reply_payload.content) > 0

    # 3. Assert report content quality
    reply_text = reply_payload.content[0].text
    assert len(reply_text) > 100
    assert any(keyword in reply_text.lower() for keyword in ["deadline", "opportunity", "hackathon", "action"])

@pytest.mark.anyio
async def test_acp_chat_message_handler_personal_deadlines():
    agent = create_deadline_guardian_agent(
        name="test_handler_agent_deadlines",
        seed="test_secret_seed_phrase_for_acp_deadlines_123",
        port=8095,
        mailbox=False,
    )

    digest = Model.build_schema_digest(ChatMessage)
    assert digest in agent._signed_message_handlers
    handler = agent._signed_message_handlers[digest]

    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    class MockContext:
        def __init__(self):
            self.logger = MockLogger()
            self.sent_messages: list[tuple[str, Any]] = []

        async def send(self, destination: str, message: Any):
            self.sent_messages.append((destination, message))

    ctx = MockContext()
    sender_addr = "agent1qtestsenderaddress1234567890abcdef"
    incoming_query = (
        "Can you keep track of my upcoming deadlines? I have a scholarship form due on the 15th "
        "and two internship applications due at the end of the month. Please remind me as each approaches."
    )
    incoming_msg = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=incoming_query)],
    )

    await handler(ctx, sender_addr, incoming_msg)

    assert len(ctx.sent_messages) == 2
    ack_dest, ack_payload = ctx.sent_messages[0]
    assert ack_dest == sender_addr
    assert isinstance(ack_payload, ChatAcknowledgement)

    reply_dest, reply_payload = ctx.sent_messages[1]
    assert reply_dest == sender_addr
    assert isinstance(reply_payload, ChatMessage)

    reply_text = reply_payload.content[0].text
    # Check that personal deadlines are recognized
    assert "Personal Deadline Tracking Report" in reply_text
    assert "Scholarship Application Form" in reply_text
    assert "Internship Application #1" in reply_text
    assert "Internship Application #2" in reply_text
    # Check that student profile is not fabricated
    assert "3rd Year Computer Science in Global" not in reply_text
    assert "Not specified" in reply_text
    # Check that tracking limitations are stated
    assert "Tracking & Reminder Limitations" in reply_text
