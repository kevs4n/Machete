@echo off
echo 🔪 Setting up MACHETE Platform...

:: Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)
echo ✅ Docker found

:: Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo    Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)
echo ✅ Docker Compose found

:: Create required directories
echo 📁 Creating required directories...
if not exist "data" mkdir data
if not exist "tools" mkdir tools
if not exist "core\caddy\data" mkdir core\caddy\data
if not exist "core\caddy\config" mkdir core\caddy\config

:: Build and start the platform
echo 🏗️ Building and starting MACHETE platform...
docker-compose build
docker-compose up -d

:: Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

:: Check if services are running
echo 🔍 Checking service health...
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ MACHETE platform is running successfully!
    echo.
    echo 🌐 Access the platform at: http://localhost:8080
    echo 📚 API documentation at: http://localhost:8080/api/health
    echo.
    echo 📊 View running containers:
    docker-compose ps
) else (
    echo ❌ Some services failed to start. Check the logs:
    docker-compose logs
    pause
    exit /b 1
)

echo.
echo 🎉 MACHETE platform setup complete!
echo.
echo Next steps:
echo 1. Open http://localhost:8080 in your browser
echo 2. Use the Tool Registry to install new tools
echo 3. Check the documentation in the docs/ folder
echo.
pause
