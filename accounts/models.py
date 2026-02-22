from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    def total_faculty(self):
        return self.faculty_set.count()

    def total_students(self):
        return self.student_set.count()


class HOD(models.Model):
    """Admin / Head of Department"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='hod/', blank=True, null=True)
    joined_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"HOD: {self.name}"


class Course(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    credits = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    courses = models.ManyToManyField(Course, blank=True)
    photo = models.ImageField(upload_to='faculty/', blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True)
    joined_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_id} - {self.name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    parent_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    courses = models.ManyToManyField(Course, blank=True)  # ✅ IMPORTANT FIX

    section = models.CharField(max_length=10, default='A')
    semester = models.IntegerField(default=1)

    photo = models.ImageField(upload_to='students/', null=True, blank=True)
    face_enrolled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.roll_number} - {self.name}"

    def attendance_percentage(self, course=None):
        from attendance.models import AttendanceRecord
        qs = AttendanceRecord.objects.filter(student=self)
        if course:
            qs = qs.filter(session__course=course)
        total = qs.count()
        present = qs.filter(status='present').count()
        if total == 0:
            return 0.0
        return round((present / total) * 100, 1)

    def is_below_threshold(self):
        return self.attendance_percentage() < 75
