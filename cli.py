"""
Command Line Interface (CLI) for Deadline Guardian AI.
Allows developers and students to run the assistant locally without requiring an active uAgents daemon.
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

from deadline_guardian.agent.chat_adapter import ChatAdapter
from deadline_guardian.models import OpportunityType, StudentProfile
from deadline_guardian.service import DeadlineGuardianService


def run_interactive():
    print("=" * 70)
    print("🛡️  DEADLINE GUARDIAN AI - INTERACTIVE ADVISOR")
    print("=" * 70)
    print("Answer a few quick questions to discover opportunities & get your checklist:\n")

    course = input("Your Course/Degree (e.g. Computer Science, Mechanical Eng) [Computer Science]: ").strip() or "Computer Science"
    year = input("Year of Study (e.g. 1st Year, 2nd Year, 3rd Year, Final Year) [3rd Year]: ").strip() or "3rd Year"
    location = input("Location / Country [India]: ").strip() or "India"
    interests_str = input("Interests (comma separated, e.g. AI, Web3, Open Source) [AI, Open Source]: ").strip() or "AI, Open Source"
    interests = [i.strip() for i in interests_str.split(",") if i.strip()]

    print("\nOpportunity Types:")
    print("  1. All Opportunities (Default)")
    print("  2. Scholarships")
    print("  3. Internships")
    print("  4. Hackathons")
    type_choice = input("Select choice (1-4) [1]: ").strip() or "1"
    type_map = {
        "1": OpportunityType.ALL,
        "2": OpportunityType.SCHOLARSHIP,
        "3": OpportunityType.INTERNSHIP,
        "4": OpportunityType.HACKATHON,
    }
    opp_type = type_map.get(type_choice, OpportunityType.ALL)

    profile = StudentProfile(
        course=course,
        year_of_study=year,
        interests=interests,
        location=location,
        opportunity_type=opp_type,
    )

    print("\n⏳ Analyzing opportunities, checking eligibility, and calculating deadlines...\n")
    service = DeadlineGuardianService()
    response = service.analyze_profile(profile)

    adapter = ChatAdapter(service=service)
    markdown_output = adapter.format_response_to_markdown(response)
    print(markdown_output)


def main():
    parser = argparse.ArgumentParser(description="Deadline Guardian AI - Local CLI & Verification Tool")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive interview mode")
    parser.add_argument("--query", "-q", type=str, help="Natural language query (e.g. '3rd year CS hackathons in India')")
    parser.add_argument("--check", "-c", type=str, help="Directly check and extract a specific opportunity URL or text")
    parser.add_argument("--course", type=str, default="Computer Science", help="Student course/major")
    parser.add_argument("--year", type=str, default="3rd Year", help="Student year of study")
    parser.add_argument("--location", type=str, default="India", help="Student location")
    parser.add_argument("--type", type=str, choices=["scholarship", "internship", "hackathon", "all"], default="all", help="Opportunity type")

    args = parser.parse_args()

    adapter = ChatAdapter()

    if args.interactive:
        run_interactive()
    elif args.query:
        print(adapter.process_message(args.query))
    elif args.check:
        profile = StudentProfile(
            course=args.course,
            year_of_study=args.year,
            location=args.location,
            opportunity_type=OpportunityType(args.type),
        )
        service = DeadlineGuardianService()
        result = service.analyze_direct_opportunity(profile, args.check)
        print(adapter.format_response_to_markdown(result))
    else:
        # If no arguments provided, run interactive
        run_interactive()


if __name__ == "__main__":
    main()
