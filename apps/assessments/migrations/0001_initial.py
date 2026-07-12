import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("courses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("passing_grade", models.PositiveIntegerField(default=70, help_text="Minimum score (%) to pass")),
                ("attempt_limit", models.PositiveIntegerField(default=3, help_text="0 = unlimited")),
                ("time_limit_minutes", models.PositiveIntegerField(default=0, help_text="0 = no limit")),
                ("randomize_questions", models.BooleanField(default=False)),
                ("randomize_choices", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to="courses.course")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quizzes", to="courses.lesson")),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("points", models.PositiveIntegerField(default=1)),
                ("order", models.PositiveIntegerField(default=0)),
                ("explanation", models.TextField(blank=True, default="", help_text="Shown after answering")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="assessments.quiz")),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Choice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=500)),
                ("is_correct", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=0)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="assessments.question")),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("in_progress", "In Progress"), ("submitted", "Submitted"), ("graded", "Graded")], default="in_progress", max_length=20)),
                ("score", models.FloatField(blank=True, help_text="Score percentage 0-100", null=True)),
                ("earned_points", models.FloatField(blank=True, null=True)),
                ("total_points", models.FloatField(blank=True, null=True)),
                ("passed", models.BooleanField(blank=True, null=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="assessments.quiz")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="AttemptAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_correct", models.BooleanField(blank=True, null=True)),
                ("points_earned", models.FloatField(default=0)),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="assessments.quizattempt")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempt_answers", to="assessments.question")),
                ("selected_choice", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="attempt_answers", to="assessments.choice")),
            ],
            options={
                "unique_together": {("attempt", "question")},
            },
        ),
    ]
