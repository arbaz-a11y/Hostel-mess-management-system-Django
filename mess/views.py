from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import LeaveRequestForm, MealAbsenceForm, StudentSignupForm, USNAuthenticationForm
from .models import LeaveRequest, MealAbsence, StudentProfile, StudentUser


def _get_student_profile(user: StudentUser) -> StudentProfile | None:
    try:
        return user.profile
    except StudentProfile.DoesNotExist:
        return None


def home(request):
    return render(request, "mess/home.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            usn = form.cleaned_data["usn"]
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]
            room_number = form.cleaned_data["room_number"]
            password = form.cleaned_data["password"]

            user = StudentUser.objects.create_user(
                username=usn,
                email=email,
                password=password,
                first_name=full_name,
            )

            StudentProfile.objects.create(
                user=user,
                full_name=full_name,
                usn=usn,
                email=email,
                room_number=room_number,
            )

            login(request, user)
            messages.success(request, "Signup successful. Welcome!")
            return redirect("student_dashboard")
    else:
        form = StudentSignupForm()

    return render(request, "mess/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        form = USNAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Logged in successfully.")
            return redirect("student_dashboard")
    else:
        form = USNAuthenticationForm(request)

    return render(request, "mess/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def student_dashboard(request):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found. Please contact admin.")
        return redirect("home")

    today = timezone.localdate()

    # A student is absent if they submitted a single-meal absence OR have an active leave covering today.
    leave_active_today = LeaveRequest.objects.filter(
        student=profile, from_date__lte=today, to_date__gte=today
    ).exists()

    absent_breakfast = leave_active_today or MealAbsence.objects.filter(
        student=profile, date=today, meal_type=MealAbsence.MealType.BREAKFAST
    ).exists()
    absent_lunch = leave_active_today or MealAbsence.objects.filter(
        student=profile, date=today, meal_type=MealAbsence.MealType.LUNCH
    ).exists()
    absent_dinner = leave_active_today or MealAbsence.objects.filter(
        student=profile, date=today, meal_type=MealAbsence.MealType.DINNER
    ).exists()

    upcoming_meal_absences = MealAbsence.objects.filter(
        student=profile, date__gte=today
    ).order_by("date", "meal_type")
    upcoming_leave_requests = LeaveRequest.objects.filter(
        student=profile, to_date__gte=today
    ).order_by("from_date")

    return render(
        request,
        "mess/student_dashboard.html",
        {
            "profile": profile,
            "today": today,
            "absent_breakfast": absent_breakfast,
            "absent_lunch": absent_lunch,
            "absent_dinner": absent_dinner,
            "upcoming_meal_absences": upcoming_meal_absences,
            "upcoming_leave_requests": upcoming_leave_requests,
        },
    )


@login_required
def meal_absence_create(request):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("home")

    if request.method == "POST":
        form = MealAbsenceForm(request.POST, student=profile)
        if form.is_valid():
            obj: MealAbsence = form.save(commit=False)
            obj.student = profile
            obj.save()
            messages.success(request, "Meal absence submitted successfully.")
            return redirect("request_history")
    else:
        form = MealAbsenceForm()

    return render(request, "mess/meal_absence_form.html", {"form": form})


@login_required
def leave_request_create(request):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("home")

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            obj: LeaveRequest = form.save(commit=False)
            obj.student = profile
            obj.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect("request_history")
    else:
        form = LeaveRequestForm()

    return render(request, "mess/leave_request_form.html", {"form": form})


@login_required
def request_history(request):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("home")

    today = timezone.localdate()

    meal_absences = MealAbsence.objects.filter(student=profile)
    leave_requests = LeaveRequest.objects.filter(student=profile)

    return render(
        request,
        "mess/request_history.html",
        {
            "today": today,
            "meal_absences": meal_absences,
            "leave_requests": leave_requests,
        },
    )


@login_required
def cancel_meal_absence(request, pk: int):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("home")

    obj = get_object_or_404(MealAbsence, pk=pk, student=profile)
    today = timezone.localdate()

    if request.method == "POST":
        if obj.date < today:
            messages.error(request, "You cannot cancel past meal requests.")
        else:
            obj.delete()
            messages.success(request, "Meal absence request cancelled.")
    else:
        messages.error(request, "Invalid request.")

    return redirect("request_history")


