@echo off
echo ==================================================
echo ?? Starting EukExpress API
echo ?? Docs: http://localhost:8000/docs
echo ==================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level error 2>nul
