from django.urls import path
from . import views


urlpatterns = [

    # =================================================
    # CITIZEN PAGES
    # =================================================

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "report/",
        views.report_complaint,
        name="report_complaint"
    ),

    path(
        "map/",
        views.city_map,
        name="city_map"
    ),

    path(
        "track/",
        views.track_complaint,
        name="track_complaint"
    ),

    path(
        "api/complaints/",
        views.complaint_api,
        name="complaint_api"
    ),


    # =================================================
    # AUTHORITY PAGES
    # =================================================

    path(
        "authority/login/",
        views.authority_login,
        name="authority_login"
    ),

    path(
        "authority/",
        views.authority_dashboard,
        name="authority_dashboard"
    ),

    path(
        "authority/logout/",
        views.authority_logout,
        name="authority_logout"
    ),


    # =================================================
    # AUTHORITY COMPLAINT MANAGEMENT
    # =================================================

    path(
        "authority/complaint/<uuid:complaint_id>/",
        views.complaint_detail,
        name="complaint_detail"
    ),

    path(
        "authority/complaint/<uuid:complaint_id>/status/",
        views.update_complaint_status,
        name="update_complaint_status"
    ),

]