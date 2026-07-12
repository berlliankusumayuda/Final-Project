from django.db import models
from django.conf import settings
from apps.courses.models import Course, Lesson


class Quiz(models.Model):
    """Quiz associated with a course or a specific lesson."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    passing_grade = models.PositiveIntegerField(default=70, help_text="Minimum score (%) to pass")
    attempt_limit = models.PositiveIntegerField(default=3, help_text="0 = unlimited")
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text="0 = no limit")
    randomize_questions = models.BooleanField(default=False)
    randomize_choices = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[Quiz] {self.title} ({self.course.title})"

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    """Multiple-choice question belonging to a quiz."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, default="", help_text="Shown after answering")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"


class Choice(models.Model):
    """Answer choice for a question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"


class QuizAttempt(models.Model):
    """A single attempt by a student on a quiz."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    score = models.FloatField(null=True, blank=True, help_text="Score percentage 0-100")
    earned_points = models.FloatField(null=True, blank=True)
    total_points = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.student.username} – {self.quiz.title} #{self.id}"

    @property
    def attempt_number(self):
        return (
            QuizAttempt.objects.filter(student=self.student, quiz=self.quiz, id__lte=self.id).count()
        )


class AttemptAnswer(models.Model):
    """The answer a student selected for one question in an attempt."""

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempt_answers")
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempt_answers"
    )
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.FloatField(default=0)

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"Attempt#{self.attempt_id} Q#{self.question_id}"
