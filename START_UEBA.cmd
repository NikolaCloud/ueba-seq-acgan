@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Локальное окружение не найдено. Сначала выполните команды установки из README.md.
  pause
  exit /b 1
)

set "PYTHONPATH=src"
echo Запуск UEBA-платформы...
echo Для остановки нажмите Ctrl+C или закройте это окно.
".venv\Scripts\python.exe" -m ueba_seq_acgan serve --open-browser
