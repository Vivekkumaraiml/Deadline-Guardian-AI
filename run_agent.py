"""
Fetch.ai Agentverse Entry Point for Deadline Guardian AI.
Initializes the autonomous agent with the Agent Chat Protocol (ACP) for ASI:One.
"""

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


def main():
    print("=" * 75)
    print("🛡️  STARTING DEADLINE GUARDIAN AI AGENT (FETCH-A-THON 3.0)")
    print("=" * 75)
    print(f"Agent Name    : {settings.AGENT_NAME}")
    print(f"Agent Port    : {settings.AGENT_PORT}")
    print(f"Mock Mode     : {settings.MOCK_SEARCH_MODE}")
    print(f"Mailbox Set   : {'YES' if settings.AGENTVERSE_MAILBOX_KEY else 'NO (Local Only)'}")

    try:
        agent = create_deadline_guardian_agent()
    except Exception as e:
        print(f"\n❌ Error initializing agent: {e}", file=sys.stderr)
        sys.exit(1)

    print("-" * 75)
    print(f"🔑 Agent Address : {agent.address}")
    print("-" * 75)

    if not settings.AGENTVERSE_MAILBOX_KEY:
        print("\n💡 AGENTVERSE & ASI:ONE NOTICE:")
        print("1. Your agent is running in local mode.")
        print("2. To connect to ASI:One chat:")
        print("   - Go to https://agentverse.ai -> My Agents -> Connect Local Agent")
        print(f"   - Enter address: {agent.address}")
        print("   - Obtain your mailbox API key and set it in your .env as:")
        print("     AGENTVERSE_MAILBOX_KEY=<key>@https://agentverse.ai")
        print("   - Rerun this script to enable live routing from ASI:One chat.")
        print("-" * 75)

    print("\n🚀 Agent is listening for messages via Agent Chat Protocol (ACP)...")
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Agent shutdown gracefully.")


if __name__ == "__main__":
    main()
