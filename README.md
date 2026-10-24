# 🛡️ Deadline Guardian AI

> **Fetch-A-Thon 3.0 Project**  
> An autonomous AI agent designed for **Agentverse** and **ASI:One** using the official **Agent Chat Protocol (ACP)** to help college students discover scholarships, internships, and hackathons, verify eligibility, track critical application deadlines, and generate prioritized, actionable checklists.

---

## 🌟 Overview & Problem Statement

College students miss high-value scholarships, internships, and hackathons every semester not because they lack talent, but because:
1. **Deadlines are fragmented** across dozens of university portals, corporate blogs, and PDF bulletins.
2. **Hidden prerequisites** (e.g. minimum CGPA, specific academic years, demographic criteria) lead to wasted applications.
3. **High lead-time documents** (e.g., official college transcripts from university exam cells, professor recommendation letters / LORs) take 7–14 days to obtain, causing students to miss cutoffs even if they know about the opportunity.
4. **Unverified info and hallucinations** run rampant on social media and web forums with outdated or fictitious deadlines.

**Deadline Guardian AI** solves this by pairing structured opportunity discovery with deterministic eligibility matching, source verification tagging, and deadline-urgent action planning.

---

## 🏗️ Architecture & Clean Separation of Concerns

The project follows a clean, modular Python architecture separating business logic from the agent communication layer:

```
Deadline Guardian AI/
│
├── deadline_guardian/            # Core business logic package
│   ├── models.py                 # Pydantic v2 schemas (Profile, Opportunity, Eligibility, Checklist)
│   ├── config.py                 # Environment configuration & credential detection
│   │
│   ├── search/                   # Opportunity Discovery Engine
│   │   ├── base.py               # BaseSearchProvider abstract class
│   │   ├── sample_data.py        # Curated authoritative benchmark opportunities
│   │   ├── mock_provider.py      # Offline mock & testing provider
│   │   ├── tavily_provider.py    # Live web search integration (Tavily AI Search)
│   │   ├── serper_provider.py    # Live web search integration (Google Serper)
│   │   └── factory.py            # Search provider factory with auto-fallback
│   │
│   ├── extractor/                # Parser & Web Extraction
│   │   ├── parser.py             # OpportunityExtractor (dates, documents, eligibility parser)
│   │   └── url_fetcher.py        # Web scraper for user-submitted URLs & notices
│   │
│   ├── matcher/                  # Eligibility Evaluation Engine
│   │   └── eligibility.py        # Course, year, location, and interest scoring with explanations
│   │
│   ├── checklist/                # Urgency & Checklist Engine
│   │   └── generator.py          # Prioritized action generator (lead-time sorting & deadlines)
│   │
│   ├── service.py                # Central workflow coordinator
│   │
│   └── agent/                    # Autonomous Agent Layer
│       ├── chat_adapter.py       # Natural language parser & Markdown response builder
│       └── uagent_app.py         # Official Fetch.ai uAgent with Agent Chat Protocol (ACP)
│
├── tests/                        # Comprehensive test suite (32 unit/integration tests)
│   ├── test_models.py
│   ├── test_search.py
│   ├── test_extractor.py
│   ├── test_matcher.py
│   ├── test_checklist.py
│   ├── test_service.py
│   ├── test_chat_adapter.py
│   └── test_uagent_integration.py
│
├── cli.py                        # Local CLI & Interactive demonstration tool
├── run_agent.py                  # Fetch.ai uAgent runner for Agentverse & ASI:One
├── requirements.txt              # Production dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Documentation
```

---

## 🛠️ Windows PowerShell Quickstart

### Step 1: Activate Virtual Environment

Open Windows PowerShell in the project directory:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

### Step 3: Run the Test Suite

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

### Step 4: Run the Local Interactive Demo

```powershell
.\.venv\Scripts\python.exe cli.py --interactive
```

### Step 5: Launch the Fetch.ai Autonomous Agent

```powershell
.\.venv\Scripts\python.exe run_agent.py
```
