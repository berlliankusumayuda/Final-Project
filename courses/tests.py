from django.test import TestCase
from django.urls import reverse
from users.models import User
from courses.models import Course, Category

class SmokeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin','a@a.com','adminpass', role='admin')
        self.instructor = User.objects.create_user('instr','i@i.com','instrpass', role='instructor')
        cat = Category.objects.create(name='Cat')
        Course.objects.create(title='C1', description='d', instructor=self.instructor, category=cat)

    def test_course_list(self):
        resp = self.client.get('/courses/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
