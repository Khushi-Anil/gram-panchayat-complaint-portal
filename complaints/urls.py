from django.urls import path

from . import views

app_name = "complaints"

urlpatterns = [
    path("", views.public_dashboard, name="public_dashboard"),
    path("submit/", views.submit_complaint, name="submit"),
    path("track/", views.track_complaint, name="track"),
    path("ledger/", views.public_ledger, name="ledger"),
    path("duplicates/", views.possible_duplicates, name="duplicates"),
    path("feedback/", views.portal_feedback, name="portal_feedback"),
    path("feedback/complaint/<str:complaint_id>/", views.citizen_feedback, name="citizen_feedback"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("categories/", views.categories, name="categories"),
    path("helpdesk/", views.helpdesk, name="helpdesk"),
    path("citizen/register/", views.citizen_register, name="citizen_register"),
    path("citizen/login/", views.CitizenLoginView.as_view(), name="citizen_login"),
    path("citizen/logout/", views.CitizenLogoutView.as_view(), name="citizen_logout"),
    path("citizen/complaints/", views.citizen_dashboard, name="citizen_dashboard"),
    path(
        "citizen/complaints/<str:complaint_id>/edit/",
        views.citizen_complaint_edit,
        name="citizen_edit",
    ),
    path("official/login/", views.OfficialLoginView.as_view(), name="official_login"),
    path("official/logout/", views.OfficialLogoutView.as_view(), name="official_logout"),
    path("official/complaints/", views.official_dashboard, name="official_dashboard"),
    path(
        "official/complaints/<str:complaint_id>/archive/",
        views.official_complaint_archive,
        name="official_archive",
    ),
    path(
        "official/complaints/<str:complaint_id>/",
        views.official_complaint_update,
        name="official_update",
    ),
    path("submitted/<str:complaint_id>/", views.submission_success, name="success"),
]
