"""
Tests for Simple LMS – Foundation + Assessment & Certificate (Paket 3)
Run: python manage.py test tests
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.courses.models import Category, Course, Section, Lesson, Enrollment, Progress
from apps.assessments.models import Quiz, Question, Choice, QuizAttempt
from apps.certificates.models import Certificate

User = get_user_model()
client = Client()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_user(username, role="student", password="Test@1234"):
    user = User.objects.create_user(username=username, email=f"{username}@test.com",
                                     password=password, role=role)
    return user


def get_token(username, password="Test@1234"):
    resp = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp.json()["access"]


def auth_headers(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class AuthTests(TestCase):
    def test_register_student(self):
        resp = client.post(
            "/api/v1/auth/register",
            data=json.dumps({"username": "newstudent", "email": "ns@test.com",
                              "password": "Test@1234", "role": "student"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["role"], "student")

    def test_login_success(self):
        create_user("logintest")
        resp = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "logintest", "password": "Test@1234"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_login_invalid(self):
        resp = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"username": "nobody", "password": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_me_requires_auth(self):
        resp = client.get("/api/v1/auth/me")
        self.assertEqual(resp.status_code, 401)

    def test_me_returns_profile(self):
        create_user("metest", role="instructor")
        token = get_token("metest")
        resp = client.get("/api/v1/auth/me", **auth_headers(token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["role"], "instructor")

    def test_register_duplicate_username(self):
        create_user("dupuser")
        resp = client.post(
            "/api/v1/auth/register",
            data=json.dumps({"username": "dupuser", "email": "d@test.com", "password": "Test@1234"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


# ─── RBAC Tests ───────────────────────────────────────────────────────────────

class RBACTests(TestCase):
    def setUp(self):
        self.admin = create_user("admin_rbac", role="admin")
        self.instructor = create_user("instr_rbac", role="instructor")
        self.student = create_user("stud_rbac", role="student")
        self.admin_token = get_token("admin_rbac")
        self.instr_token = get_token("instr_rbac")
        self.stud_token = get_token("stud_rbac")

    def test_student_cannot_create_course(self):
        resp = client.post(
            "/api/v1/courses",
            data=json.dumps({"title": "Hack Course"}),
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 403)

    def test_instructor_can_create_course(self):
        resp = client.post(
            "/api/v1/courses",
            data=json.dumps({"title": "Instructor Course", "level": "beginner"}),
            content_type="application/json",
            **auth_headers(self.instr_token),
        )
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_list_all_users(self):
        resp = client.get("/api/v1/auth/users", **auth_headers(self.stud_token))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_list_all_users(self):
        resp = client.get("/api/v1/auth/users", **auth_headers(self.admin_token))
        self.assertEqual(resp.status_code, 200)


# ─── Course Tests ─────────────────────────────────────────────────────────────

class CourseTests(TestCase):
    def setUp(self):
        self.instructor = create_user("instr_course", role="instructor")
        self.student = create_user("stud_course", role="student")
        self.instr_token = get_token("instr_course")
        self.stud_token = get_token("stud_course")
        cat = Category.objects.create(name="Test Cat")
        self.course = Course.objects.create(
            title="Test Course", instructor=self.instructor, category=cat,
            level="beginner", status="published",
        )

    def test_list_courses_public(self):
        resp = client.get("/api/v1/courses")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) >= 1)

    def test_get_course_detail(self):
        resp = client.get(f"/api/v1/courses/{self.course.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["title"], "Test Course")

    def test_enroll_student(self):
        resp = client.post(
            f"/api/v1/courses/{self.course.id}/enroll",
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "active")

    def test_enroll_only_for_students(self):
        resp = client.post(
            f"/api/v1/courses/{self.course.id}/enroll",
            content_type="application/json",
            **auth_headers(self.instr_token),
        )
        self.assertEqual(resp.status_code, 403)


# ─── Quiz Tests ───────────────────────────────────────────────────────────────

class QuizTests(TestCase):
    def setUp(self):
        self.instructor = create_user("instr_quiz", role="instructor")
        self.student = create_user("stud_quiz", role="student")
        self.instr_token = get_token("instr_quiz")
        self.stud_token = get_token("stud_quiz")

        self.course = Course.objects.create(
            title="Quiz Course", instructor=self.instructor, level="beginner", status="published"
        )
        Enrollment.objects.create(student=self.student, course=self.course, status="active")

        self.quiz = Quiz.objects.create(
            course=self.course, title="Test Quiz", passing_grade=60, attempt_limit=3
        )
        self.q1 = Question.objects.create(quiz=self.quiz, text="What is 2+2?", points=1, order=1,
                                           explanation="2+2=4")
        self.c_correct = Choice.objects.create(question=self.q1, text="4", is_correct=True, order=1)
        self.c_wrong = Choice.objects.create(question=self.q1, text="5", is_correct=False, order=2)

        self.q2 = Question.objects.create(quiz=self.quiz, text="Capital of Indonesia?", points=2, order=2,
                                           explanation="Jakarta is the capital")
        self.c2_correct = Choice.objects.create(question=self.q2, text="Jakarta", is_correct=True, order=1)
        self.c2_wrong = Choice.objects.create(question=self.q2, text="Bali", is_correct=False, order=2)

    def test_list_quizzes_enrolled_student(self):
        resp = client.get(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_list_quizzes_unenrolled_student(self):
        other = create_user("other_stud", role="student")
        tok = get_token("other_stud")
        resp = client.get(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes",
            **auth_headers(tok),
        )
        self.assertEqual(resp.status_code, 403)

    def test_get_quiz_hides_answers(self):
        resp = client.get(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Choices should not expose is_correct
        for q in data["questions"]:
            for c in q["choices"]:
                self.assertNotIn("is_correct", c)

    def test_submit_quiz_all_correct(self):
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/submit",
            data=json.dumps({"answers": [
                {"question_id": self.q1.id, "choice_id": self.c_correct.id},
                {"question_id": self.q2.id, "choice_id": self.c2_correct.id},
            ]}),
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["score"], 100.0)
        self.assertTrue(data["passed"])

    def test_submit_quiz_all_wrong(self):
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/submit",
            data=json.dumps({"answers": [
                {"question_id": self.q1.id, "choice_id": self.c_wrong.id},
                {"question_id": self.q2.id, "choice_id": self.c2_wrong.id},
            ]}),
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["score"], 0.0)
        self.assertFalse(data["passed"])

    def test_attempt_limit_enforced(self):
        # Quiz has limit 3, pass=60%. Submit wrong answers 3 times
        for _ in range(3):
            QuizAttempt.objects.create(
                student=self.student, quiz=self.quiz, status="graded",
                score=0, earned_points=0, total_points=3, passed=False,
                submitted_at=timezone.now()
            )
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/submit",
            data=json.dumps({"answers": []}),
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Attempt limit", resp.json()["detail"])

    def test_attempt_status(self):
        resp = client.get(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/status",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("can_attempt", data)
        self.assertIn("attempts_used", data)

    def test_attempt_history(self):
        # First submit
        client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/submit",
            data=json.dumps({"answers": []}),
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        resp = client.get(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/attempts",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_instructor_can_create_question(self):
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/questions",
            data=json.dumps({
                "text": "New question?",
                "points": 1,
                "order": 10,
                "explanation": "Because",
                "choices": [
                    {"text": "Right", "is_correct": True, "order": 1},
                    {"text": "Wrong", "is_correct": False, "order": 2},
                ]
            }),
            content_type="application/json",
            **auth_headers(self.instr_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("is_correct", resp.json()["choices"][0])

    def test_question_requires_correct_choice(self):
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{self.quiz.id}/questions",
            data=json.dumps({
                "text": "Bad question?",
                "points": 1,
                "order": 11,
                "explanation": "",
                "choices": [
                    {"text": "A", "is_correct": False, "order": 1},
                    {"text": "B", "is_correct": False, "order": 2},
                ]
            }),
            content_type="application/json",
            **auth_headers(self.instr_token),
        )
        self.assertEqual(resp.status_code, 400)


# ─── Certificate Tests ────────────────────────────────────────────────────────

class CertificateTests(TestCase):
    def setUp(self):
        self.instructor = create_user("instr_cert", role="instructor")
        self.student = create_user("stud_cert", role="student")
        self.stud_token = get_token("stud_cert")

        self.course = Course.objects.create(
            title="Cert Course", instructor=self.instructor, level="beginner", status="published"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, course=self.course, status="completed"
        )

    def test_request_certificate_completed_course(self):
        resp = client.post(
            f"/api/v1/certificates/generate/{self.course.id}",
            content_type="application/json",
            **auth_headers(self.stud_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("unique_code", data)
        self.assertIn("verification_url", data)

    def test_cannot_get_cert_for_incomplete_course(self):
        other = create_user("stud_nocert", role="student")
        tok = get_token("stud_nocert")
        Enrollment.objects.create(student=other, course=self.course, status="active")
        resp = client.post(
            f"/api/v1/certificates/generate/{self.course.id}",
            content_type="application/json",
            **auth_headers(tok),
        )
        self.assertEqual(resp.status_code, 400)

    def test_verify_certificate_valid(self):
        cert = Certificate.objects.create(student=self.student, course=self.course)
        resp = client.get(f"/api/v1/certificates/verify/{cert.unique_code}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["course_title"], "Cert Course")

    def test_verify_certificate_invalid(self):
        resp = client.get("/api/v1/certificates/verify/00000000-0000-0000-0000-000000000000")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["valid"])

    def test_my_certificates(self):
        Certificate.objects.create(student=self.student, course=self.course)
        resp = client.get("/api/v1/certificates/my", **auth_headers(self.stud_token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_certificate_auto_generated_on_quiz_pass(self):
        """When student passes quiz AND course is completed, cert is generated."""
        quiz = Quiz.objects.create(
            course=self.course, title="Auto Cert Quiz", passing_grade=50, attempt_limit=0
        )
        q = Question.objects.create(quiz=quiz, text="Easy?", points=1, order=1)
        c_right = Choice.objects.create(question=q, text="Yes", is_correct=True, order=1)
        Choice.objects.create(question=q, text="No", is_correct=False, order=2)

        tok = self.stud_token
        resp = client.post(
            f"/api/v1/assessments/courses/{self.course.id}/quizzes/{quiz.id}/submit",
            data=json.dumps({"answers": [{"question_id": q.id, "choice_id": c_right.id}]}),
            content_type="application/json",
            **auth_headers(tok),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["passed"])
        # Certificate must exist now
        self.assertTrue(Certificate.objects.filter(student=self.student, course=self.course).exists())
