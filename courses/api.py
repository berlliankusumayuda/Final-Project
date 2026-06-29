from ninja import Router, Schema, Query
from courses.models import Course, Lesson
from users.auth import get_user_from_token
from django.core.cache import cache
from typing import List, Optional
from django.forms.models import model_to_dict
from django.db.models import Prefetch

api = Router()

class CourseOut(Schema):
    id: int
    title: str
    description: Optional[str]
    instructor_id: int

class CourseListOut(Schema):
    success: bool
    data: List[CourseOut]

@api.get('', response=CourseListOut)
def list_courses(request, q: Optional[str] = Query(None), limit: int = 10, offset: int = 0):
    # Cache key includes query params
    key = f"courses:list:{q}:{limit}:{offset}"
    cached = cache.get(key)
    if cached is not None:
        return {'success': True, 'data': cached}
    qs = Course.objects.select_related('instructor').all()
    if q:
        qs = qs.filter(title__icontains=q)
    qs = qs[offset:offset+limit]
    data = [ {'id': c.id, 'title': c.title, 'description': c.description, 'instructor_id': c.instructor_id} for c in qs]
    cache.set(key, data, timeout=60)
    return {'success': True, 'data': data}

@api.get('{course_id}', response={200: CourseOut})
def course_detail(request, course_id: int):
    key = f"courses:detail:{course_id}"
    cached = cache.get(key)
    if cached:
        return cached
    c = Course.objects.select_related('instructor').get(id=course_id)
    out = {'id': c.id, 'title': c.title, 'description': c.description, 'instructor_id': c.instructor_id}
    cache.set(key, out, timeout=120)
    return out
