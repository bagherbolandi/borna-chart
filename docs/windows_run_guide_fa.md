# راهنمای اجرای Borna روی Windows Server با BAT

## پیش‌نیازها
- Windows Server یا Windows Desktop
- Python 3.11 یا جدیدتر
- دسترسی به Command Prompt
- دسترسی به اینترنت برای نصب وابستگی‌های Python

## فایل‌های اصلی برای کاربر نهایی
در ریشه پروژه/بسته این فایل‌ها را خواهید داشت:
- `OPEN_ME_FIRST.bat`
- `COPY_PACKAGE_TO_LOCAL_AND_RUN.bat`
- `RUN_ON_SERVER_IP.bat`
- `RESET_AND_RUN_DEMO.bat`
- `ENABLE_WINDOWS_FIREWALL_8000.bat`
- `OPEN_IIS_DEPLOY_GUIDE.bat`
- `INSTALL_PYTHON_FIRST.bat`
- `setup_windows_env.bat`
- `run_borna_server.bat`

## سناریوی 1 — ساده‌ترین اجرای محلی
اگر فقط می‌خواهید سیستم روی همان سرور بالا بیاید و در همان ماشین ببینید:

```bat
OPEN_ME_FIRST.bat
```

این فایل:
1. محیط Python را آماده می‌کند
2. وابستگی‌ها را نصب می‌کند
3. `.env` را از روی `.env.example` می‌سازد اگر لازم باشد
4. API را روی پورت `8000` اجرا می‌کند
5. مرورگر را روی `http://localhost:8000/console` باز می‌کند

### نکته مهم برای Network Share / درایو مپ‌شده
اگر فایل‌ها را از مسیر شبکه مثل `\\SERVER\share\...` یا درایو مپ‌شده مثل `Y:` اجرا می‌کنید، ساخت `.venv` ممکن است fail شود.

در این حالت از این فایل استفاده کنید:

```bat
COPY_PACKAGE_TO_LOCAL_AND_RUN.bat
```

این فایل کل بسته را به مسیر local زیر کپی می‌کند و از آنجا اجرا می‌کند:
- `%LOCALAPPDATA%\\BornaRuntime\\borna-chart-windows-selfcontained-iis-kit-20260922`

## سناریوی 2 — دسترسی از سیستم‌های دیگر شبکه
اگر می‌خواهید کاربران در شبکه با IP سرور باز کنند:

```bat
ENABLE_WINDOWS_FIREWALL_8000.bat
RUN_ON_SERVER_IP.bat
```

این حالت علاوه بر اجرای محلی، آدرس‌های LAN را هم در پنجره CMD نمایش می‌دهد. مثال:
- `http://SERVER-IP:8000/console`
- `http://SERVER-IP:8000/docs`

> فایل Firewall باید با دسترسی Administrator اجرا شود.

## سناریوی 3 — دمو تمیز از صفر
```bat
RESET_AND_RUN_DEMO.bat
```

این فایل قبل از اجرا، `borna_chart.db` را حذف می‌کند تا نسخه دمو از صفر بالا بیاید.

## اگر Python هنوز نصب نیست
ابتدا این فایل را اجرا کنید:

```bat
INSTALL_PYTHON_FIRST.bat
```

بعد از نصب Python 3.11 یا 3.12، دوباره `OPEN_ME_FIRST.bat` یا `RUN_ON_SERVER_IP.bat` را اجرا کنید.

## سناریوی 4 — IIS / Reverse Proxy
اگر می‌خواهید استقرار رسمی‌تر روی IIS داشته باشید:

```bat
OPEN_IIS_DEPLOY_GUIDE.bat
```

یا مستقیماً فایل زیر را باز کنید:
- `docs/windows_server_deploy_iis_fa.md`

## اگر فقط بخواهید محیط آماده شود
```bat
setup_windows_env.bat
```

بعد از آن می‌توانید مستقیم این را بزنید:

```bat
run_borna_server.bat
```

یا برای حالت LAN:

```bat
run_borna_server.bat --lan
```

## آدرس‌های مهم بعد از اجرا
- Console: `http://localhost:8000/`
- Console explicit: `http://localhost:8000/console`
- Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## کاربران دمو
در این نسخه دمو، برای کاربران seed شده:
- `password = username`

مثال‌ها:
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

## اگر پورت دیگری لازم بود
قبل از اجرای BAT می‌توانید این متغیرها را ست کنید:

```bat
set BORNA_PORT=8010
set BORNA_HOST=0.0.0.0
RUN_ON_SERVER_IP.bat
```

## نکته درباره نمایش نتیجه در Console
بعضی عملیات‌ها خروجی JSON را در بخش **Response viewer** پایین صفحه نشان می‌دهند. اگر چیزی ندیدید:
1. کمی پایین‌تر اسکرول کنید
2. یا همان endpoint را در Swagger (`/docs`) تست کنید

## مسیر مستقیم بدون BAT
اگر بخواهید دستی اجرا کنید:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
