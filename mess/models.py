from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class StudentUser(AbstractUser):
    """
    Custom user model so we can use USN as the login identifier.

    We keep Django's default password hashing/verification by inheriting
    from AbstractUser (built-in authentication system).
    """

    # Keep the default `username` field from AbstractUser.
    # During signup we set `username = usn`.
    pass


class StudentProfile(models.Model):
    """
    Extra student information displayed on dashboards.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=150)
    usn = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    room_number = models.CharField(max_length=20)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.usn})"


class MealAbsence(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "BREAKFAST", "Breakfast"
        LUNCH = "LUNCH", "Lunch"
        DINNER = "DINNER", "Dinner"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="meal_absences",
    )
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MealType.choices)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Prevent duplicate meal requests for the same student/date/meal.
            models.UniqueConstraint(
                fields=["student", "date", "meal_type"],
                name="unique_meal_absence_per_day",
            )
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.student.usn} - {self.meal_type} on {self.date}"


class LeaveRequest(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-from_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.student.usn} - Leave {self.from_date} to {self.to_date}"

