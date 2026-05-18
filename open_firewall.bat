@echo off
title AquaSol Inbound Firewall Rule Opener
echo ====================================================
echo  AquaSol Inbound Firewall Port 8000 Opener
echo ====================================================
echo.
echo Requesting administrator privileges to open Port 8000...
echo (Please click YES on the Windows confirmation pop-up)
echo.
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command New-NetFirewallRule -DisplayName \"\"\"AquaSol API Port 8000\"\"\" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000' -Verb RunAs"
echo.
echo Inbound TCP Port 8000 rule added successfully!
echo Your ESP32 can now connect directly to http://10.22.57.176:8000
echo.
pause
