from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
import tempfile, os, base64, json

from accounts.models import Student, Faculty, Course
from accounts.views import get_role
from .models import AttendanceSession, AttendanceRecord, Notification
from .forms import SessionForm


# ── SESSION MANAGEMENT ────────────────────────────────────────────────────────

@login_required
def create_session(request):
    role, profile = get_role(request.user)
    if role not in ('faculty', 'hod'):
        return redirect('dashboard')

    faculty = profile if role == 'faculty' else Faculty.objects.filter(department=profile.department).first()
    if not faculty:
        messages.error(request, "No faculty found. Please add faculty first.")
        return redirect('dashboard')

    form = SessionForm(request.POST or None, faculty=faculty if role == 'faculty' else None)

    if request.method == 'POST' and form.is_valid():
        session = form.save(commit=False)
        session.faculty = faculty if role == 'faculty' else Faculty.objects.get(pk=request.POST.get('faculty_override', faculty.pk))
        session.save()
        messages.success(request, f"Session created — {session.course.code} | {session.date}")
        return redirect('mark_attendance', pk=session.pk)

    return render(request, 'attendance/create_session.html', {'form': form, 'role': role})


@login_required
def mark_attendance(request, pk):
    session = get_object_or_404(AttendanceSession, pk=pk)
    role, profile = get_role(request.user)

    students = Student.objects.filter(
        department=session.course.department,
        section=session.section,
        is_active=True
    ).order_by('roll_number')

    # Pre-create absent records
    for s in students:
        AttendanceRecord.objects.get_or_create(session=session, student=s, defaults={'status': 'absent'})

    if request.method == 'POST':
        present_ids = request.POST.getlist('present_students')
        late_ids = request.POST.getlist('late_students')
        for s in students:
            record = AttendanceRecord.objects.get(session=session, student=s)
            if str(s.id) in present_ids:
                record.status = 'present'
                record.method = 'manual'
            elif str(s.id) in late_ids:
                record.status = 'late'
                record.method = 'manual'
            else:
                record.status = 'absent'
            record.save()

        _send_absence_notifications(session, students)
        session.is_active = False
        session.end_time = timezone.now().time()
        session.save()
        messages.success(request, f"✅ Attendance saved! Present: {session.present_count()}, Absent: {session.absent_count()}")
        return redirect('session_report', pk=session.pk)

    records = {r.student_id: r for r in AttendanceRecord.objects.filter(session=session)}
    return render(request, 'attendance/mark_attendance.html', {
        'session': session, 'students': students, 'records': records, 'role': role
    })


@login_required
def face_attendance(request, pk):
    """Face recognition attendance page."""
    session = get_object_or_404(AttendanceSession, pk=pk)
    role, profile = get_role(request.user)

    students = Student.objects.filter(
        department=session.course.department,
        section=session.section,
        is_active=True
    ).order_by('roll_number')

    for s in students:
        AttendanceRecord.objects.get_or_create(session=session, student=s, defaults={'status': 'absent'})

    enrolled_count = students.filter(face_enrolled=True).count()

    return render(request, 'attendance/face_attendance.html', {
        'session': session, 'students': students,
        'enrolled_count': enrolled_count, 'role': role
    })


# ── FACE RECOGNITION API ENDPOINTS ───────────────────────────────────────────

