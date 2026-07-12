from ninja import Schema
from typing import Optional, List
from datetime import datetime


class CategoryOut(Schema):
    id: int
    name: str
    description: str


class CategoryIn(Schema):
    name: str
    description: str = ""


class CourseIn(Schema):
    title: str
    description: str = ""
    category_id: Optional[int] = None
    level: str = "beginner"


class CourseOut(Schema):
    id: int
    title: str
    description: str
    level: str
    status: str
    instructor_name: str
    category_name: Optional[str] = None
    created_at: datetime


class SectionIn(Schema):
    title: str
    order: int = 0


class SectionOut(Schema):
    id: int
    title: str
    order: int


class LessonIn(Schema):
    title: str
    content_type: str = "text"
    content: str = ""
    order: int = 0
    duration_minutes: int = 0


class LessonOut(Schema):
    id: int
    title: str
    content_type: str
    content: str
    order: int
    duration_minutes: int


class EnrollmentOut(Schema):
    id: int
    course_id: int
    course_title: str
    status: str
    enrolled_at: datetime
    progress_percent: float = 0.0


class ProgressIn(Schema):
    lesson_id: int
    completed: bool = True


class ProgressOut(Schema):
    id: int
    lesson_id: int
    lesson_title: str
    completed: bool


class MessageOut(Schema):
    message: str
