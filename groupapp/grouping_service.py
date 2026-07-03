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



def generate_groups(teacher) -> list[Group]:
    """
    Regenerates all AI groups for a teacher. Existing AI-generated groups
    are cleared and rebuilt so re-running stays idempotent.
    """
    students = list(Student.objects.filter(teacher=teacher).prefetch_related("behavior_feedback"))
    if not students:
        return []

    scored = [(_composite_score(s), s) for s in students]
    scored.sort(key=lambda pair: pair[0], reverse=True)  # O(n log n) sort by composite score

    buckets: dict[str, list] = {}
    for composite, student in scored:
        classification, tag = _classify(composite)
        buckets.setdefault(classification, []).append((student, composite))

    Group.objects.filter(teacher=teacher, generated_by_ai=True).delete()  # cascades GroupStudent

    created_groups = []
    letter_index = 0
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for threshold, classification, tag in TIERS:
        members = buckets.get(classification, [])
        if not members:
            continue
        avg = round(sum(c for _, c in members) / len(members), 2)
        group = Group.objects.create(
            teacher=teacher,
            group_name=f"Group {letters[letter_index % len(letters)]}",
            classification=classification,
            tag=tag,
            avg_score=avg,
            total_students=len(members),
            generated_by_ai=True,
        )
        letter_index += 1
        GroupStudent.objects.bulk_create([
            GroupStudent(group=group, student=s) for s, _ in members
        ])
        Student.objects.filter(pk__in=[s.pk for s, _ in members]).update(recommended_group=group)
        GroupGenerationHistory.objects.create(teacher=teacher, group=group, classification=classification)
        created_groups.append(group)

    return created_groups