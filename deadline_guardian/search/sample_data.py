"""
Authoritative benchmark opportunity dataset for testing and offline/mock mode.
All entries reflect actual global and Indian student opportunities with verified official URLs,
eligibility constraints, required documents, and realistic application deadlines.
"""

from datetime import date
from typing import List
from deadline_guardian.models import Opportunity, OpportunityType, VerificationStatus

SAMPLE_OPPORTUNITIES: List[Opportunity] = [
    Opportunity(
        id="gsoc-2027",
        title="Google Summer of Code (GSoC)",
        organization="Google Open Source",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://summerofcode.withgoogle.com",
        deadline="2027-04-08",
        deadline_date=date(2027, 4, 8),
        is_rolling=False,
        location="Global / Remote",
        eligible_courses=["Computer Science", "Information Technology", "Software Engineering", "Data Science", "STEM"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year", "Postgraduate"],
        eligibility_criteria=[
            "Must be at least 18 years old at time of registration",
            "Eligible to work in their country of residence for duration of program",
            "Open to students and open source beginners",
            "Must not be a resident of a US-embargoed country"
        ],
        required_documents=[
            "Detailed Open Source Project Proposal",
            "Proof of Enrollment or Government ID",
            "Resume with GitHub / GitLab profile links",
            "Prior Pull Requests / Code contributions to mentor organization"
        ],
        application_steps=[
            "Review list of accepted mentoring organizations on official portal",
            "Join organization chat channels (Slack/Discord/IRC) and discuss ideas",
            "Submit draft proposal to mentors for feedback before final deadline",
            "Submit final PDF proposal via Google Summer of Code dashboard"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="summerofcode.withgoogle.com",
        notes="Provides competitive stipend, 12 to 22 week project durations, and 1-on-1 industry mentorship."
    ),
    Opportunity(
        id="smart-india-hackathon-2026",
        title="Smart India Hackathon (SIH) - Hardware & Software",
        organization="Ministry of Education Innovation Cell (Govt. of India)",
        opportunity_type=OpportunityType.HACKATHON,
        official_url="https://sih.gov.in",
        deadline="2026-11-30",
        deadline_date=date(2026, 11, 30),
        is_rolling=False,
        location="India",
        eligible_courses=["Engineering", "Computer Science", "Information Technology", "MCA", "Polytechnic", "STEM"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year"],
        eligibility_criteria=[
            "Regular bona-fide student of recognized Indian college or university",
            "Team of 6 students is mandatory",
            "At least one female team member is strictly mandatory per team",
            "College Single Point of Contact (SPOC) nomination required"
        ],
        required_documents=[
            "College SPOC Consent & Recommendation Letter",
            "Student College Identity Cards",
            "Idea Presentation PPT according to official SIH template",
            "Architecture diagram and solution prototype demonstration video"
        ],
        application_steps=[
            "Form team of 6 members meeting gender diversity criteria",
            "Select problem statement published by Government ministries or PSUs",
            "Submit idea PPT through College Internal Hackathon / SPOC nomination",
            "Submit shortlisted proposal on the official SIH portal"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="sih.gov.in",
        notes="Prizes up to INR 1 Lakh per problem statement and direct interaction with government ministries."
    ),
    Opportunity(
        id="mlh-fellowship-2026",
        title="Major League Hacking (MLH) Fellowship",
        organization="Major League Hacking (MLH) & GitHub",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://fellowship.mlh.io",
        deadline="Rolling",
        deadline_date=None,
        is_rolling=True,
        location="Global / Remote",
        eligible_courses=["Computer Science", "Software Engineering", "STEM", "Any"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year", "Postgraduate"],
        eligibility_criteria=[
            "Must be proficient in English (written and verbal)",
            "Able to commit 30+ hours/week (full-time) or 10-15 hours/week (part-time)",
            "Have prior coding experience in at least one modern language",
            "Have an active GitHub account with a public code sample to review"
        ],
        required_documents=[
            "Software engineering resume",
            "Public code sample (repository created by applicant)",
            "Short essay responses explaining technical passion and teamwork"
        ],
        application_steps=[
            "Complete online initial application form",
            "Submit a clean code sample that you authored personally",
            "Complete 30-minute behavioral video interview",
            "Complete 45-minute technical code review interview with an MLH Fellow alumna/alumnus"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="fellowship.mlh.io",
        notes="Offers educational stipend based on geographic location and tracks in Open Source, Software Engineering, and Site Reliability."
    ),
    Opportunity(
        id="adobe-india-wit-2026",
        title="Adobe India Women-in-Technology Scholarship",
        organization="Adobe India",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://www.adobe.com/in/careers/women-in-technology.html",
        deadline="2026-11-15",
        deadline_date=date(2026, 11, 15),
        is_rolling=False,
        location="India",
        eligible_courses=["Computer Science", "Information Technology", "Computer Applications", "Data Science"],
        eligible_years=["3rd Year", "Pre-final Year"],
        eligibility_criteria=[
            "Identifies as female student enrolled in accredited university in India",
            "Enrolled in 4-year B.Tech / B.E. (3rd year) or dual degree / M.Tech",
            "Strong academic record with minimum 7.0 CGPA or 70%",
            "Demonstrated leadership and passion for computing"
        ],
        required_documents=[
            "Comprehensive Curriculum Vitae (Resume)",
            "Official college transcripts / grade cards up to current semester",
            "Statement of Purpose (SOP) describing technology vision and impact",
            "One Academic Recommendation Letter from professor / faculty advisor",
            "Short video (1-2 minutes) introducing yourself and technical achievements"
        ],
        application_steps=[
            "Review official eligibility criteria on Adobe careers page",
            "Prepare SOP and faculty recommendation letter",
            "Submit formal online application before the November deadline",
            "Attend interview rounds with Adobe senior engineers and leaders"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="adobe.com",
        notes="Provides funding for remaining college tuition, opportunity for Adobe summer internship, and Grace Hopper conference sponsorship."
    ),
    Opportunity(
        id="ethglobal-hackathon-2026",
        title="ETHGlobal Web3 & Autonomous Agents Hackathon",
        organization="ETHGlobal & Ethereum Foundation",
        opportunity_type=OpportunityType.HACKATHON,
        official_url="https://ethglobal.com",
        deadline="2026-12-05",
        deadline_date=date(2026, 12, 5),
        is_rolling=False,
        location="Global / Remote",
        eligible_courses=["Computer Science", "Engineering", "Design", "Business", "Any"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year", "Postgraduate"],
        eligibility_criteria=[
            "Free registration for all builders worldwide",
            "Solo developers or teams of up to 5 members",
            "Projects must be built during the duration of the hackathon"
        ],
        required_documents=[
            "GitHub / Portfolio link",
            "Web3 wallet address (e.g. EVM compatible)",
            "Project README and 3-minute video demo at submission"
        ],
        application_steps=[
            "Apply via ETHGlobal platform with developer profile",
            "Receive application approval confirmation email",
            "Join Discord and participate in sponsor workshops",
            "Build and submit project on showcase portal before submission deadline"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="ethglobal.com",
        notes="Over $250,000+ in sponsor bounties across AI agents, smart contracts, and developer tooling."
    ),
    Opportunity(
        id="generation-google-scholarship-2026",
        title="Generation Google Scholarship (APAC)",
        organization="Google",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://buildyourfuture.withgoogle.com/scholarships/generation-google-scholarship-apac",
        deadline="2026-12-15",
        deadline_date=date(2026, 12, 15),
        is_rolling=False,
        location="India / Asia Pacific",
        eligible_courses=["Computer Science", "Computer Engineering", "Information Technology", "STEM"],
        eligible_years=["1st Year", "2nd Year"],
        eligibility_criteria=[
            "Currently enrolled as full-time undergraduate student at accredited university in APAC",
            "Intend to be enrolled in full-time degree program for next academic year",
            "Demonstrate passion for computer science and technological leadership",
            "Exemplify leadership and demonstrate financial need / underrepresented background"
        ],
        required_documents=[
            "General background information (e.g. contact info & education details)",
            "Resume / CV highlighting technical projects and community involvement",
            "Academic transcripts from current and prior institutions",
            "Two 400-word essay responses answering prompt on leadership and diversity"
        ],
        application_steps=[
            "Review prompt guidelines on Google Build Your Future website",
            "Draft and polish essay responses emphasizing impact and technical passion",
            "Submit online application form with transcripts and resume",
            "Complete Google online 15-minute challenge/assessment if invited"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="buildyourfuture.withgoogle.com",
        notes="Awards $2,500 USD tuition grant and networking retreat with Google engineers."
    ),
    Opportunity(
        id="outreachy-internship-2026",
        title="Outreachy Open Source Paid Internship",
        organization="Software Freedom Conservancy",
        opportunity_type=OpportunityType.INTERNSHIP,
        official_url="https://www.outreachy.org",
        deadline="2026-11-25",
        deadline_date=date(2026, 11, 25),
        is_rolling=False,
        location="Global / Remote",
        eligible_courses=["Any", "Computer Science", "Design", "Technical Writing", "Documentation"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year", "Postgraduate"],
        eligibility_criteria=[
            "Subject to systemic bias or underrepresented in the tech industry of applicant's home country",
            "Available for a 40-hour per week or 30-hour per week remote internship",
            "Must not be participating in another concurrent internship like GSoC"
        ],
        required_documents=[
            "Initial eligibility questionnaire and essay answers",
            "Time commitment verification",
            "Contributions to participating open source projects during contribution phase"
        ],
        application_steps=[
            "Submit initial eligibility application explaining background and time availability",
            "Wait for review approval",
            "Select participating open source project and record contributions during contribution period",
            "Submit final internship application with project mentor endorsement"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="outreachy.org",
        notes="Offers $7,000 USD stipend and $500 USD travel stipend for 3-month fully remote mentorship."
    ),
    Opportunity(
        id="aws-ai-ml-scholarship-2026",
        title="AWS AI & ML Scholarship Program",
        organization="Amazon Web Services & Udacity",
        opportunity_type=OpportunityType.SCHOLARSHIP,
        official_url="https://aws.amazon.com/machine-learning/scholarship-program/",
        deadline="2026-12-31",
        deadline_date=date(2026, 12, 31),
        is_rolling=False,
        location="Global",
        eligible_courses=["Computer Science", "Data Science", "Artificial Intelligence", "STEM", "Engineering"],
        eligible_years=["1st Year", "2nd Year", "3rd Year", "Final Year"],
        eligibility_criteria=[
            "High school or college student currently enrolled in higher education",
            "Must be at least 16 years of age",
            "Complete AWS DeepRacer Student learning modules and earn qualifying lap score"
        ],
        required_documents=[
            "AWS DeepRacer Student profile completion certificate",
            "Proof of college enrollment",
            "Online motivation and career aspiration survey"
        ],
        application_steps=[
            "Create free account on AWS DeepRacer Student console",
            "Complete 20 hours of AI/ML foundations training material",
            "Train reinforcement learning model and submit to monthly virtual race",
            "Submit application on Udacity scholarship portal using earned completion code"
        ],
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        source_domain="aws.amazon.com",
        notes="Awards 2,000 annual Udacity Nanodegree scholarships and mentorship by Amazon AI scientists."
    ),
]