@login_required
def cancel_leave_request(request, pk: int):
    profile = _get_student_profile(request.user)
    if profile is None:
        messages.error(request, "Student profile not found.")
        return redirect("home")

    obj = get_object_or_404(LeaveRequest, pk=pk, student=profile)
    today = timezone.localdate()

    if request.method == "POST":
        if obj.to_date < today:
            messages.error(request, "You cannot cancel past leave requests.")
        else:
            obj.delete()
            messages.success(request, "Leave request cancelled.")
    else:
        messages.error(request, "Invalid request.")

    return redirect("request_history")


def _parse_date_param(date_str: str | None) -> date:
    if not date_str:
        return timezone.localdate()
    parsed = parse_date(date_str)
    return parsed or timezone.localdate()


@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    today = timezone.localdate()
    filter_date = _parse_date_param(request.GET.get("date"))
    q = (request.GET.get("q") or "").strip()

    students_count = StudentProfile.objects.count()
    active_leave_requests = LeaveRequest.objects.filter(to_date__gte=today).count()

    def absent_student_ids_for_meal(meal_type: str) -> set[int]:
        single = set(
            MealAbsence.objects.filter(date=filter_date, meal_type=meal_type).values_list(
                "student_id", flat=True
            )
        )
        leave = set(
            LeaveRequest.objects.filter(
                from_date__lte=filter_date, to_date__gte=filter_date
            ).values_list("student_id", flat=True)
        )
        return single | leave

    absent_breakfast_ids = absent_student_ids_for_meal(MealAbsence.MealType.BREAKFAST)
    absent_lunch_ids = absent_student_ids_for_meal(MealAbsence.MealType.LUNCH)
    absent_dinner_ids = absent_student_ids_for_meal(MealAbsence.MealType.DINNER)

    absent_breakfast_count = len(absent_breakfast_ids)
    absent_lunch_count = len(absent_lunch_ids)
    absent_dinner_count = len(absent_dinner_ids)

    estimated_meal_reduction = absent_breakfast_count + absent_lunch_count + absent_dinner_count

    meal_absences = MealAbsence.objects.select_related("student").filter(date=filter_date)
    leave_requests = LeaveRequest.objects.select_related("student").filter(
        from_date__lte=filter_date, to_date__gte=filter_date
    )

    students = StudentProfile.objects.select_related("user").order_by("usn")

    if q:
        students = students.filter(
            Q(full_name__icontains=q) | Q(usn__icontains=q) | Q(email__icontains=q)
        )
        meal_absences = meal_absences.filter(
            Q(student__full_name__icontains=q)
            | Q(student__usn__icontains=q)
            | Q(student__email__icontains=q)
        )
        leave_requests = leave_requests.filter(
            Q(student__full_name__icontains=q)
            | Q(student__usn__icontains=q)
            | Q(student__email__icontains=q)
        )

    return render(
        request,
        "mess/admin_dashboard.html",
        {
            "today": today,
            "filter_date": filter_date,
            "q": q,
            "students_count": students_count,
            "active_leave_requests": active_leave_requests,
            "absent_breakfast_count": absent_breakfast_count,
            "absent_lunch_count": absent_lunch_count,
            "absent_dinner_count": absent_dinner_count,
            "estimated_meal_reduction": estimated_meal_reduction,
            "students": students,
            "meal_absences": meal_absences,
            "leave_requests": leave_requests,
        },
    )


@user_passes_test(lambda u: u.is_staff)
def admin_delete_meal_absence(request, pk: int):
    obj = get_object_or_404(MealAbsence, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Meal absence request deleted.")
    else:
        messages.error(request, "Invalid request.")
    return redirect("admin_dashboard")


@user_passes_test(lambda u: u.is_staff)
def admin_delete_leave_request(request, pk: int):
    obj = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Leave request deleted.")
    else:
        messages.error(request, "Invalid request.")
    return redirect("admin_dashboard")
