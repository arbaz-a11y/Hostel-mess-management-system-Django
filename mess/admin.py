from django.contrib import admin

from .models import LeaveRequest, MealAbsence, StudentProfile, StudentUser


@admin.register(StudentUser)
class StudentUserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email", "first_name", "last_name")
    list_display = ("username", "email", "first_name", "last_name", "is_staff")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    search_fields = ("usn", "full_name", "email", "room_number")
    list_display = ("full_name", "usn", "email", "room_number")


@admin.register(MealAbsence)
class MealAbsenceAdmin(admin.ModelAdmin):
    search_fields = ("student__usn", "student__full_name")
    list_display = ("student", "date", "meal_type", "created_at")
    list_filter = ("date", "meal_type")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    search_fields = ("student__usn", "student__full_name")
    list_display = ("student", "from_date", "to_date", "created_at")
    list_filter = ("from_date", "to_date")
