@echo off
REM ── Wait for Ollama to be ready ──
echo Waiting for Ollama to start...
:WAIT_LOOP
timeout /t 3 /nobreak >nul
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 goto WAIT_LOOP
echo Ollama is ready!

REM ── Start ngrok tunnel to Ollama ──
echo Starting ngrok tunnel to Ollama on port 11434...
ngrok http 11434
