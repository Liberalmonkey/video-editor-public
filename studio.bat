@echo off
rem Video Studyo: yerel kurgu uygulamasi (ADR 0021, hizli acilis ADR 0050)
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
if not exist ".venv\Scripts\python.exe" (
  echo .venv yok: once kur.bat calistir.
  goto hata
)
rem Tek surec: hazirlik denetimi + pencere + sunucu. Cikis 11 = Python bagimliligi eksik, 12 = arayuz derlenmeli
".venv\Scripts\python.exe" -m vedit.studio.baslat %*
set "KOD=%errorlevel%"
if "%KOD%"=="0" exit /b 0
if "%KOD%"=="11" goto kur
if "%KOD%"=="12" goto derle
echo Studyo beklenmedik sekilde kapandi (kod %KOD%).
goto hata

:kur
".venv\Scripts\python.exe" -m pip install -q -e ".[studio]"
if errorlevel 1 (
  echo Python bagimliliklari kurulamadi.
  goto hata
)
".venv\Scripts\python.exe" -m vedit.studio.baslat --denetle
set "KOD=%errorlevel%"
if "%KOD%"=="0" goto calistir
if "%KOD%"=="2" goto derle
echo Kurulumdan sonra da hazir degil (kod %KOD%).
goto hata

:derle
pushd studio
if not exist "node_modules" call npm install --no-audit --no-fund
call npm run build
if errorlevel 1 (
  popd
  echo Arayuz derlenemedi.
  goto hata
)
popd

:calistir
".venv\Scripts\python.exe" -m vedit.studio.baslat %*
if errorlevel 1 goto hata
exit /b 0

:hata
rem studio.vbs gizli calistirir: pause gorunmez, hatayi log ile goster
if defined VEDIT_GIZLI (start "" notepad "%TEMP%\vedit-studio-log.txt") else pause
exit /b 1
