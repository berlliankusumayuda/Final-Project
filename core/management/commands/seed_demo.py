# Seed data management command
from django.core.management.base import BaseCommand
from users.models import User
from courses.models import Category, Course, Lesson
from enrollments.models import Enrollment
from progress.models import Progress

class Command(BaseCommand):
    help = 'Create demo data'
    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin','admin@example.com','adminpass', role='admin')
        if not User.objects.filter(username='instructor').exists():
            User.objects.create_user('instructor','instr@example.com','instrpass', role='instructor')
        if not User.objects.filter(username='student').exists():
            User.objects.create_user('student','stud@example.com','studpass', role='student')
        cat, _ = Category.objects.get_or_create(name='Programming')
        instr = User.objects.get(username='instructor')
        c, _ = Course.objects.get_or_create(title='Intro Python', description='Learn Python', instructor=instr, category=cat)
        Lesson.objects.get_or_create(course=c, title='Lesson 1', content='Basics', order=1)
        self.stdout.write('Seeded demo data')
