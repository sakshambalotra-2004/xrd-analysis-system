Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\xrd-analysis-system\frontend && npm run dev", 0
Set WshShell = Nothing