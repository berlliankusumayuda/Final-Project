from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Course, Lesson
from django.core.cache import cache

@receiver([post_save, post_delete], sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    cache.delete(f"courses:detail:{instance.id}")
    # naive: delete all list keys
    # for simplicity, clear list cache prefix
    # In production, track keys or use tags
    # Here we flush entire default cache (acceptable for demo)
    cache.clear()

@receiver([post_save, post_delete], sender=Lesson)
def invalidate_lesson_related(sender, instance, **kwargs):
    cache.clear()
