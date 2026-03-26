@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo A criar ambiente virtual...
    py -3.12 -m venv venv
    call venv\Scripts\activate.bat
    echo A instalar dependencias...
    pip install -r requirements.txt
    pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
) else (
    call venv\Scripts\activate.bat
)

python app.py
