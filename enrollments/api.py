from ninja import Router
from ninja.security import django_auth
from users.deps import TokenAuth, require_role
from enrollments.models import Enrollment
from courses.models import Course
from core.response import success_response, error_response
from users.auth import get_user_from_token

api = Router()

@api.post('', auth=TokenAuth())
def enroll_course(request, payload: dict):
    user = request.auth
    try:
        course_id = int(request.data.get('course_id'))
    except Exception:
        return error_response('invalid_input','course_id required')
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return error_response('not_found','Course not found')
    if Enrollment.objects.filter(user=user, course=course).exists():
        return error_response('exists','Already enrolled')
    Enrollment.objects.create(user=user, course=course)
    # invalidate any related caches
    from core import cache_utils
    cache_utils.delete_pattern('courses:list:*')
    cache_utils.delete_key(f'courses:detail:{course.id}')
    return success_response({'message':'enrolled'})
