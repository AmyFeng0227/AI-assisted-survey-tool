@echo off
echo Running evaluation with default parameters...
echo.

REM Default parameters
set N_SENTENCES=10
set N_OVERLAP=2

REM Check if custom parameters were provided
if not "%1"=="" set N_SENTENCES=%1
if not "%2"=="" set N_OVERLAP=%2

echo Parameters:
echo   - n_sentences: %N_SENTENCES%
echo   - n_overlap: %N_OVERLAP%
echo.

python run_evaluation.py %N_SENTENCES% %N_OVERLAP%

echo.
echo Evaluation complete!
pause 