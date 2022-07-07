@echo off
cd %cd% && python -m venv venv && %cd%\venv\Scripts\python -m pip install --upgrade pip && %cd%\venv\Scripts\pip install -U -r requirements.txt