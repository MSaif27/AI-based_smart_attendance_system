from django.urls import path
from . import views

urlpatterns = [
    path('sessions/', views.all_sessions, name='all_sessions'),
    path('sessions/create/', views.create_session, name='create_session'),
    path('sessions/<int:pk>/manual/', views.mark_attendance, name='mark_attendance'),
    path('sessions/<int:pk>/face/', views.face_attendance, name='face_attendance'),
    path('sessions/<int:pk>/face/finalize/', views.finalize_face_session, name='finalize_face_session'),
    path('sessions/<int:pk>/report/', views.session_report, name='session_report'),

    # API
    path('api/sessions/<int:pk>/recognize/', views.api_recognize_face, name='api_recognize_face'),
    path('api/sessions/<int:pk>/upload-recognize/', views.api_upload_recognize, name='api_upload_recognize'),
    path('api/sessions/<int:pk>/stats/', views.api_session_stats, name='api_session_stats'),

    # Reports
    path('reports/absentees/', views.absentees_report, name='absentees_report'),
    path('notifications/', views.notifications_view, name='notifications'),
]
