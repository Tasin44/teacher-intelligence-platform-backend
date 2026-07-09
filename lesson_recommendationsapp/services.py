import json
import logging

from django.conf import settings
from django.db.models import Avg
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")


class LessonRecommendationError(Exception):
    pass


def generate_lesson_recommendation(assignment) -> str:
    """
    Analyses assignment feedback scores and returns a lesson recommendation
    covering struggling students (low scores) and advanced students (high scores).
    """
    from feedbackapp.models import AssignmentFeedback

    scores = list(
        AssignmentFeedback.objects
        .filter(assignment=assignment)
        .values("student__student_name", "score")
        .order_by("score")
    )
    if not scores:
        # Fall back to instruction-only recommendation when no scores exist yet
        score_summary = "No scores submitted yet."
    else:
        avg   = sum(s["score"] for s in scores) / len(scores)
        low   = [s for s in scores if s["score"] < 60]
        high  = [s for s in scores if s["score"] >= 85]
        score_summary = (
            f"Class average: {avg:.1f}/100\n"
            f"Struggling (<60): {', '.join(s['student__student_name'] for s in low) or 'None'}\n"
            f"Advanced (>=85):  {', '.join(s['student__student_name'] for s in high) or 'None'}"
        )

    system_prompt = (
        "You are an expert K-12 instructional coach. Based on the assignment details and score "
        "summary, provide differentiated lesson recommendations for both struggling and advanced "
        "students. Respond ONLY with valid JSON:\n"
        '{"recommendation": "detailed multi-line recommendation here"}'
    )
    user_prompt = (
        f"Assignment: {assignment.title}\n"
        f"Subject: {assignment.subject}\n"
        f"CCSS Code: {assignment.ccss_code or 'N/A'}\n"
        f"Difficulty: {assignment.ai_difficulty}\n"
        f"Instructions: {assignment.instructions or 'N/A'}\n\n"
        f"Score Summary:\n{score_summary}"
    )
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
        return json.loads(response.choices[0].message.content)["recommendation"]
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        logger.error("Lesson recommendation AI failed: %s", exc)
        raise LessonRecommendationError(str(exc)) from exc
