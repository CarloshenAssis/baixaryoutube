@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
    echo Criando ambiente virtual Python...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -q -r requirements.txt

echo Iniciando servidor local...
start "" http://127.0.0.1:5000
python app.py

pause
