from ninja import Router
from ninja.errors import HttpError
from django.utils import timezone
from typing import List, Optional
from .models import Category, Course, Section, Lesson, Enrollment, Progress
from .schemas import (
    CategoryIn, CategoryOut, CourseIn, CourseOut,
    SectionIn, SectionOut, LessonIn, LessonOut,
    EnrollmentOut, ProgressIn, ProgressOut, MessageOut,
)

router = Router()


# ── Categories ──────────────────────────────────────────────────────────────

@router.get("/categories", response=List[CategoryOut], auth=None, summary="List all categories")
def list_categories(request):
    return list(Category.objects.all().values("id", "name", "description"))


@router.post("/categories", response=CategoryOut, summary="[Admin] Create category")
def create_category(request, payload: CategoryIn):
    if not request.auth.is_admin():
        raise HttpError(403, "Admin only")
    cat = Category.objects.create(**payload.dict())
    return CategoryOut(id=cat.id, name=cat.name, description=cat.description)


# ── Courses ──────────────────────────────────────────────────────────────────

def _course_out(c: Course) -> CourseOut:
    return CourseOut(
        id=c.id, title=c.title, description=c.description,
        level=c.level, status=c.status,
        instructor_name=c.instructor.get_full_name() or c.instructor.username,
        category_name=c.category.name if c.category else None,
        created_at=c.created_at,
    )


@router.get("", response=List[CourseOut], auth=None, summary="List published courses")
def list_courses(request, search: Optional[str] = None, category_id: Optional[int] = None,
                 level: Optional[str] = None):
    qs = Course.objects.filter(status="published").select_related("instructor", "category")
    if search:
        qs = qs.filter(title__icontains=search)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if level:
        qs = qs.filter(level=level)
    return [_course_out(c) for c in qs]


@router.get("/{course_id}", response=CourseOut, auth=None, summary="Get course detail")
def get_course(request, course_id: int):
    try:
        c = Course.objects.select_related("instructor", "category").get(id=course_id, status="published")
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    return _course_out(c)


@router.post("", response=CourseOut, summary="[Instructor/Admin] Create course")
def create_course(request, payload: CourseIn):
    user = request.auth
    if not (user.is_instructor() or user.is_admin()):
        raise HttpError(403, "Instructor or Admin only")
    c = Course.objects.create(instructor=user, **payload.dict())
    return _course_out(c)


@router.put("/{course_id}", response=CourseOut, summary="[Instructor/Admin] Update course")
def update_course(request, course_id: int, payload: CourseIn):
    user = request.auth
    try:
        c = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    if not (user.is_admin() or c.instructor == user):
        raise HttpError(403, "Not authorized")
    for k, v in payload.dict().items():
        setattr(c, k, v)
    c.save()
    return _course_out(c)


@router.post("/{course_id}/publish", response=MessageOut, summary="[Instructor/Admin] Publish course")
def publish_course(request, course_id: int):
    user = request.auth
    try:
        c = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    if not (user.is_admin() or c.instructor == user):
        raise HttpError(403, "Not authorized")
    c.status = "published"
    c.save()
    return MessageOut(message="Course published")


@router.delete("/{course_id}", response=MessageOut, summary="[Admin] Delete course")
def delete_course(request, course_id: int):
    if not request.auth.is_admin():
        raise HttpError(403, "Admin only")
    Course.objects.filter(id=course_id).delete()
    return MessageOut(message="Course deleted")


# ── Sections ─────────────────────────────────────────────────────────────────

@router.get("/{course_id}/sections", response=List[SectionOut], auth=None, summary="List sections")
def list_sections(request, course_id: int):
    return list(Section.objects.filter(course_id=course_id).values("id", "title", "order"))


@router.post("/{course_id}/sections", response=SectionOut, summary="[Instructor/Admin] Add section")
def add_section(request, course_id: int, payload: SectionIn):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    if not (user.is_admin() or course.instructor == user):
        raise HttpError(403, "Not authorized")
    s = Section.objects.create(course=course, **payload.dict())
    return SectionOut(id=s.id, title=s.title, order=s.order)


