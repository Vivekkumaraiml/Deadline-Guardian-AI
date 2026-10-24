"""
Checklist Generator.
Generates a prioritized, time-sensitive application action plan based on
deadline proximity, lead-time required for documents (e.g. LORs, transcripts), and portal steps.
"""

from datetime import date
from typing import List, Optional, Tuple
from deadline_guardian.models import ChecklistItem, Opportunity, UrgencyLevel


class ChecklistGenerator:
    """Builds prioritized application checklists tailored to student deadlines."""

    LEAD_TIME_DOCS = {
        "letter of recommendation": ("Request from faculty early (requires 1-2 weeks advance notice)", "Document Gathering"),
        "lor": ("Request from faculty early (requires 1-2 weeks advance notice)", "Document Gathering"),
        "recommendation": ("Request from faculty early (requires 1-2 weeks advance notice)", "Document Gathering"),
        "transcript": ("Request official sealed/signed transcripts from college exam cell", "Document Gathering"),
        "bonafide": ("Obtain college bonafide / SPOC nomination certificate", "Document Gathering"),
        "statement of purpose": ("Draft, review, and proofread Statement of Purpose / Essay", "Profile & Writing"),
        "sop": ("Draft, review, and proofread Statement of Purpose / Essay", "Profile & Writing"),
        "proposal": ("Write and refine project proposal; seek mentor review if possible", "Profile & Writing"),
        "resume": ("Tailor Resume/CV to match opportunity keywords and technical skills", "Profile & Writing"),
        "github": ("Clean up GitHub repositories, pin best projects, and update READMEs", "Profile & Writing"),
        "portfolio": ("Ensure live demo links and portfolio website are accessible", "Profile & Writing"),
    }

    @classmethod
    def calculate_urgency_and_days(
        cls,
        opportunity: Opportunity,
        reference_date: Optional[date] = None,
    ) -> Tuple[UrgencyLevel, Optional[int]]:
        """Calculates days remaining until deadline and the resulting urgency category."""
        if opportunity.is_rolling:
            return UrgencyLevel.ROLLING, None

        if not opportunity.deadline_date:
            return UrgencyLevel.EXPIRED_OR_UNKNOWN, None

        ref = reference_date or date.today()
        delta = (opportunity.deadline_date - ref).days

        if delta < 0:
            return UrgencyLevel.EXPIRED_OR_UNKNOWN, delta
        elif delta < 7:
            return UrgencyLevel.CRITICAL, delta
        elif delta <= 30:
            return UrgencyLevel.UPCOMING, delta
        else:
            return UrgencyLevel.RELAXED, delta

    @classmethod
    def generate(
        cls,
        opportunity: Opportunity,
        reference_date: Optional[date] = None,
    ) -> Tuple[UrgencyLevel, Optional[int], List[ChecklistItem]]:
        """
        Builds a sequenced list of checklist action items prioritized by urgency and document lead time.
        """
        urgency, days_remaining = cls.calculate_urgency_and_days(opportunity, reference_date)

        items: List[ChecklistItem] = []
        step_counter = 1

        # Phase 1: High Lead-Time Documents (Faculty LOR, Exam Cell Transcripts)
        for doc in opportunity.required_documents:
            doc_lower = doc.lower()
            for kw, (action_desc, category) in cls.LEAD_TIME_DOCS.items():
                if kw in doc_lower:
                    # Avoid duplicate tasks for the same category
                    if not any(it.task == action_desc for it in items):
                        hint = "ASAP (Takes 7-14 days to issue)" if urgency in (UrgencyLevel.CRITICAL, UrgencyLevel.UPCOMING) else "Within next 2 weeks"
                        items.append(
                            ChecklistItem(
                                step_number=step_counter,
                                task=f"{doc}: {action_desc}",
                                deadline_hint=hint,
                                urgency=urgency,
                                category=category,
                                completed=False,
                            )
                        )
                        step_counter += 1
                    break

        # Phase 2: Application Portal Account & Form
        deadline_text = f"by {opportunity.deadline}" if opportunity.deadline else "before portal closes"
        items.append(
            ChecklistItem(
                step_number=step_counter,
                task=f"Create account & start application on official portal: {opportunity.official_url}",
                deadline_hint="Early registration recommended",
                urgency=urgency,
                category="Application Portal",
                completed=False,
            )
        )
        step_counter += 1

        # Phase 3: Application Steps specified by opportunity
        for step in opportunity.application_steps:
            if not any(step.lower() in it.task.lower() for it in items):
                items.append(
                    ChecklistItem(
                        step_number=step_counter,
                        task=step,
                        deadline_hint=f"Complete {deadline_text}",
                        urgency=urgency,
                        category="Application Steps",
                        completed=False,
                    )
                )
                step_counter += 1

        # Phase 4: Final Submission & Confirmation
        submission_hint = (
            "🚨 CRITICAL: Submit at least 24 hours before deadline to prevent server crashes"
            if urgency == UrgencyLevel.CRITICAL
            else f"Submit before {deadline_text}"
        )
        items.append(
            ChecklistItem(
                step_number=step_counter,
                task=f"Final Review: Double-check all uploaded documents, confirm timezone, and submit.",
                deadline_hint=submission_hint,
                urgency=urgency,
                category="Submission",
                completed=False,
            )
        )

        return urgency, days_remaining, items
