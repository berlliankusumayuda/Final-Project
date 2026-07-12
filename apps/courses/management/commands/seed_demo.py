"""
Management command: seed_demo
Creates demo users, courses, lessons, quizzes with questions, and sample enrollments.
Run: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for Simple LMS"

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Seeding demo data...")

        # ── Users ────────────────────────────────────────────────────────────
        admin = self._get_or_create_user("admin", "admin@lms.id", "Admin@1234", "admin",
                                          "Super", "Admin")
        instructor = self._get_or_create_user("instructor1", "instructor@lms.id", "Instructor@1234",
                                               "instructor", "Budi", "Santoso")
        student = self._get_or_create_user("student1", "student@lms.id", "Student@1234",
                                            "student", "Sari", "Dewi")
        student2 = self._get_or_create_user("student2", "student2@lms.id", "Student@1234",
                                             "student", "Andi", "Pratama")

        # ── Django superuser ─────────────────────────────────────────────────
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        # ── Categories ───────────────────────────────────────────────────────
        from apps.courses.models import Category, Course, Section, Lesson, Enrollment
        cat_prog, _ = Category.objects.get_or_create(name="Programming",
                                                      defaults={"description": "Software development courses"})
        cat_ds, _ = Category.objects.get_or_create(name="Data Science",
                                                    defaults={"description": "Data analysis and ML courses"})

        # ── Course 1: Python Basics ──────────────────────────────────────────
        course1, _ = Course.objects.get_or_create(
            title="Python Basics",
            defaults=dict(
                description="Learn Python programming from scratch. Perfect for beginners.",
                instructor=instructor,
                category=cat_prog,
                level="beginner",
                status="published",
            )
        )

        # Sections + Lessons
        sec1, _ = Section.objects.get_or_create(course=course1, title="Introduction", defaults={"order": 1})
        l1, _ = Lesson.objects.get_or_create(section=sec1, title="What is Python?",
                                              defaults={"content_type": "text", "content": "Python is a high-level programming language.", "order": 1})
        l2, _ = Lesson.objects.get_or_create(section=sec1, title="Installing Python",
                                              defaults={"content_type": "text", "content": "Download from python.org and install.", "order": 2})

        sec2, _ = Section.objects.get_or_create(course=course1, title="Core Concepts", defaults={"order": 2})
        l3, _ = Lesson.objects.get_or_create(section=sec2, title="Variables and Types",
                                              defaults={"content_type": "text", "content": "Variables store data. Python is dynamically typed.", "order": 1})
        l4, _ = Lesson.objects.get_or_create(section=sec2, title="Control Flow",
                                              defaults={"content_type": "text", "content": "if/else, for, while loops.", "order": 2})
        l5, _ = Lesson.objects.get_or_create(section=sec2, title="Functions",
                                              defaults={"content_type": "text", "content": "def keyword defines a function.", "order": 3})

        # ── Quiz for Course 1 ────────────────────────────────────────────────
        from apps.assessments.models import Quiz, Question, Choice
        quiz1, created = Quiz.objects.get_or_create(
            course=course1, title="Python Basics Final Quiz",
            defaults=dict(
                description="Test your Python knowledge!",
                passing_grade=70,
                attempt_limit=3,
                randomize_questions=True,
                randomize_choices=False,
            )
        )
        if created:
            self._add_python_questions(quiz1)

        # ── Course 2: Data Science 101 ───────────────────────────────────────
        course2, _ = Course.objects.get_or_create(
            title="Data Science 101",
            defaults=dict(
                description="Introduction to data science with Python and pandas.",
                instructor=instructor,
                category=cat_ds,
                level="intermediate",
                status="published",
            )
        )
        sec3, _ = Section.objects.get_or_create(course=course2, title="Getting Started", defaults={"order": 1})
        Lesson.objects.get_or_create(section=sec3, title="Introduction to Data Science",
                                     defaults={"content_type": "text", "content": "Data science is an interdisciplinary field.", "order": 1})
        Lesson.objects.get_or_create(section=sec3, title="Python for Data Science",
                                     defaults={"content_type": "text", "content": "Libraries: NumPy, Pandas, Matplotlib.", "order": 2})

        quiz2, created2 = Quiz.objects.get_or_create(
            course=course2, title="Data Science Quiz",
            defaults=dict(
                description="Test your data science knowledge.",
                passing_grade=60,
                attempt_limit=2,
            )
        )
        if created2:
            self._add_ds_questions(quiz2)

        # ── Enroll students ──────────────────────────────────────────────────
        Enrollment.objects.get_or_create(student=student, course=course1,
                                         defaults={"status": "active"})
        Enrollment.objects.get_or_create(student=student, course=course2,
                                         defaults={"status": "active"})
        Enrollment.objects.get_or_create(student=student2, course=course1,
                                         defaults={"status": "active"})

        self.stdout.write(self.style.SUCCESS("✅ Demo data seeded successfully!\n"))
        self.stdout.write("Demo accounts:")
        self.stdout.write("  Admin:      admin / Admin@1234")
        self.stdout.write("  Instructor: instructor1 / Instructor@1234")
        self.stdout.write("  Student:    student1 / Student@1234")
        self.stdout.write("  Student:    student2 / Student@1234")
        self.stdout.write("Swagger: http://localhost:8000/api/v1/docs")

    def _get_or_create_user(self, username, email, password, role, first, last):
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(email=email, role=role, first_name=first, last_name=last)
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  Created user: {username}")
        return user

    def _add_python_questions(self, quiz):
        from apps.assessments.models import Question, Choice
        questions_data = [
            {
                "text": "What keyword is used to define a function in Python?",
                "explanation": "The 'def' keyword is used to define functions in Python.",
                "choices": [
                    ("function", False), ("def", True), ("fun", False), ("define", False)
                ]
            },
            {
                "text": "Which data type stores a sequence of characters?",
                "explanation": "Strings (str) store text/characters in Python.",
                "choices": [
                    ("int", False), ("float", False), ("str", True), ("list", False)
                ]
            },
            {
                "text": "What is the output of: print(type(3.14))?",
                "explanation": "3.14 is a float literal in Python.",
                "choices": [
                    ("<class 'int'>", False), ("<class 'float'>", True),
                    ("<class 'str'>", False), ("<class 'double'>", False)
                ]
            },
            {
                "text": "Which loop iterates over a sequence?",
                "explanation": "The 'for' loop is used to iterate over sequences.",
                "choices": [
                    ("while", False), ("do-while", False), ("for", True), ("loop", False)
                ]
            },
            {
                "text": "How do you start a comment in Python?",
                "explanation": "Python comments start with the # character.",
                "choices": [
                    ("//", False), ("/*", False), ("#", True), ("--", False)
                ]
            },
        ]
        for i, qd in enumerate(questions_data, 1):
            q = Question.objects.create(quiz=quiz, text=qd["text"], points=1,
                                        order=i, explanation=qd["explanation"])
            for j, (text, correct) in enumerate(qd["choices"], 1):
                Choice.objects.create(question=q, text=text, is_correct=correct, order=j)

    def _add_ds_questions(self, quiz):
        from apps.assessments.models import Question, Choice
        questions_data = [
            {
                "text": "Which Python library is commonly used for data manipulation?",
                "explanation": "Pandas is the standard library for data manipulation in Python.",
                "choices": [
                    ("NumPy", False), ("Pandas", True), ("Matplotlib", False), ("Scikit-learn", False)
                ]
            },
            {
                "text": "What does 'ML' stand for in Data Science?",
                "explanation": "ML stands for Machine Learning.",
                "choices": [
                    ("Manual Learning", False), ("Machine Logic", False),
                    ("Machine Learning", True), ("Model Learning", False)
                ]
            },
            {
                "text": "Which format is commonly used for datasets?",
                "explanation": "CSV (Comma-Separated Values) is one of the most common dataset formats.",
                "choices": [
                    ("MP3", False), ("CSV", True), ("PNG", False), ("DOC", False)
                ]
            },
        ]
        for i, qd in enumerate(questions_data, 1):
            q = Question.objects.create(quiz=quiz, text=qd["text"], points=1,
                                        order=i, explanation=qd["explanation"])
            for j, (text, correct) in enumerate(qd["choices"], 1):
                Choice.objects.create(question=q, text=text, is_correct=correct, order=j)
