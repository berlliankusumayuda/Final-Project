import random
from ninja import Router
from ninja.errors import HttpError
from django.utils import timezone
from typing import List, Optional

from apps.courses.models import Course, Lesson, Enrollment
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer
from .schemas import (
    QuizIn, QuizOut, QuizDetailOut,
    QuestionIn, QuestionOut, QuestionWithAnswersOut,
    ChoiceOut, ChoiceWithAnswerOut,
    SubmitQuizIn, AttemptOut, AttemptDetailOut, AttemptAnswerOut,
    AttemptStatusOut, MessageOut,
)

router = Router()


def _require_enrollment(user, course_id):
    """Ensure student is enrolled in the course."""
    if not Enrollment.objects.filter(student=user, course_id=course_id, status__in=["active", "completed"]).exists():
        raise HttpError(403, "You are not enrolled in this course")


def _require_course_ownership(user, course):
    if not (user.is_admin() or course.instructor == user):
        raise HttpError(403, "Not authorized")


def _quiz_out(quiz: Quiz) -> QuizOut:
    return QuizOut(
        id=quiz.id, course_id=quiz.course_id, lesson_id=quiz.lesson_id,
        title=quiz.title, description=quiz.description,
        passing_grade=quiz.passing_grade, attempt_limit=quiz.attempt_limit,
        time_limit_minutes=quiz.time_limit_minutes,
        randomize_questions=quiz.randomize_questions,
        randomize_choices=quiz.randomize_choices,
        is_active=quiz.is_active,
        total_questions=quiz.questions.count(),
        total_points=quiz.total_points,
    )


def _question_out(q: Question, show_answers=False):
    choices_qs = list(q.choices.all())
    if show_answers:
        choices = [ChoiceWithAnswerOut(id=c.id, text=c.text, order=c.order, is_correct=c.is_correct)
                   for c in choices_qs]
        return QuestionWithAnswersOut(id=q.id, text=q.text, points=q.points, order=q.order,
                                      explanation=q.explanation, choices=choices)
    else:
        choices = [ChoiceOut(id=c.id, text=c.text, order=c.order) for c in choices_qs]
        return QuestionOut(id=q.id, text=q.text, points=q.points, order=q.order,
                           explanation=q.explanation, choices=choices)


# ── Quiz CRUD ────────────────────────────────────────────────────────────────

@router.post("/courses/{course_id}/quizzes", response=QuizOut, summary="[Instructor/Admin] Create quiz")
def create_quiz(request, course_id: int, payload: QuizIn):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    _require_course_ownership(user, course)

    lesson = None
    if payload.lesson_id:
        try:
            lesson = Lesson.objects.get(id=payload.lesson_id, section__course=course)
        except Lesson.DoesNotExist:
            raise HttpError(404, "Lesson not found in this course")

    quiz = Quiz.objects.create(
        course=course, lesson=lesson,
        title=payload.title, description=payload.description,
        passing_grade=payload.passing_grade, attempt_limit=payload.attempt_limit,
        time_limit_minutes=payload.time_limit_minutes,
        randomize_questions=payload.randomize_questions,
        randomize_choices=payload.randomize_choices,
    )
    return _quiz_out(quiz)


@router.get("/courses/{course_id}/quizzes", response=List[QuizOut], summary="List quizzes in a course")
def list_quizzes(request, course_id: int):
    user = request.auth
    # Instructors/admin see all; students must be enrolled
    if user.is_student():
        _require_enrollment(user, course_id)
    quizzes = Quiz.objects.filter(course_id=course_id, is_active=True).prefetch_related("questions")
    return [_quiz_out(q) for q in quizzes]


@router.get("/courses/{course_id}/quizzes/{quiz_id}", response=QuizDetailOut,
            summary="Get quiz with questions (student view – no answers)")
