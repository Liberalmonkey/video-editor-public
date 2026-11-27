' cat-cut (Video Studyo): terminal penceresi gostermeden studio.bat calistirir.
' Cikti %TEMP%\vedit-studio-log.txt dosyasina yazilir; pencere kapaninca sunucu da kapanir.
Set sh = CreateObject("WScript.Shell")
d = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Environment("Process")("VEDIT_GIZLI") = "1"
logf = sh.ExpandEnvironmentStrings("%TEMP%") & "\vedit-studio-log.txt"
sh.Run "cmd /c """"" & d & "\studio.bat"" > """ & logf & """ 2>&1""", 0, False
