from django.db import models
from users.models import User
from courses.models import Course, Lesson

class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses')
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('user','lesson')
