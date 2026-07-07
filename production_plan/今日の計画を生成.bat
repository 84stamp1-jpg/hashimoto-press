@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ============================================
echo 橋本工業 生産計画 自動生成
echo %date% %time%
echo ============================================
where python >nul 2>&1
if errorlevel 1 ( echo [ERROR] Python が見つかりません & pause & exit /b 1 )
python generate_plan.py --slack
if errorlevel 1 ( echo [ERROR] 生成に失敗しました & pause & exit /b 1 )
echo ============================================
echo 完了しました。output フォルダを確認してください。
echo ============================================
timeout /t 3
