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


def generate_ai_recommendation(student) -> dict:
    """
    Returns dict with keys: current_strengths, recommended_activities, skill_gaps
    Each value is a newline-joined string of 5 bullet points.
    """
    snapshot = _build_student_snapshot(student)
    system_prompt = (
        "You are an expert K-12 educational coach. Analyse the student data and respond "
        "ONLY with valid JSON (no markdown) in this exact shape:\n"
        '{"current_strengths":["...","...","...","...","..."],'
        '"recommended_activities":["...","...","...","...","..."],'
        '"skill_gaps":["...","...","...","...","..."]}'
    )
    user_prompt = f"Student performance data:\n{snapshot}"
    try:
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model           = settings.OPENAI_MODEL,
            messages        = [{"role": "system", "content": system_prompt},
                               {"role": "user",   "content": user_prompt}],
            response_format = {"type": "json_object"},
            temperature     = 0.4,
            max_tokens      = 800,
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "current_strengths":      "\n".join(data.get("current_strengths",      []) [:5]),
            "recommended_activities": "\n".join(data.get("recommended_activities", [])[:5]),
            "skill_gaps":             "\n".join(data.get("skill_gaps",             [])[:5]),
        }
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        logger.error("AI recommendation failed for student %s: %s", student.pk, exc)
        raise AIRecommendationError(str(exc)) from exc