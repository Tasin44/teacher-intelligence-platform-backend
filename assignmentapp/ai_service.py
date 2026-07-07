"""
Wraps the OpenAI API to generate assignment questions.
Kept isolated from views so the AI provider can be swapped without
touching request/response handling.

Uses the centralized OpenAI client from coreapp.ai_utils for connection
reuse, automatic retry with exponential backoff, and token-usage logging.
"""
import logging

from coreapp.ai_utils import call_openai_with_retry, AIServiceError

logger = logging.getLogger("classroom_app")


class AIGenerationError(Exception):
    pass


def generate_assignment_questions(
    *,
    subject: str,
    ccss_code: str,
    difficulty: str,
    number_of_questions: int,
    instructions: str,
    grade_level: str = "",
) -> list[str]:
    """
    Calls OpenAI via centralized client and returns a list of question strings.
    Raises AIGenerationError on any failure so the caller can mark the
    assignment as failed instead of leaving it half-created.

    Improvements over the original:
    - Richer pedagogical prompt with Bloom's taxonomy and grade awareness
    - Dynamic max_tokens based on question count (avoids truncation)
    - Retry with exponential backoff (via coreapp.ai_utils)
    - Post-generation quality validation (dedup, min length, count check)
    """

    # ── Build the system prompt with pedagogical scaffolding ──
    system_prompt = (
        "You are an expert K-12 curriculum designer with deep knowledge of "
        "Common Core State Standards (CCSS), Bloom's Taxonomy, and "
        "differentiated instruction.\n\n"
        "RULES:\n"
        "1. Generate questions that are age-appropriate and aligned to the "
        "   given CCSS standard and difficulty level.\n"
        "2. Use a MIX of question types: multiple-choice, short-answer, "
        "   open-ended, and scenario-based problems.\n"
        "3. For LOW difficulty: focus on Bloom's Remember/Understand levels.\n"
        "   For MEDIUM difficulty: focus on Apply/Analyze levels.\n"
        "   For HIGH difficulty: focus on Evaluate/Create levels.\n"
        "4. Each question must be self-contained (no references to other questions).\n"
        "5. Avoid trivially similar or duplicate questions.\n"
        "6. Respond ONLY with valid JSON in this exact shape:\n"
        '   {"questions": ["question 1", "question 2", ...]}\n'
        "7. Do NOT include markdown, code fences, or any text outside the JSON.\n"
    )

    # ── Build the user prompt ──
    grade_info = f"Grade Level: {grade_level}\n" if grade_level else ""
    user_prompt = (
        f"Subject: {subject}\n"
        f"{grade_info}"
        f"CCSS Standard: {ccss_code or 'N/A'}\n"
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {number_of_questions}\n"
        f"Lesson/task instructions: {instructions or 'N/A'}"
    )

    # ── Dynamic max_tokens: ~80 tokens per question + 100 for JSON overhead ──
    dynamic_max_tokens = min(max(number_of_questions * 80 + 100, 600), 4000)

    try:
        parsed = call_openai_with_retry(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            top_p=0.9,
            max_tokens=dynamic_max_tokens,
            max_retries=3,
        )

        questions = parsed.get("questions", [])

        # ── Quality validation ──
        if not isinstance(questions, list) or not questions:
            raise AIGenerationError("AI returned no questions")

        # Clean, deduplicate, and validate
        cleaned: list[str] = []
        seen_lower: set[str] = set()
        for q in questions[:number_of_questions]:
            text = str(q).strip()
            # Reject questions that are too short to be meaningful
            if len(text) < 10:
                logger.warning("Skipping too-short AI question: %r", text)
                continue
            lower = text.lower()
            if lower in seen_lower:
                logger.warning("Skipping duplicate AI question: %r", text)
                continue
            seen_lower.add(lower)
            cleaned.append(text)

        if not cleaned:
            raise AIGenerationError(
                "AI returned questions but none passed quality validation"
            )

        if len(cleaned) < number_of_questions:
            logger.warning(
                "AI returned %d valid questions out of %d requested",
                len(cleaned),
                number_of_questions,
            )

        return cleaned

    except AIServiceError as exc:
        logger.error("AI question generation failed after retries: %s", exc)
        raise AIGenerationError(str(exc)) from exc
