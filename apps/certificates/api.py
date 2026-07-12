from ninja import Router
from ninja.errors import HttpError
from typing import List
from django.conf import settings

from .models import Certificate
from .schemas import CertificateOut, CertificateVerifyOut, MessageOut
from .service import generate_certificate

router = Router()


def _cert_out(cert: Certificate, request=None) -> CertificateOut:
    pdf_url = None
    if cert.pdf_file:
        pdf_url = f"{settings.MEDIA_URL}{cert.pdf_file}"
        if request:
            pdf_url = request.build_absolute_uri(pdf_url)

    return CertificateOut(
        id=cert.id,
        course_id=cert.course_id,
        course_title=cert.course.title,
        student_name=cert.student.get_full_name() or cert.student.username,
        unique_code=cert.unique_code,
        issued_at=cert.issued_at,
        pdf_url=pdf_url,
        verification_url=cert.verification_url,
    )


@router.get("/my", response=List[CertificateOut], summary="List my certificates")
def my_certificates(request):
    certs = Certificate.objects.filter(student=request.auth).select_related("course", "student")
    return [_cert_out(c, request) for c in certs]


@router.get("/verify/{unique_code}", response=CertificateVerifyOut, auth=None,
            summary="[Public] Verify a certificate by unique code")
def verify_certificate(request, unique_code: str):
    try:
        from uuid import UUID
        cert = Certificate.objects.select_related("student", "course", "course__instructor").get(
            unique_code=UUID(unique_code)
        )
        return CertificateVerifyOut(
            valid=True,
            course_title=cert.course.title,
            student_name=cert.student.get_full_name() or cert.student.username,
            instructor_name=cert.course.instructor.get_full_name() or cert.course.instructor.username,
            issued_at=cert.issued_at,
            message="Certificate is valid.",
        )
    except Exception:
        return CertificateVerifyOut(valid=False, message="Certificate not found or invalid code.")


@router.post("/generate/{course_id}", response=CertificateOut,
             summary="Manually request certificate generation (if eligible)")
def request_certificate(request, course_id: int):
    user = request.auth
    from apps.courses.models import Course, Enrollment

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")

    enrollment = Enrollment.objects.filter(
        student=user, course=course, status="completed"
    ).first()
    if not enrollment:
        raise HttpError(400, "You have not completed this course yet")

    cert = generate_certificate(user, course)
    return _cert_out(cert, request)


@router.get("/admin/all", response=List[CertificateOut],
            summary="[Admin] List all certificates")
def all_certificates(request):
    if not request.auth.is_admin():
        raise HttpError(403, "Admin only")
    certs = Certificate.objects.all().select_related("course", "student")
    return [_cert_out(c, request) for c in certs]
