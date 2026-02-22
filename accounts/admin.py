from django.contrib import admin
from .models import Department, HOD, Faculty, Student, Course

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']

@admin.register(HOD)
class HODAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'department', 'email']

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'name', 'department', 'is_active']
    filter_horizontal = ['courses']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'name', 'department', 'section', 'face_enrolled']
    list_filter = ['department', 'section', 'face_enrolled']
    search_fields = ['name', 'roll_number']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credits']
