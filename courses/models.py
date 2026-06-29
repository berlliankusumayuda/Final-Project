from django.db import models
from users.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.course.title} - {self.title}"
