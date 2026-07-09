"""
Builds a rich student performance snapshot and asks GPT to produce
structured strengths / activities / skill_gaps in JSON.
"""
import json
import logging

from django.conf import settings
from django.db.models import Avg
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")


class AIRecommendationError(Exception):
    pass


def _build_student_snapshot(student) -> str:
    """Aggregate every piece of data available for this student into a text snapshot."""
    from feedbackapp.models import AssignmentFeedback
    from behaviorapp.models import BehaviorFeedback
    from observationsapp.models import Observation

    # ── scores ──────────────────────────────────────────────────
    feedback_qs  = AssignmentFeedback.objects.filter(student=student).order_by("-assessment_date")[:20]
    score_lines  = [f"  - {f.subject}: {f.score}/100 (CCSS {f.ccss_code or 'N/A'}, {f.assessment_date})"
                    for f in feedback_qs]

    # ── behavior ────────────────────────────────────────────────
    behavior_qs  = BehaviorFeedback.objects.filter(student=student).order_by("-event_date")[:10]
    behavior_avg = behavior_qs.aggregate(a=Avg("engagement_rating"))["a"] or 0
    behavior_summary = (f"avg engagement {behavior_avg:.1f}/5, "
                        f"incidents: {', '.join(b.incident_classification for b in behavior_qs)}")

    # ── observations ────────────────────────────────────────────
    obs_qs = Observation.objects.filter(student=student).order_by("-observation_date")[:5]
    obs_lines = [f"  - [{o.setting_tag}] {o.notes or 'No notes'}" for o in obs_qs]

    snapshot = f"""
Student: {student.student_name}
Grade: {student.student_grade}
Reading Level: {student.reading_level or 'N/A'}
Risk Status: {student.risk_status}
Avg Score: {student.avg_score or 'N/A'}
Attendance Rate: {student.attendance_rate or 'N/A'}%

Recent Assessment Scores:
{chr(10).join(score_lines) or '  No scores yet'}

Behavior Summary: {behavior_summary}

Recent Observations:
{chr(10).join(obs_lines) or '  No observations yet'}
""".strip()
    return snapshot