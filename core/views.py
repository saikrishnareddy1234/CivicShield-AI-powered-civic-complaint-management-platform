from django.http import JsonResponse

from .forms import ComplaintForm
from .models import Complaint, CivicIncident

from .ai_engine import (
    classify_complaint,
    analyze_complaint_image,
    calculate_severity,
    route_department,
    detect_duplicate_complaint,
    get_or_create_incident,
)

from django.db.models import Count

from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


def home(request):
    return render(request, "index.html")


def report_complaint(request):

    if request.method == "POST":

        form = ComplaintForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            complaint = form.save()

            ai_reason = ""
            visual_evidence = ""
            ai_confidence = None

            try:

                # =========================================
                # IMAGE + TEXT AI ANALYSIS
                # =========================================

                if complaint.image:

                    image_path = complaint.image.path

                    ai_result = analyze_complaint_image(
                        image_path,
                        complaint.description
                    )

                else:

                    # =====================================
                    # TEXT FALLBACK
                    # =====================================

                    ai_result = classify_complaint(
                        complaint.description
                    )

                # =========================================
                # SAVE AI RESULTS
                # =========================================

                complaint.category = ai_result["category"]
                complaint.priority = ai_result["priority"]
                complaint.department = ai_result["department"]

                # =========================================
                # CIVICSHIELD SEVERITY
                # =========================================

                severity = calculate_severity(
                    ai_result,
                    complaint.description
                )

                complaint.severity_score = severity["score"]

                complaint.priority = severity["priority"]

                # CivicShield controls the final department.
                # AI identifies the category.

                complaint.department = route_department(
                    ai_result["category"]
                )

                complaint.severity_reason = (
                    f"AI classified the issue as "
                    f"{severity['priority']} priority with "
                    f"a severity score of "
                    f"{severity['score']}/100."
                )

                complaint.save()

                # =========================================
                # DUPLICATE COMPLAINT DETECTION
                # =========================================

                existing_complaints = (
                    Complaint.objects
                    .exclude(pk=complaint.pk)
                )

                duplicate_result = detect_duplicate_complaint(
                    complaint,
                    existing_complaints
                )

                if duplicate_result["is_duplicate"]:

                    complaint.is_duplicate = True

                    complaint.duplicate_score = (
                        duplicate_result["score"]
                    )

                    complaint.duplicate_of = (
                        duplicate_result["matched_complaint"]
                    )

                else:

                    complaint.is_duplicate = False

                    complaint.duplicate_score = (
                        duplicate_result["score"]
                    )

                complaint.save()

                # =========================================
                # CIVIC INCIDENT CLUSTERING
                # =========================================

                incident = get_or_create_incident(
                    complaint,
                    duplicate_result
                )

                complaint.incident = incident

                complaint.save()

                # =========================================
                # AI RESPONSE DATA
                # =========================================

                ai_reason = ai_result.get(
                    "reason",
                    ""
                )

                visual_evidence = ai_result.get(
                    "visual_evidence",
                    ""
                )

                ai_confidence = ai_result.get(
                    "confidence",
                    None
                )

            except Exception as error:

                print(
                    "GROQ VISION ERROR:",
                    error
                )

                ai_reason = (
                    "AI analysis could not be completed. "
                    "The complaint was still registered."
                )

            return render(
                request,
                "complaint_success.html",
                {
                    "complaint": complaint,
                    "ai_reason": ai_reason,
                    "visual_evidence": visual_evidence,
                    "ai_confidence": ai_confidence,
                }
            )

    else:

        form = ComplaintForm()

    return render(
        request,
        "report.html",
        {
            "form": form
        }
    )


def city_map(request):

    return render(
        request,
        "map.html"
    )


def complaint_api(request):

    complaints = (
        Complaint.objects
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
    )

    data = []

    for complaint in complaints:

        data.append({

            "id": str(
                complaint.complaint_id
            ),

            "category": (
                complaint.get_category_display()
            ),

            "description": (
                complaint.description
            ),

            "latitude": complaint.latitude,

            "longitude": complaint.longitude,

            "priority": complaint.priority,

            "status": complaint.status,

            "department": complaint.department,

            "created_at": (
                complaint.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                )
            ),
        })

    return JsonResponse({
        "complaints": data
    })


