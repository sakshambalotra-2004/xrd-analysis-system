Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\xrd-analysis-system\backend && python -m uvicorn app:app --reload", 0
Set WshShell = Nothing