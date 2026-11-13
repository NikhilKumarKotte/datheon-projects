@echo off
title Push to GitHub - Datheon Projects
cd /d "f:\New folder\github projects\datheon projects"
echo ======================================================================
echo Pushing Datheon Projects Monorepo to GitHub...
echo Target: https://github.com/NikhilKumarKotte/datheon-projects.git
echo ======================================================================
echo.
git push -u origin main
echo.
echo ======================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your repository has been pushed to GitHub successfully!
    echo Visit: https://github.com/NikhilKumarKotte/datheon-projects
) else (
    echo [ERROR] Push failed. If prompted, please complete the browser login.
)
echo ======================================================================
echo.
pause
