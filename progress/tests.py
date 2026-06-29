from django.test import TestCase
from users.models import User
from courses.models import Course, Category, Lesson
from progress.models import Progress

class ProgressTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user('instr','i@i.com','instrpass', role='instructor')
        self.student = User.objects.create_user('student','s@a.com','studpass', role='student')
        cat = Category.objects.create(name='Cat')
        self.course = Course.objects.create(title='PCourse', description='d', instructor=self.instructor, category=cat)
        self.lesson = Lesson.objects.create(course=self.course, title='L1', content='x', order=1)

    def test_complete_requires_auth(self):
        resp = self.client.post('/progress/complete', data={'lesson_id': self.lesson.id})
        self.assertEqual(resp.status_code, 401)

    def test_complete_success(self):
        self.client.force_login(self.student)
        resp = self.client.post('/progress/complete', data={'lesson_id': self.lesson.id})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Progress.objects.filter(user=self.student, lesson=self.lesson, completed=True).exists())
