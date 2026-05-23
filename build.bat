@echo off
pip install pyinstaller >nul 2>&1
pyinstaller nowplay.spec --clean --noconfirm
echo.
echo Done. dist\NowPlaying\NowPlaying.exe
pause