def get_quiz(request, course_id: int, quiz_id: int):
    user = request.auth
    if user.is_student():
        _require_enrollment(user, course_id)
    try:
        quiz = Quiz.objects.prefetch_related("questions__choices").get(
            id=quiz_id, course_id=course_id, is_active=True
        )
    except Quiz.DoesNotExist:
        raise HttpError(404, "Quiz not found")

    questions_qs = list(quiz.questions.prefetch_related("choices"))
    if quiz.randomize_questions:
        random.shuffle(questions_qs)

    questions_out = []
    for q in questions_qs:
        choices = list(q.choices.all())
        if quiz.randomize_choices:
            random.shuffle(choices)
        q_out = QuestionOut(
            id=q.id, text=q.text, points=q.points, order=q.order,
            explanation="",  # hide explanation before answering
            choices=[ChoiceOut(id=c.id, text=c.text, order=c.order) for c in choices],
        )
        questions_out.append(q_out)

    return QuizDetailOut(
        id=quiz.id, course_id=quiz.course_id, lesson_id=quiz.lesson_id,
        title=quiz.title, description=quiz.description,
        passing_grade=quiz.passing_grade, attempt_limit=quiz.attempt_limit,
        time_limit_minutes=quiz.time_limit_minutes,
        randomize_questions=quiz.randomize_questions,
        randomize_choices=quiz.randomize_choices,
        is_active=quiz.is_active,
        questions=questions_out,
    )


@router.put("/courses/{course_id}/quizzes/{quiz_id}", response=QuizOut,
            summary="[Instructor/Admin] Update quiz")
def update_quiz(request, course_id: int, quiz_id: int, payload: QuizIn):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
    except (Course.DoesNotExist, Quiz.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)
    for k, v in payload.dict(exclude={"lesson_id"}).items():
        setattr(quiz, k, v)
    if payload.lesson_id:
        quiz.lesson_id = payload.lesson_id
    quiz.save()
    return _quiz_out(quiz)


@router.delete("/courses/{course_id}/quizzes/{quiz_id}", response=MessageOut,
               summary="[Instructor/Admin] Delete quiz")
def delete_quiz(request, course_id: int, quiz_id: int):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
    except (Course.DoesNotExist, Quiz.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)
    quiz.delete()
    return MessageOut(message="Quiz deleted")


# ── Question Bank ────────────────────────────────────────────────────────────

@router.post("/courses/{course_id}/quizzes/{quiz_id}/questions", response=QuestionWithAnswersOut,
             summary="[Instructor/Admin] Add question with choices")
def add_question(request, course_id: int, quiz_id: int, payload: QuestionIn):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
    except (Course.DoesNotExist, Quiz.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)

    if not any(c.is_correct for c in payload.choices):
        raise HttpError(400, "At least one choice must be marked as correct")

    question = Question.objects.create(
        quiz=quiz, text=payload.text, points=payload.points,
        order=payload.order, explanation=payload.explanation,
    )
    for c in payload.choices:
        Choice.objects.create(question=question, text=c.text,
                              is_correct=c.is_correct, order=c.order)

    choices = list(question.choices.all())
    return QuestionWithAnswersOut(
        id=question.id, text=question.text, points=question.points,
        order=question.order, explanation=question.explanation,
        choices=[ChoiceWithAnswerOut(id=c.id, text=c.text, order=c.order, is_correct=c.is_correct)
                 for c in choices],
    )


@router.get("/courses/{course_id}/quizzes/{quiz_id}/questions", response=List[QuestionWithAnswersOut],
            summary="[Instructor/Admin] List questions with answers")
def list_questions(request, course_id: int, quiz_id: int):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
    except (Course.DoesNotExist, Quiz.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)

    return [
        QuestionWithAnswersOut(
            id=q.id, text=q.text, points=q.points, order=q.order, explanation=q.explanation,
            choices=[ChoiceWithAnswerOut(id=c.id, text=c.text, order=c.order, is_correct=c.is_correct)
                     for c in q.choices.all()],
        )
        for q in quiz.questions.prefetch_related("choices").all()
    ]


@router.delete("/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
               response=MessageOut, summary="[Instructor/Admin] Delete question")
def delete_question(request, course_id: int, quiz_id: int, question_id: int):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
        question = Question.objects.get(id=question_id, quiz=quiz)
    except (Course.DoesNotExist, Quiz.DoesNotExist, Question.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)
    question.delete()
    return MessageOut(message="Question deleted")


# ── Attempt Status ────────────────────────────────────────────────────────────

@router.get("/courses/{course_id}/quizzes/{quiz_id}/status", response=AttemptStatusOut,
            summary="Check how many attempts used and best score")
