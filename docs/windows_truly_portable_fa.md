# راهنمای نسخه Portable واقعی Borna برای Windows

## هدف
این بسته برای حالتی است که بخواهید:
- بدون تکیه به Python نصب‌شده روی سرور کار کنید
- از network share یا mapped drive هم فایل را بردارید ولی اجرا روی local runtime انجام شود
- وابستگی‌های Python به‌صورت offline داخل خود بسته باشند

## این نسخه چه تفاوتی دارد؟
این نسخه:
- از Python embeddable 3.12 استفاده می‌کند
- wheelhouse وابستگی‌های runtime را داخل خودش دارد
- موقع اجرا خودش را به مسیر local کاربر کپی می‌کند
- سپس runtime محلی را می‌سازد و برنامه را بالا می‌آورد

## Assumption
- `Assumption`: PowerShell روی Windows Server فعال است
- `Assumption`: معماری سیستم `win_amd64` است
- `Assumption`: برای اولین اجرا، فایل‌های بسته کامل extract شده‌اند

## فایل‌های اصلی
- `PORTABLE_OPEN_ME_FIRST.bat`
- `PORTABLE_RUN_ON_SERVER_IP.bat`
- `PORTABLE_RESET_AND_RUN_DEMO.bat`
- `ENABLE_WINDOWS_FIREWALL_8000.bat`
- `OPEN_IIS_DEPLOY_GUIDE.bat`

## اجرای ساده
```bat
PORTABLE_OPEN_ME_FIRST.bat
```

### اگر مرحله کپی اولیه fail شد
این نسخه ابتدا بسته را به مسیر local کوتاه‌تری کپی می‌کند:
- `%LOCALAPPDATA%\\BornaP24`

اگر به هر دلیل robocopy در این مرحله fail شد، در همان پوشه extracted این دو دستور را مستقیم در CMD اجرا کنید:

```bat
set BORNA_PORTABLE_LOCAL=1
powershell -NoProfile -ExecutionPolicy Bypass -File portable\bootstrap_portable_runtime.ps1
```

## اجرا روی IP سرور / LAN
```bat
ENABLE_WINDOWS_FIREWALL_8000.bat
PORTABLE_RUN_ON_SERVER_IP.bat
```

## اجرای دمو تمیز از صفر
```bat
PORTABLE_RESET_AND_RUN_DEMO.bat
```

## مسیر local runtime
این نسخه خودش را به این مسیر کپی می‌کند:
- `%LOCALAPPDATA%\BornaPortable\borna-chart-windows-truly-portable-20260922`

و runtime را در اینجا می‌سازد:
- `%LOCALAPPDATA%\BornaPortable\borna-chart-windows-truly-portable-20260922\.portable_runtime`

## آدرس‌ها بعد از اجرا
- `http://localhost:8000/console`
- `http://localhost:8000/docs`

و در حالت LAN:
- `http://SERVER-IP:8000/console`

## اگر آنتی‌ویروس یا Endpoint Security باز شدن خودکار مرورگر را block کرد
بعضی محیط‌های سازمانی ممکن است اجرای خودکار `msedge.exe` یا مرورگر را از داخل PowerShell block کنند. در این حالت:
- server همچنان می‌تواند بالا بیاید
- فقط browser auto-open fail می‌شود

در این وضعیت آدرس را دستی در مرورگر باز کنید:
- `http://localhost:8000/console`

## کاربران دمو
- `master.admin / master.admin`
- `security.1 / security.1`
- `ali / ali`
- `manager.1 / manager.1`
- `buyer.1 / buyer.1`
- `tech.1 / tech.1`
- `finance.1 / finance.1`
- `warehouse.1 / warehouse.1`
- `qc.1 / qc.1`
- `ap.1 / ap.1`
- `treasury.1 / treasury.1`
- `pricing.1 / pricing.1`
- `sales.1 / sales.1`
- `sales.mgr / sales.mgr`

## نکته مهم
اگر قبلاً از نسخه non-portable استفاده کرده‌اید و مشکل `.venv` روی network share داشتید، این نسخه برای دور زدن همان مشکل طراحی شده است.
