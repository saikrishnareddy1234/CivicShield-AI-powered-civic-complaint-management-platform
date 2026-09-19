from django.db import models
import uuid

class CivicIncident(models.Model):

    incident_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    title = models.CharField(
        max_length=200
    )

    category = models.CharField(
        max_length=50
    )

    department = models.CharField(
        max_length=150
    )

    priority = models.CharField(
        max_length=20,
        default="medium"
    )

    status = models.CharField(
        max_length=30,
        default="pending"
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title
class Complaint(models.Model):

    CATEGORY_CHOICES = [
        ("garbage", "Garbage"),
        ("road", "Road Damage"),
        ("streetlight", "Street Light"),
        ("water", "Water Leakage"),
        ("drainage", "Drainage"),
        ("traffic", "Traffic Signal"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ]

    complaint_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    name = models.CharField(max_length=100)

    email = models.EmailField()

    phone = models.CharField(max_length=15)

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to="complaints/",
        blank=True,
        null=True
    )

    location = models.CharField(max_length=255)

    latitude = models.FloatField(
        blank=True,
        null=True
    )

    longitude = models.FloatField(
        blank=True,
        null=True
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium"
    )
    severity_score = models.IntegerField(
    default=0
)

    severity_reason = models.TextField(
    blank=True
)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    department = models.CharField(
        max_length=100,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_duplicate = models.BooleanField(
        default=False
    )

    duplicate_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="duplicate_complaints"
    )

    duplicate_score = models.FloatField(
        default=0
)
    incident = models.ForeignKey(
    "CivicIncident",
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="complaints"
)
    def __str__(self):
        return f"{self.category} - {self.complaint_id}"