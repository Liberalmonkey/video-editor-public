# HyperFrames haftalık güncelleme görevi (ADR 0051). Kullanıcı bir kez çalıştırır; Görev Zamanlayıcı'ya kaydeder.
# Görev her cuma 13:00'te `vedit hf-guncelle --bekle 240` koşar: aday sürüm duman testinden geçerse sabitlenir.
# Çalışan edit/render varsa sabitlemeden önce en çok 4 saat bekler (2026-11-23: güncelleme render'ı düşürmüştü).
# Kaldırmak için: Unregister-ScheduledTask -TaskName "vedit-hf-guncelle" -Confirm:$false
$kok = Split-Path -Parent $PSScriptRoot
$vedit = Join-Path $kok ".venv\Scripts\vedit.exe"
$log = Join-Path $kok "work\hf-aday\gorev.log"
$eylem = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"`"$vedit`" hf-guncelle --bekle 240 >> `"$log`" 2>&1`"" -WorkingDirectory $kok
$tetik = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 13:00
$ayar = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 6)
Register-ScheduledTask -TaskName "vedit-hf-guncelle" -Action $eylem -Trigger $tetik -Settings $ayar -Description "HyperFrames güncellemesi: aday + duman testi (ADR 0051)" -Force
Write-Host "Kaydedildi: vedit-hf-guncelle (her cuma 13:00). Günlük: $log"
