@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "BIN_DIR=%~dp0bin"
set "PY_URL=https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe"
set "YTDLP_URL=https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

REM --- 1. Verifica se o Python esta instalado ---
where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Baixando e instalando automaticamente...
    curl -L -o "%TEMP%\python-installer.exe" "%PY_URL%"
    if not exist "%TEMP%\python-installer.exe" (
        echo ERRO: nao foi possivel baixar o instalador do Python. Verifique sua conexao com a internet.
        pause
        exit /b 1
    )
    "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0
    del "%TEMP%\python-installer.exe"
    echo.
    echo Python foi instalado com sucesso.
    echo Feche esta janela e execute run.bat novamente para continuar.
    pause
    exit /b 0
)

REM --- 2. Baixa yt-dlp.exe se necessario ---
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

if not exist "%BIN_DIR%\yt-dlp.exe" (
    echo Baixando yt-dlp.exe...
    curl -L -o "%BIN_DIR%\yt-dlp.exe" "%YTDLP_URL%"
    if not exist "%BIN_DIR%\yt-dlp.exe" (
        echo ERRO: nao foi possivel baixar o yt-dlp.exe. Verifique sua conexao com a internet.
        pause
        exit /b 1
    )
)

REM --- 3. Baixa ffmpeg.exe e ffprobe.exe se necessario ---
if not exist "%BIN_DIR%\ffmpeg.exe" (
    echo Baixando ffmpeg ^(pode demorar alguns minutos^)...
    curl -L -o "%TEMP%\ffmpeg.zip" "%FFMPEG_URL%"
    if not exist "%TEMP%\ffmpeg.zip" (
        echo ERRO: nao foi possivel baixar o ffmpeg. Verifique sua conexao com a internet.
        pause
        exit /b 1
    )
    echo Extraindo ffmpeg...
    if exist "%TEMP%\ffmpeg-extract" rmdir /s /q "%TEMP%\ffmpeg-extract"
    powershell -NoProfile -Command "Expand-Archive -Path '%TEMP%\ffmpeg.zip' -DestinationPath '%TEMP%\ffmpeg-extract' -Force"
    for /d %%D in ("%TEMP%\ffmpeg-extract\ffmpeg-*") do (
        copy /y "%%D\bin\ffmpeg.exe" "%BIN_DIR%\ffmpeg.exe" >nul
        copy /y "%%D\bin\ffprobe.exe" "%BIN_DIR%\ffprobe.exe" >nul
    )
    del "%TEMP%\ffmpeg.zip"
    rmdir /s /q "%TEMP%\ffmpeg-extract"
    if not exist "%BIN_DIR%\ffmpeg.exe" (
        echo ERRO: nao foi possivel extrair o ffmpeg.exe.
        pause
        exit /b 1
    )
)

REM --- 4. Cria/ativa o ambiente virtual e instala dependencias ---
if not exist venv (
    echo Criando ambiente virtual Python...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -q -r requirements.txt

echo.
echo Tudo pronto. Iniciando servidor local...

REM Forca abertura em um navegador moderno (Edge ou Chrome), evitando que o
REM Windows use o Internet Explorer como padrao em maquinas mal configuradas.
set "EDGE_EXE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
set "EDGE_EXE_ALT=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
set "CHROME_EXE_ALT=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"

if exist "%EDGE_EXE%" (
    start "" "%EDGE_EXE%" "http://127.0.0.1:5000"
) else if exist "%EDGE_EXE_ALT%" (
    start "" "%EDGE_EXE_ALT%" "http://127.0.0.1:5000"
) else if exist "%CHROME_EXE%" (
    start "" "%CHROME_EXE%" "http://127.0.0.1:5000"
) else if exist "%CHROME_EXE_ALT%" (
    start "" "%CHROME_EXE_ALT%" "http://127.0.0.1:5000"
) else (
    start "" "http://127.0.0.1:5000"
)

python app.py

pause
