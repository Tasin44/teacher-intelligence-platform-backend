"""
AI group-generation logic.

Approach: rather than calling an LLM for the actual clustering (slow,
non-deterministic, hard to audit for a grading decision), we compute a
weighted composite performance score per student from every metric the
teacher has entered (assessment average, attendance, behavior/engagement),
sort students by that score (O(n log n)), and bucket them into
classification tiers using fixed thresholds (O(n)) -- a standard
score-and-bucket technique. An optional OpenAI call can layer a short
natural-language rationale on top (see `explain_group_with_ai`), which is
the "AI" surfaced to the teacher without making the grouping itself
non-reproducible.
"""



from django.db.models import Avg

from groupapp.models import Group, GroupStudent, GroupGenerationHistory
from studentapp.models import Student

WEIGHT_SCORE = 0.5
WEIGHT_ATTENDANCE = 0.3
WEIGHT_ENGAGEMENT = 0.2

TIERS = [
    # (min_composite_inclusive, classification, tag)
    (85, Group.Classification.ADVANCE, Group.Tag.ABOVE),
    (70, Group.Classification.ON_TRACK, Group.Tag.AT),
    (50, Group.Classification.DEVELOPING, Group.Tag.APPROACHING),
    (0, Group.Classification.RISK, Group.Tag.BELOW),
]


def _composite_score(student) -> float:
    avg_score = float(student.avg_score) if student.avg_score is not None else 0.0
    attendance = float(student.attendance_rate) if student.attendance_rate is not None else 0.0
    engagement_avg = student.behavior_feedback.aggregate(a=Avg("engagement_rating"))["a"] or 0.0
    engagement_pct = engagement_avg * 20  # scale 1-5 -> 0-100
    return round(
        avg_score * WEIGHT_SCORE + attendance * WEIGHT_ATTENDANCE + engagement_pct * WEIGHT_ENGAGEMENT,
        2,
    )

def _classify(composite: float):
    for threshold, classification, tag in TIERS:
        if composite >= threshold:
            return classification, tag
    return Group.Classification.RISK, Group.Tag.BELOW