def attempt_status(request, course_id: int, quiz_id: int):
    user = request.auth
    _require_enrollment(user, course_id)
    try:
        quiz = Quiz.objects.get(id=quiz_id, course_id=course_id)
    except Quiz.DoesNotExist:
        raise HttpError(404, "Quiz not found")

    attempts = QuizAttempt.objects.filter(student=user, quiz=quiz, status="graded")
    count = attempts.count()
    best = attempts.order_by("-score").first()
    best_score = best.score if best else None
    passed = best.passed if best else False

    can_attempt = (quiz.attempt_limit == 0 or count < quiz.attempt_limit) and not passed

    return AttemptStatusOut(
        attempts_used=count,
        attempts_allowed=quiz.attempt_limit,
        can_attempt=can_attempt,
        best_score=best_score,
        passed=bool(passed),
    )


# ── Submit Quiz ───────────────────────────────────────────────────────────────

@router.post("/courses/{course_id}/quizzes/{quiz_id}/submit", response=AttemptDetailOut,
             summary="Submit quiz answers – auto-graded")
def submit_quiz(request, course_id: int, quiz_id: int, payload: SubmitQuizIn):
    user = request.auth
    _require_enrollment(user, course_id)

    try:
        quiz = Quiz.objects.prefetch_related("questions__choices").get(
            id=quiz_id, course_id=course_id, is_active=True
        )
    except Quiz.DoesNotExist:
        raise HttpError(404, "Quiz not found")

    # Attempt limit check
    if quiz.attempt_limit > 0:
        used = QuizAttempt.objects.filter(
            student=user, quiz=quiz, status__in=["graded", "submitted"]
        ).count()
        if used >= quiz.attempt_limit:
            raise HttpError(400, f"Attempt limit reached ({quiz.attempt_limit})")

    # Already passed?
    already_passed = QuizAttempt.objects.filter(
        student=user, quiz=quiz, status="graded", passed=True
    ).exists()
    if already_passed:
        raise HttpError(400, "You have already passed this quiz")

    # Build choice lookup
    choice_map: dict[int, Choice] = {}
    question_map: dict[int, Question] = {}
    for q in quiz.questions.all():
        question_map[q.id] = q
        for c in q.choices.all():
            choice_map[c.id] = c

    # Create attempt
    attempt = QuizAttempt.objects.create(student=user, quiz=quiz, status="graded",
                                          submitted_at=timezone.now())

    total_points = 0.0
    earned_points = 0.0
    answers_out = []

    for answer_in in payload.answers:
        q = question_map.get(answer_in.question_id)
        if not q:
            continue
        choice = choice_map.get(answer_in.choice_id)
        is_correct = bool(choice and choice.is_correct and choice.question_id == q.id)
        pts = float(q.points) if is_correct else 0.0
        total_points += float(q.points)
        earned_points += pts

        aa = AttemptAnswer.objects.create(
            attempt=attempt, question=q,
            selected_choice=choice if choice else None,
            is_correct=is_correct, points_earned=pts,
        )

        correct_choice = q.choices.filter(is_correct=True).first()
        answers_out.append(AttemptAnswerOut(
            question_id=q.id, question_text=q.text,
            selected_choice_id=choice.id if choice else None,
            selected_choice_text=choice.text if choice else None,
            is_correct=is_correct, points_earned=pts,
            correct_choice_id=correct_choice.id if correct_choice else None,
            correct_choice_text=correct_choice.text if correct_choice else None,
            explanation=q.explanation,
        ))

    # Add unsubmitted questions
    submitted_qids = {a.question_id for a in payload.answers}
    for qid, q in question_map.items():
        if qid not in submitted_qids:
            total_points += float(q.points)
            correct_choice = q.choices.filter(is_correct=True).first()
            answers_out.append(AttemptAnswerOut(
                question_id=q.id, question_text=q.text,
                selected_choice_id=None, selected_choice_text=None,
                is_correct=False, points_earned=0,
                correct_choice_id=correct_choice.id if correct_choice else None,
                correct_choice_text=correct_choice.text if correct_choice else None,
                explanation=q.explanation,
            ))

    score = round(earned_points / total_points * 100, 2) if total_points > 0 else 0
    passed = score >= quiz.passing_grade

    attempt.score = score
    attempt.earned_points = earned_points
    attempt.total_points = total_points
    attempt.passed = passed
    attempt.save()

    # Auto-generate certificate if course completed and quiz passed
    if passed:
        _maybe_generate_certificate(user, quiz.course)

    return AttemptDetailOut(
        id=attempt.id, quiz_id=quiz.id, quiz_title=quiz.title,
        status=attempt.status, score=score, earned_points=earned_points,
        total_points=total_points, passed=passed,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at, submitted_at=attempt.submitted_at,
        answers=answers_out,
    )


