from django.test import TestCase
from users.models import User
from courses.models import Course, Category
from enrollments.models import Enrollment

class EnrollmentTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user('instr','i@i.com','instrpass', role='instructor')
        self.student = User.objects.create_user('student','s@a.com','studpass', role='student')
        cat = Category.objects.create(name='Cat')
        self.course = Course.objects.create(title='EnrollmentCourse', description='d', instructor=self.instructor, category=cat)

    def test_enroll_requires_auth(self):
        resp = self.client.post('/enrollments/', data={'course_id': self.course.id})
        self.assertEqual(resp.status_code, 401)

    def test_enroll_success(self):
        # login via seed users is not available here; use force_login
        self.client.force_login(self.student)
        resp = self.client.post('/enrollments/', data={'course_id': self.course.id})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Enrollment.objects.filter(user=self.student, course=self.course).exists())
