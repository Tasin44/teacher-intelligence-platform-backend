import json
import logging

from django.conf import settings
from django.db.models import Avg
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")


class PacingError(Exception):
    pass


def generate_pacing_recommendation(assignment, teacher) -> dict:
    """
    Returns:
      curriculum_adjustment        : str  (paragraph)
      standards_coverage_checklist : list[{standard, covered, notes}]
    """
    from feedbackapp.models import AssignmentFeedback

    # Gather class-wide performance on this assignment's topic/CCSS code
    scores = list(
        AssignmentFeedback.objects.filter(assignment=assignment)
        .aggregate(avg=Avg("score"))
        .items()
    )
    avg_score = scores[0][1] if scores else None

    # All CCSS codes ever used by this teacher for this topic/subject
    from assignmentapp.models import Assignment
    all_ccss = list(
        Assignment.objects.filter(teacher=teacher, subject=assignment.subject)
        .exclude(ccss_code__isnull=True)
        .values_list("ccss_code", flat=True)
        .distinct()
    )

    system_prompt = (
        "You are a K-12 curriculum pacing expert. Given assignment data and class performance, "
        "produce:\n"
        "1. Curriculum Adjustment Recommendations (2-3 paragraphs of concrete advice)\n"
        "2. Standards Coverage Checklist (list each CCSS standard with covered:true/false and brief notes)\n"
        "Respond ONLY with valid JSON:\n"
        '{"curriculum_adjustment":"...","standards_coverage_checklist":'
        '[{"standard":"...","covered":true,"notes":"..."}]}'
    )
    user_prompt = (
        f"Assignment: {assignment.title}\n"
        f"Subject: {assignment.subject}\n"
        f"CCSS Code: {assignment.ccss_code or 'N/A'}\n"
        f"Difficulty: {assignment.ai_difficulty}\n"
        f"Instructions: {assignment.instructions or 'N/A'}\n"
        f"Class Avg Score: {avg_score or 'N/A'}\n"
        f"All CCSS codes covered in this subject so far: {', '.join(all_ccss) or 'None'}"
    )
    try:
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model           = settings.OPENAI_MODEL,
            messages        = [{"role": "system", "content": system_prompt},
                               {"role": "user",   "content": user_prompt}],
            response_format = {"type": "json_object"},
            temperature     = 0.4,
            max_tokens      = 900,
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "curriculum_adjustment":        data.get("curriculum_adjustment", ""),
            "standards_coverage_checklist": data.get("standards_coverage_checklist", []),
        }
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        logger.error("Pacing AI failed: %s", exc)
        raise PacingError(str(exc)) from exc
