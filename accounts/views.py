from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
import json, base64, os
from django.core.files.base import ContentFile
from django.conf import settings

from .models import Department, HOD, Faculty, Student, Course
from .forms import (LoginForm, FacultyForm, StudentForm,
                    FacultyUserForm, StudentUserForm, CourseForm, DepartmentForm)


def get_role(user):
    try:
        return 'hod', user.hod
    except Exception:
        pass
    try:
        return 'faculty', user.faculty
    except Exception:
        pass
    try:
        return 'student', user.student
    except Exception:
        pass
    return 'unknown', None


# ── AUTH ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    role, profile = get_role(request.user)
    from attendance.models import AttendanceSession, AttendanceRecord, Notification
    from datetime import date

    ctx = {'role': role, 'profile': profile, 'today': date.today()}

    if role == 'hod':
        ctx.update({
            'total_faculty': Faculty.objects.filter(department=profile.department).count(),
            'total_students': Student.objects.filter(department=profile.department).count(),
            'total_sessions': AttendanceSession.objects.filter(course__department=profile.department).count(),
            'recent_faculty': Faculty.objects.filter(department=profile.department).order_by('-id')[:5],
            'departments': Department.objects.all(),
            'low_attendance': Student.objects.filter(department=profile.department, is_active=True),
        })

    elif role == 'faculty':
        sessions = AttendanceSession.objects.filter(faculty=profile).order_by('-date', '-start_time')
        ctx.update({
            'recent_sessions': sessions[:6],
            'total_sessions': sessions.count(),
            'sessions_today': sessions.filter(date=date.today()).count(),
            'my_courses': profile.courses.all(),
        })

    elif role == 'student':
        records = AttendanceRecord.objects.filter(student=profile)
        total = records.count()
        present = records.filter(status='present').count()
        ctx.update({
            'total': total,
            'present': present,
            'absent': records.filter(status='absent').count(),
            'percentage': round(present / total * 100, 1) if total else 0,
            'notifications': Notification.objects.filter(student=profile, is_read=False)[:5],
            'recent_records': records.order_by('-session__date')[:10],
        })

    return render(request, 'accounts/dashboard.html', ctx)


# ── HOD: MANAGE FACULTY ───────────────────────────────────────────────────────

@login_required
def faculty_list(request):
    role, profile = get_role(request.user)
    if role != 'hod':
        return redirect('dashboard')
    q = request.GET.get('q', '')
    faculty = Faculty.objects.filter(department=profile.department)
    if q:
        faculty = faculty.filter(Q(name__icontains=q) | Q(employee_id__icontains=q))
    return render(request, 'accounts/faculty_list.html', {'faculty': faculty, 'q': q})


@login_required
def add_faculty(request):
    role, profile = get_role(request.user)
    if role != 'hod':
        return redirect('dashboard')

    user_form = FacultyUserForm(request.POST or None)
    faculty_form = FacultyForm(request.POST or None, request.FILES or None, department=profile.department)

    if request.method == 'POST' and user_form.is_valid() and faculty_form.is_valid():
        user = user_form.save(commit=False)
        user.set_password(user_form.cleaned_data['password'])
        user.is_staff = True
        user.save()
        faculty = faculty_form.save(commit=False)
        faculty.user = user
        faculty.department = profile.department
        faculty.save()
        faculty_form.save_m2m()
        messages.success(request, f"Faculty {faculty.name} added successfully!")
        return redirect('faculty_list')

    return render(request, 'accounts/add_faculty.html', {
        'user_form': user_form, 'faculty_form': faculty_form
    })


@login_required
def edit_faculty(request, pk):
    role, profile = get_role(request.user)
    if role != 'hod':
        return redirect('dashboard')
    faculty = get_object_or_404(Faculty, pk=pk, department=profile.department)
    faculty_form = FacultyForm(request.POST or None, request.FILES or None,
                                instance=faculty, department=profile.department)
    if request.method == 'POST' and faculty_form.is_valid():
        faculty_form.save()
        messages.success(request, "Faculty updated!")
        return redirect('faculty_list')
    return render(request, 'accounts/edit_faculty.html', {'faculty_form': faculty_form, 'faculty': faculty})


# ── FACULTY: MANAGE STUDENTS ──────────────────────────────────────────────────

@login_required
def student_list(request):
    role, profile = get_role(request.user)
    if role not in ('hod', 'faculty'):
        return redirect('dashboard')

    q = request.GET.get('q', '')
    section = request.GET.get('section', '')

    if role == 'hod':
        students = Student.objects.filter(department=profile.department)
    else:
        students = Student.objects.filter(department=profile.department)

    if q:
        students = students.filter(Q(name__icontains=q) | Q(roll_number__icontains=q))
    if section:
        students = students.filter(section=section)

    return render(request, 'accounts/student_list.html', {
        'students': students.order_by('roll_number'),
        'q': q, 'section': section, 'role': role
    })


