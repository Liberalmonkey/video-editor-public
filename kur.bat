@echo off
setlocal
rem AI Video Editor: sifirdan kurulum (Windows). Tekrar calistirmak guvenli; kurulu adimlari atlar.
cd /d "%~dp0"
set OM_COMMIT=c8066452325cb57c8fc1ba8c2a71b6e8842e6b65
set HATA=0

echo [1/8] Gerekli programlar denetleniyor
call :gerekli python "winget install -e --id Python.Python.3.12"
call :gerekli node "winget install -e --id OpenJS.NodeJS.LTS"
call :gerekli git "winget install -e --id Git.Git"
call :gerekli ffmpeg "winget install -e --id Gyan.FFmpeg"
if %HATA%==1 (
  echo.
  echo Eksik programlari yukaridaki komutlarla kur, yeni bir terminal ac ve kur.bat'i tekrar calistir.
  goto son
)
python -c "import sys; sys.exit(sys.version_info < (3, 11))"
if errorlevel 1 (
  echo Python 3.11 ya da ustu gerekli. Kur: winget install -e --id Python.Python.3.12
  goto son
)

echo [2/8] Python ortami (.venv)
if not exist ".venv\Scripts\python.exe" python -m venv .venv || goto hata
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -q -e ".[studio,boards,dev]" || goto hata

echo [3/8] OpenMontage (AGPL-3.0, sabit surum + patches\openmontage.patch)
if not exist "openmontage\.git" (
  git clone -q https://github.com/calesthio/OpenMontage.git openmontage || goto hata
  git -C openmontage checkout -q %OM_COMMIT% || goto hata
  git -C openmontage apply --binary --whitespace=nowarn ..\patches\openmontage.patch || goto hata
) else (
  echo     openmontage zaten var, dokunulmadi.
)

echo [4/8] OpenMontage Python ortami
if not exist "openmontage\.venv\Scripts\python.exe" python -m venv openmontage\.venv || goto hata
"openmontage\.venv\Scripts\python.exe" -m pip install -q -r openmontage\requirements.txt || goto hata

echo [5/8] Reels motoru (Remotion)
pushd openmontage\remotion-composer
call npm install --no-audit --no-fund --loglevel=error || (popd & goto hata)
popd

echo [6/8] cat-cut arayuzu
pushd studio
call npm install --no-audit --no-fund --loglevel=error || (popd & goto hata)
call npm run build || (popd & goto hata)
popd

echo [7/8] HyperFrames ve CC0 ses efektleri (internet gerekir; hata olursa kurulum surer)
call npm install --no-audit --no-fund --loglevel=error
call node_modules\.bin\hyperframes browser ensure >nul
".venv\Scripts\vedit.exe" sfx fetch kenney >nul
".venv\Scripts\vedit.exe" sfx fetch remotion >nul
".venv\Scripts\vedit.exe" sfx synth >nul
".venv\Scripts\vedit.exe" sfx index

echo [8/8] Masaustu kisayolu
rem KUR_KISAYOL_YOK: test kurulumlari gercek kisayolu ezmesin
if not defined KUR_KISAYOL_YOK powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\cat-cut.lnk'); $s.TargetPath=$env:WINDIR+'\System32\wscript.exe'; $s.Arguments='\"%~dp0studio.vbs\"'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0studio\cat-cut.ico,0'; $s.Save()"

echo.
echo Kurulum tamam. cat-cut: masaustundeki kisayol ya da studio.vbs. Terminal hatti: bu klasorde "claude".
goto son

:gerekli
where %1 >nul 2>nul
if errorlevel 1 (
  echo     EKSIK: %1  ^>  %~2
  set HATA=1
) else (
  echo     tamam: %1
)
exit /b 0

:hata
echo.
echo Kurulum bir adimda durdu. Yukaridaki hatayi oku; duzeltip kur.bat'i tekrar calistir.

:son
if not defined KUR_SESSIZ pause
endlocal
