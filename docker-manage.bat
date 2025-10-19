@echo off
REM Simple Docker management script for LLM Enrichment Pipeline

if "%1"=="" goto help
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="logs" goto logs
if "%1"=="setup" goto setup
if "%1"=="clean" goto clean
goto help

:start
echo Starting LLM Enrichment Pipeline...
docker-compose up --build
goto end

:stop
echo Stopping services...
docker-compose down
goto end

:logs
echo Showing logs...
docker-compose logs -f
goto end

:setup
echo Setting up ollama model...
docker-compose up -d ollama
timeout /t 10 /nobreak >nul
docker-compose exec ollama ollama pull llama3
echo Setup complete!
goto end

:clean
echo Cleaning up containers...
docker-compose down -v
goto end

:help
echo LLM Enrichment Pipeline - Docker Management
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   start    Build and start all services
echo   stop     Stop all services  
echo   logs     Show logs
echo   setup    Download llama3 model
echo   clean    Remove containers and volumes
echo   help     Show this help
echo.

:end