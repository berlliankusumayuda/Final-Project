from ninja import Schema
from typing import Optional
from datetime import datetime
import uuid


class CertificateOut(Schema):
    id: int
    course_id: int
    course_title: str
    student_name: str
    unique_code: uuid.UUID
    issued_at: datetime
    pdf_url: Optional[str] = None
    verification_url: str


class CertificateVerifyOut(Schema):
    valid: bool
    course_title: Optional[str] = None
    student_name: Optional[str] = None
    instructor_name: Optional[str] = None
    issued_at: Optional[datetime] = None
    message: str


class MessageOut(Schema):
    message: str
