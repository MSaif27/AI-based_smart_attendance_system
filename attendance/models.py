from django.db import models
from accounts.models import Student, Faculty, Course


class AttendanceSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    section = models.CharField(max_length=10, default='A')
    is_active = models.BooleanField(default=True)
    mode = models.CharField(max_length=20, default='manual',
                            choices=[('manual', 'Manual'), ('face', 'Face Recognition'), ('both', 'Both')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} | {self.date} | Sec-{self.section}"

    def total_students(self):
        return self.attendancerecord_set.count()

    def present_count(self):
        return self.attendancerecord_set.filter(status='present').count()

    def absent_count(self):
        return self.attendancerecord_set.filter(status='absent').count()

    def late_count(self):
        return self.attendancerecord_set.filter(status='late').count()

    def percentage(self):
        total = self.total_students()
        if total == 0:
            return 0
        return round(self.present_count() / total * 100, 1)


class AttendanceRecord(models.Model):
    STATUS = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]
    METHOD = [('manual', 'Manual'), ('face', 'Face Recognition'), ('webcam', 'Webcam')]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS, default='absent')
    method = models.CharField(max_length=10, choices=METHOD, default='manual')
    marked_at = models.DateTimeField(auto_now_add=True)
    face_confidence = models.FloatField(null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.roll_number} | {self.status}"


class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notif_type = models.CharField(max_length=30, default='absence')

    def __str__(self):
        return f"→ {self.student.name}: {self.message[:40]}"
