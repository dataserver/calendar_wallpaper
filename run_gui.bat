@echo off
:: Get the directory of this batch file
set SCRIPT_DIR=%~dp0

:: Set the path to the virtual environment's Scripts folder (Windows specific)
set VENV_PATH=%SCRIPT_DIR%.venv\Scripts
set PROJECT_PATH=%SCRIPT_DIR%

:: Check if paths are correct
echo VENV_PATH: %VENV_PATH%
echo PROJECT_PATH: %PROJECT_PATH%

:: Change to the project root directory before running anything
cd /d %PROJECT_PATH%
if %ERRORLEVEL% neq 0 (
    echo Failed to change directory to the project directory. Exiting.
    pause
    exit /b
)

:: Debug: Check if we're in the right directory
echo Current directory: %CD%

:: Activate the virtual environment
echo Activating virtual environment...
call %VENV_PATH%\activate.bat
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment. Exiting.
    pause
    exit /b
)


:: Ensure the virtual environment is activated and print the Python version
echo Virtual environment activated.
python --version
if %ERRORLEVEL% neq 0 (
    echo Python version check failed. Exiting.
    pause
    exit /b
)


:: Run the GUI script
echo Running GUI script...
python -m gui.gui

if %ERRORLEVEL% neq 0 (
    echo GUI script execution failed. Exiting.
    pause
    exit /b
)

:: Deactivate the virtual environment after running the scripts
echo Deactivating virtual environment...
call %VENV_PATH%\deactivate.bat

:: End the script
echo Script execution completed. Press any key to close.
:: uncomment if you want to keep the window open untill a key is pressed
:: pause

:: Uncomment if you want keep the window oepn after execution
:: cmd /K echo This command window will stay open.

