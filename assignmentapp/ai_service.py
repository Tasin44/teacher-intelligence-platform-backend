"""
Wraps the OpenAI API to generate assignment questions.
Kept isolated from views so the AI provider can be swapped without
touching request/response handling.
"""
import json
import logging

from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger("classroom_app")


class AIGenerationError(Exception):
    pass


def _client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise AIGenerationError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_assignment_questions(*, subject: str, ccss_code: str, difficulty: str,
                                   number_of_questions: int, instructions: str) -> list[str]:
    """
    Calls OpenAI in JSON mode and returns a list of question strings.
    Raises AIGenerationError on any failure so the caller can mark the
    assignment as failed instead of leaving it half-created.
    """
    system_prompt = (
        "You are an expert K-12 curriculum designer. Generate classroom "
        "assignment questions strictly aligned to the given CCSS standard "
        "and difficulty level. Respond ONLY with valid JSON, no markdown, "
        'in this exact shape: {"questions": ["question 1", "question 2", ...]}'
    )
    user_prompt = (
        f"Subject: {subject}\n"
        f"CCSS Standard: {ccss_code or 'N/A'}\n"
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {number_of_questions}\n"
        f"Lesson/task instructions: {instructions or 'N/A'}"
    )
    try:
        client = _client()
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        questions = parsed.get("questions", [])
        if not isinstance(questions, list) or not questions:
            raise AIGenerationError("AI returned no questions")
        return [str(q).strip() for q in questions[:number_of_questions]]
    except (OpenAIError, json.JSONDecodeError, KeyError) as exc:
        logger.error("AI question generation failed: %s", exc)
        raise AIGenerationError(str(exc)) from exc
