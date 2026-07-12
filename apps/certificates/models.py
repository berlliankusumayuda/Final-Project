import uuid
from django.db import models
from django.conf import settings
from apps.courses.models import Course


class Certificate(models.Model):
    """Certificate issued when a student completes a course."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates")
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pdf_file = models.FileField(upload_to="certificates/", null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Certificate – {self.student.username} – {self.course.title}"

    @property
    def verification_url(self):
        return f"/api/v1/certificates/verify/{self.unique_code}"