@login_required
def api_recognize_face(request, pk):
    """
    POST: base64 image → returns list of recognized student IDs.
    Used by the webcam face attendance page.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    session = get_object_or_404(AttendanceSession, pk=pk)
    data = json.loads(request.body)
    image_data = data.get('image', '')

    if not image_data:
        return JsonResponse({'error': 'No image data'}, status=400)

    students = Student.objects.filter(
        department=session.course.department,
        section=session.section,
        is_active=True,
        face_enrolled=True
    )

    # Save image to temp file
    tmp_path = None
    try:
        if ',' in image_data:
            _, imgstr = image_data.split(',', 1)
        else:
            imgstr = image_data

        img_bytes = base64.b64decode(imgstr)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        from .face_utils import recognize_faces_bulk
        recognized = recognize_faces_bulk(tmp_path, students)

        # Auto-mark recognized students as present
        newly_marked = []
        for student_id, confidence in recognized.items():
            try:
                record = AttendanceRecord.objects.get(session=session, student_id=student_id)
                if record.status != 'present':
                    record.status = 'present'
                    record.method = 'face'
                    record.face_confidence = confidence
                    record.save()
                    newly_marked.append({
                        'student_id': student_id,
                        'name': record.student.name,
                        'roll': record.student.roll_number,
                        'confidence': confidence
                    })
            except AttendanceRecord.DoesNotExist:
                pass

        return JsonResponse({
            'success': True,
            'recognized': newly_marked,
            'total_present': AttendanceRecord.objects.filter(session=session, status='present').count()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@login_required
def api_upload_recognize(request, pk):
    """
    POST: uploaded photo file → recognize and mark attendance.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    session = get_object_or_404(AttendanceSession, pk=pk)
    photo = request.FILES.get('photo')

    if not photo:
        return JsonResponse({'error': 'No photo uploaded'}, status=400)

    students = Student.objects.filter(
        department=session.course.department,
        section=session.section,
        is_active=True,
        face_enrolled=True
    )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            for chunk in photo.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        from .face_utils import recognize_faces_bulk
        recognized = recognize_faces_bulk(tmp_path, students)

        newly_marked = []
        for student_id, confidence in recognized.items():
            try:
                record = AttendanceRecord.objects.get(session=session, student_id=student_id)
                if record.status != 'present':
                    record.status = 'present'
                    record.method = 'face'
                    record.face_confidence = confidence
                    record.save()
                    newly_marked.append({
                        'student_id': student_id,
                        'name': record.student.name,
                        'roll': record.student.roll_number,
                        'confidence': confidence
                    })
            except AttendanceRecord.DoesNotExist:
                pass

        return JsonResponse({
            'success': True,
            'recognized': newly_marked,
            'total': len(newly_marked)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@login_required
def api_session_stats(request, pk):
    session = get_object_or_404(AttendanceSession, pk=pk)
    records = AttendanceRecord.objects.filter(session=session)
    return JsonResponse({
        'present': session.present_count(),
        'absent': session.absent_count(),
        'late': session.late_count(),
        'total': session.total_students(),
        'percentage': session.percentage(),
        'face_marked': records.filter(method='face').count(),
        'manual_marked': records.filter(method='manual').count(),
    })


@login_required
def finalize_face_session(request, pk):
    """Finalize session after face recognition."""
    session = get_object_or_404(AttendanceSession, pk=pk)
    if request.method == 'POST':
        # Handle any manual overrides submitted with the form
        students = Student.objects.filter(
            department=session.course.department,
            section=session.section, is_active=True
        )
        _send_absence_notifications(session, students)
        session.is_active = False
        session.end_time = timezone.now().time()
        session.save()
        messages.success(request, f"✅ Session finalized! Present: {session.present_count()}, Absent: {session.absent_count()}")
        return redirect('session_report', pk=pk)
    return redirect('face_attendance', pk=pk)


# ── REPORTS ───────────────────────────────────────────────────────────────────

@login_required
def session_report(request, pk):
    session = get_object_or_404(AttendanceSession, pk=pk)
    records = AttendanceRecord.objects.filter(session=session).select_related('student').order_by('student__roll_number')
    role, _ = get_role(request.user)
    return render(request, 'attendance/session_report.html', {
        'session': session, 'records': records, 'role': role
    })


@login_required
def all_sessions(request):
    role, profile = get_role(request.user)
    if role == 'faculty':
        sessions = AttendanceSession.objects.filter(faculty=profile).order_by('-date', '-start_time')
    elif role == 'hod':
        sessions = AttendanceSession.objects.filter(course__department=profile.department).order_by('-date', '-start_time')
    else:
        return redirect('dashboard')

    date_filter = request.GET.get('date', '')
    course_filter = request.GET.get('course', '')
    if date_filter:
        sessions = sessions.filter(date=date_filter)
    if course_filter:
        sessions = sessions.filter(course__id=course_filter)

    courses = Course.objects.filter(department=profile.department)
    return render(request, 'attendance/all_sessions.html', {
        'sessions': sessions, 'courses': courses,
        'date_filter': date_filter, 'course_filter': course_filter, 'role': role
    })


@login_required
def absentees_report(request):
    role, profile = get_role(request.user)
    target_date = request.GET.get('date', str(date.today()))
    course_id = request.GET.get('course', '')

    sessions = AttendanceSession.objects.filter(course__department=profile.department, date=target_date)
    if course_id:
        sessions = sessions.filter(course__id=course_id)

    absentees = AttendanceRecord.objects.filter(
        session__in=sessions, status='absent'
    ).select_related('student', 'session__course').order_by('student__roll_number')

    courses = Course.objects.filter(department=profile.department)
    return render(request, 'attendance/absentees_report.html', {
        'absentees': absentees, 'target_date': target_date,
        'courses': courses, 'course_id': course_id, 'role': role
    })


@login_required
def notifications_view(request):
    role, profile = get_role(request.user)
    if role != 'student':
        return redirect('dashboard')
    notifs = Notification.objects.filter(student=profile).order_by('-sent_at')
    notifs.update(is_read=True)
    return render(request, 'attendance/notifications.html', {'notifications': notifs})


# ── HELPER ────────────────────────────────────────────────────────────────────

def _send_absence_notifications(session, students):
    absent_records = AttendanceRecord.objects.filter(session=session, status='absent')
    for record in absent_records:
        Notification.objects.create(
            student=record.student,
            message=(f"⚠️ Absent Alert: You were marked ABSENT in "
                     f"{session.course.name} ({session.course.code}) "
                     f"on {session.date}. Section: {session.section}. "
                     f"Please maintain 75%+ attendance."),
            notif_type='absence'
        )
