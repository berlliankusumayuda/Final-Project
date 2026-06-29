from ninja import Router
from users.deps import TokenAuth
from progress.models import Progress
from courses.models import Lesson
from core.response import success_response, error_response

api = Router()

@api.post('complete', auth=TokenAuth())
def complete_lesson(request, payload: dict):
    user = request.auth
    try:
        lesson_id = int(request.data.get('lesson_id'))
    except Exception:
        return error_response('invalid_input','lesson_id required')
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return error_response('not_found','Lesson not found')
    obj, created = Progress.objects.update_or_create(user=user, lesson=lesson, defaults={'completed': True})
    return success_response({'lesson_id': lesson.id, 'completed': True})