# ── Lessons ──────────────────────────────────────────────────────────────────

@router.get("/{course_id}/sections/{section_id}/lessons", response=List[LessonOut], auth=None)
def list_lessons(request, course_id: int, section_id: int):
    return [LessonOut(id=l.id, title=l.title, content_type=l.content_type,
                      content=l.content, order=l.order, duration_minutes=l.duration_minutes)
            for l in Lesson.objects.filter(section_id=section_id, section__course_id=course_id)]


@router.post("/{course_id}/sections/{section_id}/lessons", response=LessonOut)
def add_lesson(request, course_id: int, section_id: int, payload: LessonIn):
    user = request.auth
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    if not (user.is_admin() or course.instructor == user):
        raise HttpError(403, "Not authorized")
    section = Section.objects.get(id=section_id, course=course)
    l = Lesson.objects.create(section=section, **payload.dict())
    return LessonOut(id=l.id, title=l.title, content_type=l.content_type,
                     content=l.content, order=l.order, duration_minutes=l.duration_minutes)


# ── Enrollment ────────────────────────────────────────────────────────────────

def _calc_progress(enrollment: Enrollment) -> float:
    total = Lesson.objects.filter(section__course=enrollment.course).count()
    if total == 0:
        return 0.0
    done = Progress.objects.filter(enrollment=enrollment, completed=True).count()
    return round(done / total * 100, 1)


@router.post("/{course_id}/enroll", response=EnrollmentOut, summary="Enroll in a course")
def enroll(request, course_id: int):
    user = request.auth
    if not user.is_student():
        raise HttpError(403, "Students only")
    try:
        course = Course.objects.get(id=course_id, status="published")
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found or not published")
    enrollment, created = Enrollment.objects.get_or_create(student=user, course=course)
    return EnrollmentOut(
        id=enrollment.id, course_id=course.id, course_title=course.title,
        status=enrollment.status, enrolled_at=enrollment.enrolled_at,
        progress_percent=_calc_progress(enrollment),
    )


@router.get("/enrollments/my", response=List[EnrollmentOut], summary="My enrollments")
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(student=request.auth).select_related("course")
    return [
        EnrollmentOut(
            id=e.id, course_id=e.course.id, course_title=e.course.title,
            status=e.status, enrolled_at=e.enrolled_at, progress_percent=_calc_progress(e),
        ) for e in enrollments
    ]


@router.post("/{course_id}/progress", response=MessageOut, summary="Mark lesson progress")
def mark_progress(request, course_id: int, payload: ProgressIn):
    user = request.auth
    try:
        enrollment = Enrollment.objects.get(student=user, course_id=course_id)
        lesson = Lesson.objects.get(id=payload.lesson_id, section__course_id=course_id)
    except (Enrollment.DoesNotExist, Lesson.DoesNotExist):
        raise HttpError(404, "Enrollment or lesson not found")
    prog, _ = Progress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    prog.completed = payload.completed
    prog.completed_at = timezone.now() if payload.completed else None
    prog.save()

    # Auto-complete enrollment if all lessons done
    total = Lesson.objects.filter(section__course_id=course_id).count()
    done = Progress.objects.filter(enrollment=enrollment, completed=True).count()
    if total > 0 and done >= total:
        enrollment.status = "completed"
        enrollment.completed_at = timezone.now()
        enrollment.save()

    return MessageOut(message="Progress updated")


@router.get("/{course_id}/progress", response=List[ProgressOut], summary="Get my progress")
def get_progress(request, course_id: int):
    try:
        enrollment = Enrollment.objects.get(student=request.auth, course_id=course_id)
    except Enrollment.DoesNotExist:
        raise HttpError(404, "Not enrolled")
    records = Progress.objects.filter(enrollment=enrollment).select_related("lesson")
    return [ProgressOut(id=p.id, lesson_id=p.lesson.id, lesson_title=p.lesson.title,
                        completed=p.completed) for p in records]
