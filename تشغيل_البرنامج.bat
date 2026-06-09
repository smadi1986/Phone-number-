@echo off
chcp 65001 >nul
echo جارٍ تشغيل دليل الهاتف...
pip install customtkinter pillow --quiet
python app.py
pause
