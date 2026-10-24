"""
Fetch.ai Agentverse Entry Point for Deadline Guardian AI.
Initializes the autonomous agent with the Agent Chat Protocol (ACP) for ASI:One.
Supports both Agentverse Mailbox mode and local standalone mode.
"""

import argparse
import sys

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from deadline_guardian.agent.uagent_app import create_deadline_guardian_agent
from deadline_guardian.config import settings
from deadline_guardian.search.factory import get_resolved_search_mode_description


def parse_args():
    parser = argparse.ArgumentParser(description="Start Deadline Guardian AI Agent")
    parser.add_argument(
        "--mailbox",
        action="store_true",
        default=None,
        help="Force enable Agentverse Mailbox mode for ASI:One connection",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Force local-only mode (disable Agentverse mailbox)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Custom port for agent HTTP server",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force mock search provider",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Attempt live search provider using configured API keys",
    )
    args, _ = parser.parse_known_args()
    return args


def build_agent_from_args(args):
    """Resolves mailbox mode and builds the agent instance."""
    if args.local:
        is_mailbox = False
    elif args.mailbox is not None and args.mailbox:
        is_mailbox = True
    elif getattr(settings, "AGENT_MAILBOX", False):
        is_mailbox = True
    elif settings.AGENTVERSE_MAILBOX_KEY:
        val = settings.AGENTVERSE_MAILBOX_KEY.strip()
        is_mailbox = True if val.lower() in ("true", "1", "yes") else val
    else:
        is_mailbox = False

    agent = create_deadline_guardian_agent(
        port=args.port,
        mailbox=is_mailbox,
    )
    return agent, is_mailbox


def main():
    args = parse_args()

    try:
        agent, is_mailbox = build_agent_from_args(args)
    except Exception as e:
        print(f"\n❌ Error initializing agent: {e}", file=sys.stderr)
        sys.exit(1)

    search_desc = get_resolved_search_mode_description(
        force_mock=True if args.mock else None,
        force_live=True if args.live else None,
    )

    print("=" * 75)
    print("🛡️  STARTING DEADLINE GUARDIAN AI AGENT (FETCH-A-THON 3.0)")
    print("=" * 75)
    print(f"Agent Name    : {agent.name}")
    print(f"Agent Port    : {agent._port}")
    print(f"Search Mode   : {search_desc}")
    print(
        f"Mailbox Mode  : {'ENABLED (Agentverse Mailbox)' if agent._use_mailbox else 'DISABLED (Local Only)'}"
    )

    print("-" * 75)
    print(f"🔑 Agent Address : {agent.address}")
    if agent._endpoints:
        endpoint_urls = ", ".join(str(ep.url) for ep in agent._endpoints)
        print(f"📡 Registered Endpoints : {endpoint_urls}")
    else:
        print("📡 Registered Endpoints : [None - Local Only]")
    print("-" * 75)

    if agent._use_mailbox:
        print("\n🌐 AGENTVERSE MAILBOX ACTIVE:")
        print("1. Your agent is connected to the Agentverse Mailbox relay.")
        print("2. ASI:One can route chat requests directly to your agent address:")
        print(f"   {agent.address}")
        print("3. Messages are received without requiring a public inbound HTTP port.")
        print("-" * 75)
    else:
        print("\n💡 AGENTVERSE & ASI:ONE NOTICE:")
        print("1. Your agent is running in local mode (endpoints skipped).")
        print("2. To connect to ASI:One chat:")
        print("   - Run with '--mailbox' flag or set AGENT_MAILBOX=true in .env")
        print(f"   - Enter address: {agent.address} in Agentverse")
        print("-" * 75)

    print("\n🚀 Agent is listening for messages via Agent Chat Protocol (ACP)...")
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Agent shutdown gracefully.")


if __name__ == "__main__":
    main()
