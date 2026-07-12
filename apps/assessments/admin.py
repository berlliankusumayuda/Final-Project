from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, AttemptAnswer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "passing_grade", "attempt_limit", "is_active")
    list_filter = ("is_active",)
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "points", "order")
    inlines = [ChoiceInline]

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "passed", "started_at")
    list_filter = ("passed", "status")

admin.site.register(Choice)
admin.site.register(AttemptAnswer)
