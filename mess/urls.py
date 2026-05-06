from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("absence/new/", views.meal_absence_create, name="meal_absence_create"),
    path("leave/new/", views.leave_request_create, name="leave_request_create"),
    path("requests/", views.request_history, name="request_history"),
    path(
        "requests/meal/<int:pk>/cancel/",
        views.cancel_meal_absence,
        name="cancel_meal_absence",
    ),
    path(
        "requests/leave/<int:pk>/cancel/",
        views.cancel_leave_request,
        name="cancel_leave_request",
    ),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path(
        "admin-panel/meal-absence/<int:pk>/delete/",
        views.admin_delete_meal_absence,
        name="admin_delete_meal_absence",
    ),
    path(
        "admin-panel/leave/<int:pk>/delete/",
        views.admin_delete_leave_request,
        name="admin_delete_leave_request",
    ),
]

