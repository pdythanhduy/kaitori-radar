@echo off
cd /d "%~dp0\.."
set PYTHONUTF8=1
"C:\Users\thanh\AppData\Local\Programs\Python\Python311\python.exe" marketing\daily_traffic.py > marketing\daily_traffic.log 2>&1
