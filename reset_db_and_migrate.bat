@echo off
:: ==============================================
:: 비대면 중고거래 플랫폼 DB 초기화 & 재마이그레이션
:: ==============================================

:: 1️⃣ 현재 경로 표시
echo.
echo 🚀 Django DB 초기화 및 마이그레이션을 시작합니다.
echo 현재 경로: %cd%
echo.

:: 2️⃣ 가상환경 활성화
if exist ".venv\Scripts\activate" (
    call .venv\Scripts\activate
    echo ✅ 가상환경 활성화 완료
) else (
    echo ⚠️ .venv 폴더가 없습니다. 수동으로 가상환경을 만들어주세요.
    pause
    exit /b
)

:: 3️⃣ 기존 DB 삭제
@REM if exist "db.sqlite3" (
@REM     del /f /q db.sqlite3
@REM     echo 🗑️ 기존 db.sqlite3 파일 삭제 완료
@REM ) else (
@REM     echo (DB 파일이 없습니다 — 새로 생성합니다.)
@REM )

:: 4️⃣ 마이그레이션 폴더 내 기존 파일 제거
@REM for %%a in (chat listings users orders verification) do (
@REM     if exist %%a\migrations (
@REM         del /q %%a\migrations\0*.py 2>nul
@REM         del /q %%a\migrations\*.pyc 2>nul
@REM         echo 🧹 %%a\migrations 초기화 완료
@REM     )
@REM )

:: 5️⃣ 마이그레이션 생성 및 적용
echo.
echo 🔄 makemigrations 실행 중...
python manage.py makemigrations

echo.
echo 🧱 migrate 실행 중...
python manage.py migrate

:: 6️⃣ superuser 생성 안내
echo.
echo 👤 superuser 생성을 시작합니다.
echo 관리자 계정을 직접 입력해주세요.
python manage.py createsuperuser

echo.
echo ✅ 모든 작업이 완료되었습니다!
echo 서버 실행: python manage.py runserver 0.0.0.0:8000
pause
