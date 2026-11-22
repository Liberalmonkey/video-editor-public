# HyperFrames haftalık güncelleme görevi (ADR 0051). Kullanıcı bir kez çalıştırır; Görev Zamanlayıcı'ya kaydeder.
# Görev her pazartesi 10:00'da `vedit hf-guncelle` koşar: aday sürüm duman testinden geçerse sabitlenir.
# Kaldırmak için: Unregister-ScheduledTask -TaskName "vedit-hf-guncelle" -Confirm:$false
$kok = Split-Path -Parent $PSScriptRoot
$vedit = Join-Path $kok ".venv\Scripts\vedit.exe"
$log = Join-Path $kok "work\hf-aday\gorev.log"
$eylem = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"`"$vedit`" hf-guncelle >> `"$log`" 2>&1`"" -WorkingDirectory $kok
$tetik = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00
$ayar = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "vedit-hf-guncelle" -Action $eylem -Trigger $tetik -Settings $ayar -Description "HyperFrames güncellemesi: aday + duman testi (ADR 0051)" -Force
Write-Host "Kaydedildi: vedit-hf-guncelle (her pazartesi 10:00). Günlük: $log"
