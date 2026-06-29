FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app/
RUN python manage.py collectstatic --noinput || true
CMD ["gunicorn", "lms_project.wsgi:application", "--bind", "0.0.0.0:8000"]
