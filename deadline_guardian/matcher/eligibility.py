"""
Eligibility Matcher.
Compares a student profile against opportunity criteria, evaluates match score,
identifies satisfied vs missing prerequisites, and provides clear explanations.
"""

from typing import List, Optional, Tuple
from deadline_guardian.models import (
    EligibilityCheckResult,
    EligibilityStatus,
    Opportunity,
    StudentProfile,
)


class EligibilityMatcher:
    """Evaluates suitability of an opportunity for a given student profile."""

    STEM_COURSES = {
        "computer science", "cs", "it", "information technology", "software engineering",
        "data science", "artificial intelligence", "ai", "machine learning", "ml",
        "electrical", "electronics", "mechanical", "civil", "chemical", "aerospace",
        "biotechnology", "engineering", "stem", "mca", "bca"
    }

    CS_SPECIFIC_COURSES = {
        "computer science", "cs", "it", "information technology", "software engineering",
        "data science", "artificial intelligence", "ai", "machine learning", "mca", "bca"
    }

    @classmethod
    def evaluate(cls, profile: StudentProfile, opportunity: Opportunity) -> EligibilityCheckResult:
        matched: List[str] = []
        missing: List[str] = []
        warnings: List[str] = []

        # 1. Course Match (Weight: 35)
        course_score, course_match_desc, course_missing_desc = cls._check_course(profile.course, opportunity.eligible_courses)
        if course_match_desc:
            matched.append(course_match_desc)
        if course_missing_desc:
            missing.append(course_missing_desc)

        # 2. Year of Study Match (Weight: 30)
        year_score, year_match_desc, year_missing_desc = cls._check_year(profile.year_of_study, opportunity.eligible_years)
        if year_match_desc:
            matched.append(year_match_desc)
        if year_missing_desc:
            missing.append(year_missing_desc)

        # 3. Location Match (Weight: 20)
        loc_score, loc_match_desc, loc_missing_desc = cls._check_location(profile.location, opportunity.location)
        if loc_match_desc:
            matched.append(loc_match_desc)
        if loc_missing_desc:
            missing.append(loc_missing_desc)

        # 4. Interest & Domain Match (Weight: 15)
        interest_score, interest_desc = cls._check_interests(profile.interests, opportunity)
        if interest_desc:
            matched.append(interest_desc)

        # Total calculated score
        total_score = round(course_score + year_score + loc_score + interest_score, 1)

        # Check for unverified source warning
        if opportunity.verification_status.value == "UNVERIFIED_USER_INPUT":
            warnings.append("Opportunity details are from unverified input; confirm eligibility on official portal.")

        # Determine Status
        if total_score >= 75.0:
            status = EligibilityStatus.ELIGIBLE
        elif total_score >= 45.0:
            status = EligibilityStatus.PARTIALLY_ELIGIBLE
        else:
            status = EligibilityStatus.NOT_ELIGIBLE

        # Generate Human Explanation
        explanation = cls._generate_explanation(
            status=status,
            score=total_score,
            opp_title=opportunity.title,
            matched=matched,
            missing=missing,
            profile=profile,
        )

        return EligibilityCheckResult(
            opportunity_id=opportunity.id,
            opportunity_title=opportunity.title,
            status=status,
            match_score=total_score,
            matched_criteria=matched,
            missing_criteria=missing,
            warnings=warnings,
            explanation=explanation,
        )

    @classmethod
    def _check_course(cls, student_course: Optional[str], eligible_courses: List[str]) -> Tuple[float, str, str]:
        if not student_course:
            return 25.0, "Degree field not specified by student (assumed open / requires self-check)", "Verify specific degree prerequisites"

        if not eligible_courses or any(c.lower() in ("any", "all", "unspecified") for c in eligible_courses):
            return 35.0, f"Open to all degrees (Student is studying {student_course})", ""

        sc_lower = student_course.lower().strip()
        ec_lower = [c.lower() for c in eligible_courses]

        # Direct name match
        for ec in ec_lower:
            if ec in sc_lower or sc_lower in ec:
                return 35.0, f"Course Match: '{student_course}' matches target '{ec}'", ""

        # Check STEM / Engineering categories
        is_student_cs = any(kw in sc_lower for kw in cls.CS_SPECIFIC_COURSES)
        is_opp_cs_only = any("cs" in c or "computer" in c or "software" in c for c in ec_lower) and not any("stem" in c or "engineering" in c or "any" in c for c in ec_lower)

        if is_opp_cs_only and not is_student_cs:
            return 10.0, "", f"Course Gap: Requires Computer Science/IT disciplines, but student is in '{student_course}'."

        if any("stem" in c or "engineering" in c for c in ec_lower) and any(kw in sc_lower for kw in cls.STEM_COURSES):
            return 30.0, f"Course Match: '{student_course}' satisfies Engineering/STEM degree requirement.", ""

        return 5.0, "", f"Course Mismatch: Opportunity lists {eligible_courses}, student is enrolled in '{student_course}'."

    @classmethod
    def _check_year(cls, student_year: Optional[str], eligible_years: List[str]) -> Tuple[float, str, str]:
        if not student_year:
            return 20.0, "Academic year not specified by student (assumed open / requires self-check)", "Verify specific academic year prerequisites"

        if not eligible_years or any(y.lower() in ("any", "all", "unspecified") for y in eligible_years):
            return 30.0, f"Open to any academic year (Student is in {student_year})", ""

        sy_lower = student_year.lower().strip()
        ey_lower = [y.lower() for y in eligible_years]

        # Exact or substring match
        for ey in ey_lower:
            if ey in sy_lower or sy_lower in ey:
                return 30.0, f"Year Match: Student is in '{student_year}', matching target {eligible_years}.", ""

        # Pre-final year synonyms
        if "pre-final" in ey_lower and ("3rd year" in sy_lower or "third" in sy_lower):
            return 30.0, f"Year Match: 3rd Year satisfies pre-final year requirement.", ""

        return 5.0, "", f"Academic Year Gap: Opportunity targets {eligible_years}, student is currently in '{student_year}'."

    @classmethod
    def _check_location(cls, student_loc: Optional[str], opp_loc: str) -> Tuple[float, str, str]:
        opp_lower = opp_loc.lower()
        if not student_loc:
            return 15.0, "Location not specified by student (assumed eligible for global/remote)", ""

        stu_lower = student_loc.lower()

        if "global" in opp_lower or "remote" in opp_lower:
            return 20.0, f"Location Eligible: Program is open globally / remote.", ""

        if any(token in opp_lower for token in stu_lower.split()) or any(token in stu_lower for token in opp_lower.split()):
            return 20.0, f"Location Match: Student in '{student_loc}' matches requirement ({opp_loc}).", ""

        return 5.0, "", f"Geographic Constraint: Requires residence in '{opp_loc}', student is in '{student_loc}'."

    @classmethod
    def _check_interests(cls, interests: List[str], opp: Opportunity) -> Tuple[float, str]:
        if not interests:
            return 10.0, ""

        opp_text = f"{opp.title} {opp.organization} {opp.notes or ''} {' '.join(opp.eligibility_criteria)}".lower()
        matched_interests = [i for i in interests if i.lower() in opp_text]

        if matched_interests:
            return 15.0, f"Interest Alignment: Matches student interests in {', '.join(matched_interests)}."
        return 8.0, ""

    @classmethod
    def _generate_explanation(
        cls,
        status: EligibilityStatus,
        score: float,
        opp_title: str,
        matched: List[str],
        missing: List[str],
        profile: StudentProfile,
    ) -> str:
        if status == EligibilityStatus.ELIGIBLE:
            details = "; ".join(matched[:2]) if matched else "All core prerequisites met"
            return f"High Match ({score}%): You qualify well for {opp_title}. {details}."
        elif status == EligibilityStatus.PARTIALLY_ELIGIBLE:
            gaps = "; ".join(missing) if missing else "Some prerequisites need verification"
            return f"Moderate Match ({score}%): You meet several requirements for {opp_title}, but note potential barriers: {gaps}."
        else:
            gaps = "; ".join(missing) if missing else "Significant requirement mismatch"
            return f"Low Match ({score}%): You may not meet the primary eligibility criteria for {opp_title}. Reason: {gaps}."
