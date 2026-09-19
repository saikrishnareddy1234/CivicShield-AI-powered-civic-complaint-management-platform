from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):

    list_display = (
        "complaint_id",
        "category",
        "priority",
        "status",
        "department",
        "created_at",
    )

    list_filter = (
        "category",
        "priority",
        "status",
        "department",
    )

    search_fields = (
        "complaint_id",
        "name",
        "email",
        "location",
        "description",
    )

    readonly_fields = (
        "complaint_id",
        "created_at",
        "updated_at",
    )