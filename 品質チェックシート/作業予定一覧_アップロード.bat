@echo off
chcp 65001 > nul
echo ============================================
echo 作業予定一覧 アップロードツール
echo ============================================
echo.

set SRC1=%USERPROFILE%\OneDrive\Desktop\作業予定一覧.xlsx
set SRC2=%USERPROFILE%\Desktop\作業予定一覧.xlsx
set DST=G:\マイドライブ\品質チェックシート記録\作業予定一覧\作業予定一覧.xlsx
set GAS_URL=https://script.google.com/macros/s/AKfycbw3zssfr-pWlRcgMT4fhQ40HoOUeJHz7-_yYIcA0b4hxh2BXdWAPe96D2kXPizLzsqI/exec

rem --- ソースファイル検索 ---
if exist "%SRC1%" ( set SRC=%SRC1% & goto :found )
if exist "%SRC2%" ( set SRC=%SRC2% & goto :found )
echo [エラー] 作業予定一覧.xlsx が見つかりません
echo 確認パス1: %SRC1%
echo 確認パス2: %SRC2%
pause
exit /b 1

:found
echo コピー元: %SRC%
echo コピー先: %DST%
echo.

rem --- コピー先フォルダ確認 ---
if not exist "G:\マイドライブ\品質チェックシート記録\作業予定一覧" (
    echo [エラー] コピー先フォルダが見つかりません
    echo G:\マイドライブ\品質チェックシート記録\作業予定一覧 を確認してください
    pause
    exit /b 1
)

rem --- xlsxをGoogleドライブにコピー ---
copy /Y "%SRC%" "%DST%"
if not %ERRORLEVEL% == 0 (
    echo [エラー] ファイルコピーに失敗しました
    pause
    exit /b 1
)
echo [完了] Googleドライブにコピーしました
echo.

rem --- GASを呼び出してスプレッドシートを更新 ---
echo スプレッドシートを更新中...
powershell -Command "try { $r = Invoke-WebRequest -Uri '%GAS_URL%?action=updateSakuyo' -UseBasicParsing -TimeoutSec 60; Write-Host '[完了] スプレッドシートを更新しました'; Write-Host $r.Content } catch { Write-Host '[エラー] GAS呼び出し失敗: ' $_.Exception.Message }"

echo.
echo %DATE% %TIME% 処理完了
echo.
pause