@login_required(login_url="/authority/login/")
def authority_dashboard(request):

    selected_department = request.GET.get(
        "department",
        ""
    )

    # =========================================
    # ALL COMPLAINTS
    # =========================================

    complaints = Complaint.objects.all()

    # =========================================
    # DEPARTMENT FILTER
    # =========================================

    if selected_department:

        complaints = complaints.filter(
            department=selected_department
        )

    # =========================================
    # HIGHEST SEVERITY FIRST
    # =========================================

    complaints = complaints.order_by(
        "-severity_score",
        "-created_at"
    )

    # =========================================
    # CIVIC INCIDENTS
    #
    # IMPORTANT:
    # The dashboard now displays CivicIncident
    # objects instead of individual complaints.
    #
    # Therefore:
    #
    # Complaint A ─┐
    # Complaint B ─┼──> Civic Incident #1
    # Complaint C ─┘
    #
    # appears only ONCE.
    # =========================================

    active_incidents = (
        CivicIncident.objects
        .filter(
            complaints__in=complaints
        )
        .annotate(
            report_count=Count(
                "complaints",
                distinct=True
            )
        )
        .distinct()
        .order_by(
            "-created_at"
        )
    )

    # =========================================
    # COMPLAINT STATISTICS
    # =========================================

    total_complaints = complaints.count()

    pending_count = complaints.filter(
        status="pending"
    ).count()

    in_progress_count = complaints.filter(
        status="in_progress"
    ).count()

    resolved_count = complaints.filter(
        status="resolved"
    ).count()

    critical_count = complaints.filter(
        priority="critical"
    ).count()

    high_count = complaints.filter(
        priority="high"
    ).count()

    # =========================================
    # DEPARTMENTS
    # =========================================

    departments = [

        "Municipal Sanitation",

        "Roads & Infrastructure",

        "Electrical Department",

        "Water Supply Department",

        "Drainage & Sewerage Department",

        "Traffic Department",

        "General Civic Services",

    ]

    # =========================================
    # CATEGORY ANALYTICS
    # =========================================

    category_stats = (
        Complaint.objects
        .values("category")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =========================================
    # PRIORITY ANALYTICS
    # =========================================

    priority_stats = (
        Complaint.objects
        .values("priority")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =========================================
    # DEPARTMENT ANALYTICS
    # =========================================

    department_stats = (
        Complaint.objects
        .values("department")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =========================================
    # STATUS ANALYTICS
    # =========================================

    status_stats = (
        Complaint.objects
        .values("status")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # =========================================
    # RESOLUTION RATE
    # =========================================

    resolved_total = (
        Complaint.objects
        .filter(status="resolved")
        .count()
    )

    all_total = Complaint.objects.count()

    resolution_rate = (

        round(
            (
                resolved_total
                / all_total
            ) * 100,
            1
        )

        if all_total > 0

        else 0
    )

    # =========================================
    # CONTEXT
    # =========================================

    context = {

        "complaints": complaints,

        "active_incidents": active_incidents,

        "total_complaints": total_complaints,

        "pending_count": pending_count,

        "in_progress_count": in_progress_count,

        "resolved_count": resolved_count,

        "critical_count": critical_count,

        "high_count": high_count,

        "departments": departments,

        "selected_department": (
            selected_department
        ),

        "category_stats": category_stats,

        "priority_stats": priority_stats,

        "department_stats": department_stats,

        "status_stats": status_stats,

        "resolution_rate": resolution_rate,
    }

    return render(
        request,
        "authority_dashboard.html",
        context
    )


@login_required(login_url="/authority/login/")
def complaint_detail(request, complaint_id):

    complaint = get_object_or_404(
        Complaint,
        complaint_id=complaint_id
    )

    return render(
        request,
        "complaint_detail.html",
        {
            "complaint": complaint
        }
    )


@login_required(login_url="/authority/login/")
def update_complaint_status(
    request,
    complaint_id
):
    complaint = get_object_or_404(
        Complaint,
        complaint_id=complaint_id
    )

    if request.method == "POST":

        new_status = request.POST.get("status")

        allowed_statuses = [
            "pending",
            "in_progress",
            "resolved",
        ]

        if new_status in allowed_statuses:

            # Update complaint status
            complaint.status = new_status
            complaint.save()

            # Update related Civic Incident
            if complaint.incident:

                incident = complaint.incident

                incident_complaints = (
                    incident.complaints.all()
                )

                statuses = list(
                    incident_complaints.values_list(
                        "status",
                        flat=True
                    )
                )

                # Incident is resolved only when
                # all complaints are resolved
                if statuses and all(
                    status == "resolved"
                    for status in statuses
                ):
                    incident.status = "resolved"

                # If any complaint is in progress,
                # incident is in progress
                elif "in_progress" in statuses:
                    incident.status = "in_progress"

                # Otherwise keep it pending
                else:
                    incident.status = "pending"

                incident.save()

    return redirect(
        "complaint_detail",
        complaint_id=complaint.complaint_id
    )

def authority_login(request):

    if request.user.is_authenticated:

        return redirect(
            "authority_dashboard"
        )

    error = ""

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if user.is_staff:

                login(
                    request,
                    user
                )

                return redirect(
                    "authority_dashboard"
                )

            error = (
                "You are not authorized "
                "to access the authority dashboard."
            )

        else:

            error = (
                "Invalid username or password."
            )

    return render(
        request,
        "authority_login.html",
        {
            "error": error
        }
    )


def authority_logout(request):

    logout(request)

    return redirect(
        "authority_login"
    )


def track_complaint(request):

    complaint = None

    error = ""

    if request.method == "POST":

        complaint_id = request.POST.get(
            "complaint_id",
            ""
        ).strip()

        if complaint_id:

            try:

                complaint = Complaint.objects.get(
                    complaint_id=complaint_id
                )

            except Complaint.DoesNotExist:

                error = (
                    "Complaint not found. "
                    "Please check your Complaint ID."
                )

        else:

            error = (
                "Please enter a Complaint ID."
            )

    return render(
        request,
        "track_complaint.html",
        {
            "complaint": complaint,
            "error": error,
        }
    )