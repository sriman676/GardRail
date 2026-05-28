@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo GuardRail Profile Junction Setup Utility
echo ====================================================
echo.

:: Check for administrative privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Requesting Administrator privileges for creating directory junction...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo [1/3] Administrative privileges confirmed.
echo.
echo IMPORTANT: Please close all active IDE windows, terminal windows, and agent 
echo processes before proceeding so that files in C:\Users\srima\.gemini are not locked.
echo.
pause

set "SOURCE_DIR=C:\Users\srima\.gemini"
set "TARGET_DIR=D:\.gemini"
set "BACKUP_DIR=C:\Users\srima\.gemini.old"

:: Verify target directory exists
if not exist "%TARGET_DIR%" (
    echo [ERROR] Target directory %TARGET_DIR% does not exist!
    echo Please make sure the migration to D:\.gemini is complete.
    pause
    exit /b
)

:: If source directory is already a junction, we are done
fsutil reparsepoint query "%SOURCE_DIR%" >nul 2>&1
if %errorLevel% == 0 (
    echo [SUCCESS] %SOURCE_DIR% is already a junction/reparse point. No action needed!
    goto cleanup
)

:: If backup directory already exists, rename it with a timestamp to avoid conflicts
if exist "%BACKUP_DIR%" (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "dt=%%I"
    set "timestamp=!dt:~0,14!"
    set "BACKUP_DIR=C:\Users\srima\.gemini.old.!timestamp!"
)

echo [2/3] Renaming source directory to !BACKUP_DIR!...
ren "%SOURCE_DIR%" "!BACKUP_DIR:~15!"
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Failed to rename %SOURCE_DIR%. 
    echo Files are likely locked by an active process (such as VS Code or Antigravity).
    echo Please close them and try again.
    echo.
    pause
    exit /b
)

echo [3/3] Creating directory junction from %SOURCE_DIR% to %TARGET_DIR%...
mklink /J "%SOURCE_DIR%" "%TARGET_DIR%"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to create junction link. Reverting rename...
    ren "!BACKUP_DIR!" ".gemini"
    pause
    exit /b
)

echo.
echo ====================================================
echo [SUCCESS] Junction created successfully!
echo C:\Users\srima\.gemini now maps directly to D:\.gemini
echo All agent configuration and browser profile files are active.
echo ====================================================
echo.
pause

:cleanup
echo Cleaning up setup utility...
:: Self-deletes the script upon exit
(goto) 2>nul & del "%~f0"