def _maybe_generate_certificate(user, course):
    """Trigger certificate generation if all course conditions are met."""
    from apps.certificates.models import Certificate
    from apps.certificates.service import generate_certificate

    # Already has certificate?
    if Certificate.objects.filter(student=user, course=course).exists():
        return

    # Must be enrolled and completed
    enrollment = Enrollment.objects.filter(
        student=user, course=course, status="completed"
    ).first()
    if not enrollment:
        return

    generate_certificate(user, course)


# ── Attempt History ───────────────────────────────────────────────────────────

@router.get("/courses/{course_id}/quizzes/{quiz_id}/attempts", response=List[AttemptOut],
            summary="My attempt history for a quiz")
def my_attempts(request, course_id: int, quiz_id: int):
    user = request.auth
    _require_enrollment(user, course_id)
    attempts = QuizAttempt.objects.filter(
        student=user, quiz_id=quiz_id, quiz__course_id=course_id
    ).select_related("quiz")
    result = []
    for a in attempts:
        result.append(AttemptOut(
            id=a.id, quiz_id=a.quiz_id, quiz_title=a.quiz.title,
            status=a.status, score=a.score, earned_points=a.earned_points,
            total_points=a.total_points, passed=a.passed,
            attempt_number=a.attempt_number,
            started_at=a.started_at, submitted_at=a.submitted_at,
        ))
    return result


@router.get("/courses/{course_id}/quizzes/{quiz_id}/attempts/{attempt_id}",
            response=AttemptDetailOut, summary="Get attempt detail with answers")
def get_attempt(request, course_id: int, quiz_id: int, attempt_id: int):
    user = request.auth
    try:
        attempt = QuizAttempt.objects.select_related("quiz").get(
            id=attempt_id, student=user, quiz_id=quiz_id, quiz__course_id=course_id
        )
    except QuizAttempt.DoesNotExist:
        raise HttpError(404, "Attempt not found")

    answers = AttemptAnswer.objects.filter(attempt=attempt).select_related(
        "question", "selected_choice"
    )
    answers_out = []
    for aa in answers:
        correct_choice = aa.question.choices.filter(is_correct=True).first()
        answers_out.append(AttemptAnswerOut(
            question_id=aa.question.id, question_text=aa.question.text,
            selected_choice_id=aa.selected_choice_id,
            selected_choice_text=aa.selected_choice.text if aa.selected_choice else None,
            is_correct=aa.is_correct, points_earned=aa.points_earned,
            correct_choice_id=correct_choice.id if correct_choice else None,
            correct_choice_text=correct_choice.text if correct_choice else None,
            explanation=aa.question.explanation,
        ))

    return AttemptDetailOut(
        id=attempt.id, quiz_id=attempt.quiz_id, quiz_title=attempt.quiz.title,
        status=attempt.status, score=attempt.score, earned_points=attempt.earned_points,
        total_points=attempt.total_points, passed=attempt.passed,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at, submitted_at=attempt.submitted_at,
        answers=answers_out,
    )


# ── Instructor: All attempts for a quiz ───────────────────────────────────────

@router.get("/courses/{course_id}/quizzes/{quiz_id}/all-attempts", response=List[AttemptOut],
            summary="[Instructor/Admin] All student attempts for a quiz")
def all_attempts(request, course_id: int, quiz_id: int):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
        quiz = Quiz.objects.get(id=quiz_id, course=course)
    except (Course.DoesNotExist, Quiz.DoesNotExist):
        raise HttpError(404, "Not found")
    _require_course_ownership(user, course)

    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related("quiz", "student")
    result = []
    for a in attempts:
        result.append(AttemptOut(
            id=a.id, quiz_id=a.quiz_id, quiz_title=a.quiz.title,
            status=a.status, score=a.score, earned_points=a.earned_points,
            total_points=a.total_points, passed=a.passed,
            attempt_number=a.attempt_number,
            started_at=a.started_at, submitted_at=a.submitted_at,
        ))
    return result
