@echo off
echo Running Backend Tests...
go test ./...
if %errorlevel% neq 0 (
    echo [ERROR] Backend tests failed!
    exit /b %errorlevel%
)
echo [SUCCESS] All tests passed!
