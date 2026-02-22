from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Faculty management (HOD)
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/add/', views.add_faculty, name='add_faculty'),
    path('faculty/<int:pk>/edit/', views.edit_faculty, name='edit_faculty'),

    # Student management (Faculty/HOD)
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),

    # HOD management
    path('departments/', views.manage_departments, name='manage_departments'),
    path('courses/', views.manage_courses, name='manage_courses'),
]
