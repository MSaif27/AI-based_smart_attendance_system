from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord, Notification

@admin.register(AttendanceSession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['course', 'faculty', 'date', 'section', 'mode', 'is_active']
    list_filter = ['date', 'mode', 'is_active']

@admin.register(AttendanceRecord)
class RecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'method', 'face_confidence']
    list_filter = ['status', 'method']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notif_type', 'sent_at', 'is_read']
