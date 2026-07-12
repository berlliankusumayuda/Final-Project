"""
Certificate generation service.
Generates a PDF certificate using WeasyPrint (if available) or falls back to a plain HTML file.
"""
from __future__ import annotations
import os
import io
from datetime import datetime
from django.conf import settings
from django.utils import timezone


CERT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<style>
  @page {{ size: A4 landscape; margin: 0; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    background: #fff8ee;
    width: 297mm;
    height: 210mm;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .cert {{
    border: 12px solid #b8860b;
    outline: 4px solid #daa520;
    outline-offset: -20px;
    width: 270mm;
    height: 190mm;
    padding: 30px 50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    text-align: center;
    background: #fffdf7;
  }}
  .header {{ color: #8b6914; font-size: 14px; letter-spacing: 4px; text-transform: uppercase; }}
  .title {{ font-size: 42px; color: #b8860b; font-weight: bold; margin-top: 8px; }}
  .subtitle {{ font-size: 13px; color: #666; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px; }}
  .body {{ margin: 20px 0 10px; }}
  .body p {{ font-size: 16px; color: #444; margin-bottom: 6px; }}
  .student-name {{ font-size: 32px; color: #2c2c2c; font-style: italic; border-bottom: 2px solid #b8860b; padding-bottom: 4px; margin: 10px auto; display: inline-block; }}
  .course-name {{ font-size: 20px; color: #b8860b; font-weight: bold; margin-top: 8px; }}
  .details {{ font-size: 13px; color: #666; margin-top: 4px; }}
  .footer {{ width: 100%; display: flex; justify-content: space-between; align-items: flex-end; padding-top: 16px; }}
  .sig-block {{ text-align: center; min-width: 160px; }}
  .sig-line {{ border-top: 1px solid #444; margin-top: 40px; padding-top: 6px; font-size: 12px; color: #444; }}
  .code-block {{ text-align: center; }}
  .code-block .label {{ font-size: 10px; color: #888; letter-spacing: 1px; text-transform: uppercase; }}
  .code-block .code {{ font-family: monospace; font-size: 11px; color: #555; margin-top: 4px; }}
  .seal {{ font-size: 48px; }}
</style>
</head>
<body>
<div class="cert">
  <div>
    <div class="header">Simple LMS · Universitas Dian Nuswantoro</div>
    <div class="title">Certificate of Completion</div>
    <div class="subtitle">This is to certify that</div>
  </div>
  <div class="body">
    <div class="student-name">{student_name}</div>
    <p style="margin-top:12px;">has successfully completed the course</p>
    <div class="course-name">{course_title}</div>
    <div class="details">Instructed by {instructor_name} · {level} Level</div>
    <div class="details" style="margin-top:4px;">Issued on {issued_date}</div>
  </div>
  <div class="footer">
    <div class="sig-block">
      <div class="sig-line">{instructor_name}<br/><small>Course Instructor</small></div>
    </div>
    <div class="code-block">
      <div class="seal">🎓</div>
      <div class="label">Certificate ID</div>
      <div class="code">{unique_code}</div>
    </div>
    <div class="sig-block">
      <div class="sig-line">Simple LMS Admin<br/><small>Program Director</small></div>
    </div>
  </div>
</div>
</body>
</html>
"""


def generate_certificate(user, course):
    """Generate and save a certificate PDF (or HTML fallback) for user+course."""
    from .models import Certificate

    cert, created = Certificate.objects.get_or_create(student=user, course=course)
    if not created and cert.pdf_file:
        return cert  # already generated

    student_name = user.get_full_name() or user.username
    instructor_name = course.instructor.get_full_name() or course.instructor.username
    issued_date = timezone.now().strftime("%B %d, %Y")
    unique_code = str(cert.unique_code)

    html_content = CERT_TEMPLATE.format(
        student_name=student_name,
        course_title=course.title,
        instructor_name=instructor_name,
        level=course.get_level_display(),
        issued_date=issued_date,
        unique_code=unique_code,
    )

    # Ensure media/certificates dir exists
    cert_dir = os.path.join(settings.MEDIA_ROOT, "certificates")
    os.makedirs(cert_dir, exist_ok=True)

    filename = f"certificate_{unique_code}.pdf"
    filepath = os.path.join(cert_dir, filename)

    try:
        from weasyprint import HTML as WeasyHTML
        WeasyHTML(string=html_content).write_pdf(filepath)
    except Exception:
        # Fallback: save HTML file instead
        filename = f"certificate_{unique_code}.html"
        filepath = os.path.join(cert_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

    cert.pdf_file.name = f"certificates/{filename}"
    cert.save()
    return cert
