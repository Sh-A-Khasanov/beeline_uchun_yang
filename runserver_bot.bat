@echo off
cd /d "D:\all_code\Beeline_GOLD_Nomer_new\"

rem --- UTF-8 kodlash ---
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

rem --- virtual environment yo'li ---
set VIRTUAL_ENV=D:\all_code\Beeline_GOLD_Nomer_new\.venv

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(env) %PROMPT%

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
set VIRTUAL_ENV_PROMPT=(env) 

rem --- 5 ta faylni parallel ishga tushirish ---
start "" cmd /k "py num_category\Oddiy.py"
start "" cmd /k "py num_category\Bronze.py"
start "" cmd /k "py num_category\Silver.py"
start "" cmd /k "py num_category\Gold.py"
start "" cmd /k "py num_category\Platinum.py"
start "" cmd /k "py num_category\Platinum10.py"
start "" cmd /k "py num_category\Platinum20.py"
start "" cmd /k "py num_category\Platinum30.py"


:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)
