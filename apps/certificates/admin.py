from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "unique_code", "issued_at")
    readonly_fields = ("unique_code", "issued_at")
