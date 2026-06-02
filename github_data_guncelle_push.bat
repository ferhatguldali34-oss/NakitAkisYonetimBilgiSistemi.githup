@echo off
chcp 65001 > nul
setlocal

set "REPO=C:\Users\ferha\Documents\GitHub\NakitAkisYonetimBilgiSistemi.githup"
set "INPUT=ham_data.json"
set "OUTPUT=data.json"
set "UPDATER=data_updater.py"

echo ================================
echo NAKIT AKIS DATA GUNCELLEME
echo ================================
echo Repo: %REPO%

if not exist "%REPO%" (
  echo HATA: GitHub klasoru bulunamadi.
  pause
  exit /b 1
)

cd /d "%REPO%"

if not exist "%UPDATER%" (
  echo HATA: data_updater.py bu klasorde yok.
  pause
  exit /b 1
)

if not exist "%INPUT%" (
  echo HATA: ham_data.json bulunamadi. Excel makrosu once bunu uretmeli.
  pause
  exit /b 1
)

echo [1/4] data_updater calisiyor...
python "%UPDATER%" --input "%INPUT%" --output "%OUTPUT%"
if errorlevel 1 (
  echo HATA: data_updater calismadi.
  pause
  exit /b 1
)

echo [2/4] Git add...
git add "%OUTPUT%" "%INPUT%"

echo [3/4] Git commit...
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "data guncellendi %date% %time%"
) else (
  echo Degisiklik yok, commit atlandi.
)

echo [4/4] Git push...
git push
if errorlevel 1 (
  echo HATA: git push basarisiz.
  pause
  exit /b 1
)

echo TAMAM: data.json GitHub'a gonderildi.
pause
