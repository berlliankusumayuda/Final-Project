from ninja import Schema
from typing import Optional, List
from datetime import datetime


# ── Question Bank ────────────────────────────────────────────────────────────

class ChoiceIn(Schema):
    text: str
    is_correct: bool = False
    order: int = 0


class ChoiceOut(Schema):
    id: int
    text: str
    order: int
    # is_correct only shown to instructors/admin


class ChoiceWithAnswerOut(Schema):
    id: int
    text: str
    order: int
    is_correct: bool


class QuestionIn(Schema):
    text: str
    points: int = 1
    order: int = 0
    explanation: str = ""
    choices: List[ChoiceIn]


class QuestionOut(Schema):
    id: int
    text: str
    points: int
    order: int
    explanation: str
    choices: List[ChoiceOut]


class QuestionWithAnswersOut(Schema):
    id: int
    text: str
    points: int
    order: int
    explanation: str
    choices: List[ChoiceWithAnswerOut]


# ── Quiz ─────────────────────────────────────────────────────────────────────

class QuizIn(Schema):
    title: str
    description: str = ""
    passing_grade: int = 70
    attempt_limit: int = 3
    time_limit_minutes: int = 0
    randomize_questions: bool = False
    randomize_choices: bool = False
    lesson_id: Optional[int] = None


class QuizOut(Schema):
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    title: str
    description: str
    passing_grade: int
    attempt_limit: int
    time_limit_minutes: int
    randomize_questions: bool
    randomize_choices: bool
    is_active: bool
    total_questions: int
    total_points: int


class QuizDetailOut(Schema):
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    title: str
    description: str
    passing_grade: int
    attempt_limit: int
    time_limit_minutes: int
    randomize_questions: bool
    randomize_choices: bool
    is_active: bool
    questions: List[QuestionOut]


# ── Attempt ──────────────────────────────────────────────────────────────────

class AnswerIn(Schema):
    question_id: int
    choice_id: int


class SubmitQuizIn(Schema):
    answers: List[AnswerIn]


class AttemptAnswerOut(Schema):
    question_id: int
    question_text: str
    selected_choice_id: Optional[int] = None
    selected_choice_text: Optional[str] = None
    is_correct: Optional[bool] = None
    points_earned: float
    correct_choice_id: Optional[int] = None
    correct_choice_text: Optional[str] = None
    explanation: str


class AttemptOut(Schema):
    id: int
    quiz_id: int
    quiz_title: str
    status: str
    score: Optional[float] = None
    earned_points: Optional[float] = None
    total_points: Optional[float] = None
    passed: Optional[bool] = None
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None


class AttemptDetailOut(Schema):
    id: int
    quiz_id: int
    quiz_title: str
    status: str
    score: Optional[float] = None
    earned_points: Optional[float] = None
    total_points: Optional[float] = None
    passed: Optional[bool] = None
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    answers: List[AttemptAnswerOut]


class MessageOut(Schema):
    message: str


class AttemptStatusOut(Schema):
    attempts_used: int
    attempts_allowed: int
    can_attempt: bool
    best_score: Optional[float] = None
    passed: bool
