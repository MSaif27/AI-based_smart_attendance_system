@echo off
echo ╔══════════════════════════════════════════╗
echo ║   LPU SmartAttend - Setup               ║
echo ╚══════════════════════════════════════════╝

echo.
echo [1/4] Installing packages...
pip install -r requirements.txt

echo.
echo [2/4] Making migrations...
python manage.py makemigrations accounts attendance
python manage.py migrate

echo.
echo [3/4] Loading sample data...
python manage.py seed_data

echo.
echo [4/4] Starting server...
echo.
echo ╔══════════════════════════════════════════╗
echo ║  Open: http://127.0.0.1:8000            ║
echo ║  HOD:     hod / hod123                  ║
echo ║  Faculty: faculty1 / fac123             ║
echo ╚══════════════════════════════════════════╝
echo.
python manage.py runserver