@login_required
def add_student(request):
    role, profile = get_role(request.user)
    if role not in ('hod', 'faculty'):
        return redirect('dashboard')

    user_form = StudentUserForm(request.POST or None)
    student_form = StudentForm(request.POST or None, request.FILES or None, department=profile.department)

    if request.method == 'POST':
        # Handle webcam photo
        webcam_data = request.POST.get('webcam_photo')
        photo_file = None
        if webcam_data and webcam_data.startswith('data:image'):
            format, imgstr = webcam_data.split(';base64,')
            ext = format.split('/')[-1]
            photo_file = ContentFile(base64.b64decode(imgstr), name=f'webcam_student.{ext}')

        if student_form.is_valid():
            student = student_form.save(commit=False)
            student.department = profile.department

            # Photo: webcam takes priority over upload
            if photo_file:
                student.photo = photo_file
                student.face_enrolled = True
            elif student.photo:
                student.face_enrolled = True

            # Create login user if username provided
            if user_form.is_valid() and user_form.cleaned_data.get('username'):
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password'])
                user.save()
                student.user = user

            student.save()
            messages.success(request, f"Student {student.name} added with face enrolled!")
            return redirect('student_list')
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'accounts/add_student.html', {
        'user_form': user_form,
        'student_form': student_form,
    })


@login_required
def edit_student(request, pk):
    role, profile = get_role(request.user)
    if role not in ('hod', 'faculty'):
        return redirect('dashboard')
    student = get_object_or_404(Student, pk=pk)
    student_form = StudentForm(request.POST or None, request.FILES or None,
                                instance=student, department=profile.department)

    if request.method == 'POST':
        webcam_data = request.POST.get('webcam_photo')
        if webcam_data and webcam_data.startswith('data:image'):
            format, imgstr = webcam_data.split(';base64,')
            ext = format.split('/')[-1]
            photo_file = ContentFile(base64.b64decode(imgstr), name=f'webcam_{student.roll_number}.{ext}')
            student.photo = photo_file
            student.face_enrolled = True
            student.save()

        if student_form.is_valid():
            s = student_form.save(commit=False)
            if s.photo:
                s.face_enrolled = True
            s.save()
            messages.success(request, "Student updated!")
            return redirect('student_list')

    return render(request, 'accounts/edit_student.html', {
        'student_form': student_form, 'student': student
    })


@login_required
def student_detail(request, pk):
    role, profile = get_role(request.user)
    student = get_object_or_404(Student, pk=pk)
    from attendance.models import AttendanceRecord, AttendanceSession
    records = AttendanceRecord.objects.filter(student=student).select_related('session__course').order_by('-session__date')
    total = records.count()
    present = records.filter(status='present').count()
    percentage = round(present / total * 100, 1) if total else 0

    # Per-course stats
    courses = Course.objects.filter(attendancesession__attendancerecord__student=student).distinct()
    course_stats = []
    for c in courses:
        cr = records.filter(session__course=c)
        ct = cr.count()
        cp = cr.filter(status='present').count()
        course_stats.append({'course': c, 'total': ct, 'present': cp,
                              'percentage': round(cp / ct * 100, 1) if ct else 0})

    return render(request, 'accounts/student_detail.html', {
        'student': student, 'records': records[:20],
        'total': total, 'present': present,
        'absent': records.filter(status='absent').count(),
        'percentage': percentage, 'course_stats': course_stats, 'role': role
    })


# ── HOD: MANAGE DEPARTMENTS & COURSES ─────────────────────────────────────────

@login_required
def manage_departments(request):
    role, profile = get_role(request.user)
    if role != 'hod':
        return redirect('dashboard')
    dept_form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and dept_form.is_valid():
        dept_form.save()
        messages.success(request, "Department added!")
        return redirect('manage_departments')
    departments = Department.objects.all()
    return render(request, 'accounts/manage_departments.html', {
        'departments': departments, 'dept_form': dept_form
    })


@login_required
def manage_courses(request):
    role, profile = get_role(request.user)
    if role != 'hod':
        return redirect('dashboard')
    course_form = CourseForm(request.POST or None)
    if request.method == 'POST' and course_form.is_valid():
        course_form.save()
        messages.success(request, "Course added!")
        return redirect('manage_courses')
    courses = Course.objects.filter(department=profile.department)
    return render(request, 'accounts/manage_courses.html', {
        'courses': courses, 'course_form': course_form
    })
