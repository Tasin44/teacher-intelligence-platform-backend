import json
import logging

from django.conf import settings
from django.db.models import Avg
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")


class ParentMessageError(Exception):
    pass


def _build_student_context(student) -> str:
    from feedbackapp.models import AssignmentFeedback
    from behaviorapp.models import BehaviorFeedback

    subject_avgs = (
        AssignmentFeedback.objects.filter(student=student)
        .values("subject").annotate(avg=Avg("score"))
    )
    score_lines = [f"  {r['subject']}: {r['avg']:.1f}/100" for r in subject_avgs]

    behavior_counts = {}
    for b in BehaviorFeedback.objects.filter(student=student).values("incident_classification"):
        k = b["incident_classification"]
        behavior_counts[k] = behavior_counts.get(k, 0) + 1

    return (
        f"Student: {student.student_name}\n"
        f"Grade: {student.student_grade}\n"
        f"Reading Level: {student.reading_level or 'N/A'}\n"
        f"Overall Risk Status: {student.risk_status}\n"
        f"Avg Score: {student.avg_score or 'N/A'}/100\n"
        f"Attendance Rate: {student.attendance_rate or 'N/A'}%\n"
        f"Subject Scores:\n{chr(10).join(score_lines) or '  No scores yet'}\n"
        f"Behavior Summary: {behavior_counts or 'No records'}"
    )
def generate_parent_message(student, classification: str, tone: str) -> str:
    """
    Calls OpenAI to draft a parent-facing message.
    Returns the message text string.
    """
    context = _build_student_context(student)
    tone_desc = {
        "formal":   "professional and formal, suitable for official school communication",
        "friendly": "warm, encouraging, and conversational",
    }.get(tone, "professional")

    trigger_desc = {
        "progress_update": "a general progress update covering academics and attendance",
        "concern":         "a concern about the student's performance or behaviour that needs parent attention",
        "achievement":     "celebrating a significant achievement or improvement",
    }.get(classification, "a progress update")

    system_prompt = (
        "You are a K-12 teacher drafting a parent communication. Write a single, complete message "
        f"that is {tone_desc}. The message purpose is {trigger_desc}. "
        "Use the student data provided. Respond ONLY with valid JSON: "
        '{"message": "full message text here"}'
    )
    try:
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model           = settings.OPENAI_MODEL,
            messages        = [{"role": "system", "content": system_prompt},
                               {"role": "user",   "content": context}],
            response_format = {"type": "json_object"},
            temperature     = 0.6,
            max_tokens      = 600,
        )
        return json.loads(response.choices[0].message.content)["message"]
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        logger.error("Parent message AI generation failed: %s", exc)
        raise ParentMessageError(str(exc)) from exc


def send_parent_email(to_email: str, student_name: str, message_text: str):
    """
    Stub: replace with SendGrid / AWS SES in production.
    In production also generate a PDF attachment here if required.
    """
    logger.info("[EMAIL STUB] To: %s | Student: %s | Preview: %s…",
                to_email, student_name, message_text[:80])
    # from sendgrid import SendGridAPIClient
    # ...
