from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Department, Course, HOD, Faculty, Student


class Command(BaseCommand):
    help = 'Seed initial data for LPU Smart Attendance'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding database...')

        # Departments
        cse = Department.objects.get_or_create(name='Computer Science & Engineering', code='CSE')[0]
        ece = Department.objects.get_or_create(name='Electronics & Communication', code='ECE')[0]

        # Courses
        py_course  = Course.objects.get_or_create(name='Python & Full Stack', code='CSE401', department=cse, defaults={'credits': 4})[0]
        ds_course  = Course.objects.get_or_create(name='Data Structures', code='CSE301', department=cse, defaults={'credits': 3})[0]
        dbms       = Course.objects.get_or_create(name='Database Management', code='CSE302', department=cse, defaults={'credits': 3})[0]

        # HOD
        hod_user, _ = User.objects.get_or_create(username='hod', defaults={
            'first_name': 'Dr. Sunita', 'last_name': 'Sharma',
            'email': 'hod@lpu.in', 'is_staff': True, 'is_superuser': True
        })
        hod_user.set_password('hod123')
        hod_user.save()
        HOD.objects.get_or_create(user=hod_user, defaults={
            'name': 'Dr. Sunita Sharma', 'employee_id': 'HOD001',
            'email': 'hod@lpu.in', 'department': cse
        })

        # Faculty
        fac_user, _ = User.objects.get_or_create(username='faculty1', defaults={
            'first_name': 'Dr. Rajesh', 'last_name': 'Kumar',
            'email': 'faculty@lpu.in', 'is_staff': True
        })
        fac_user.set_password('fac123')
        fac_user.save()
        faculty, _ = Faculty.objects.get_or_create(user=fac_user, defaults={
            'name': 'Dr. Rajesh Kumar', 'employee_id': 'FAC001',
            'email': 'faculty@lpu.in', 'department': cse,
            'qualification': 'Ph.D Computer Science'
        })
        faculty.courses.set([py_course, ds_course, dbms])

        # Students
        for roll, name, email in [
            ('21CSE001', 'Arjun Sharma', 'arjun@lpu.in'),
            ('21CSE002', 'Priya Singh', 'priya@lpu.in'),
            ('21CSE003', 'Rahul Gupta', 'rahul@lpu.in'),
            ('21CSE004', 'Ananya Patel', 'ananya@lpu.in'),
            ('21CSE005', 'Vikram Mehta', 'vikram@lpu.in'),
        ]:
            Student.objects.get_or_create(roll_number=roll, defaults={
                'name': name, 'email': email,
                'parent_email': f'parent_{roll}@gmail.com',
                'department': cse, 'section': 'A', 'semester': 5
            })

        self.stdout.write(self.style.SUCCESS('''
╔══════════════════════════════════════╗
║   ✅ LPU SmartAttend Ready!          ║
╠══════════════════════════════════════╣
║  HOD      →  hod       / hod123     ║
║  Faculty  →  faculty1  / fac123     ║
╠══════════════════════════════════════╣
║  http://127.0.0.1:8000              ║
╚══════════════════════════════════════╝
        '''))
