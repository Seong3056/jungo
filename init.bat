
@echo off
title Django 프로젝트 자동 초기화
echo =====================================
echo  🚀 비대면 중고거래 플랫폼 초기화 스크립트
echo =====================================
echo.

set /p PROJPATH=프로젝트 폴더 경로를 입력하세요 (예: C:\Users\user\Desktop\bidamen_jungo_final): 
if "%PROJPATH%"=="" (
    echo [오류] 경로가 비어 있습니다.
    pause
    exit /b 1
)
if not exist "%PROJPATH%\manage.py" (
    echo [오류] 입력한 경로에 manage.py가 없습니다: "%PROJPATH%"
    pause
    exit /b 1
)

cd /d "%PROJPATH%"
echo 현재 경로: %cd%

if not exist .venv (
    echo 📦 가상환경 생성 중...
    py -m venv .venv
) else (
    echo ✅ 기존 가상환경이 존재합니다.
)

echo ⚙️  가상환경 활성화...
call .venv\Scripts\activate

python -m pip install --upgrade pip
pip install django pillow djangorestframework python-dotenv

echo 🗃️  DB 마이그레이션 수행...
python manage.py makemigrations
python manage.py makemigrations chat
python manage.py migrate

echo 🚀 개발 서버를 시작합니다!
python manage.py runserver 0.0.0.0:8000
pause
