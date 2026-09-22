# راهنمای استقرار Borna روی Windows Server با IIS / Reverse Proxy

## هدف
این راهنما برای زمانی است که بخواهید Borna را روی Windows Server اجرا کنید و از طریق:
- `http://SERVER-IP:8000` در LAN
- یا از طریق IIS با دامنه/SSL

به آن دسترسی بدهید.

---

## سناریوهای پیشنهادی استقرار

### سناریو A — سریع‌ترین حالت برای بازبینی داخلی
- اجرای مستقیم Uvicorn روی پورت `8000`
- باز کردن Firewall برای TCP 8000
- دسترسی کاربران LAN از طریق `http://SERVER-IP:8000/console`

**مناسب برای:** تست، بازبینی، UAT داخلی، فاز طراحی

### سناریو B — حالت مناسب‌تر برای سرور سازمانی
- اجرای Uvicorn روی `127.0.0.1:8000`
- IIS به‌عنوان Reverse Proxy
- Bind دامنه و SSL روی IIS
- هدایت ترافیک خارجی به API داخلی

**مناسب برای:** محیط‌های کنترل‌شده سازمانی و انتشار رسمی‌تر

---

## Required Input
- `Required Input`: نام یا IP سرور
- `Required Input`: آیا فقط LAN کافی است یا دامنه عمومی/داخلی نیاز دارید
- `Required Input`: آیا SSL/TLS باید روی IIS terminate شود یا نه
- `Required Input`: آیا سرویس باید بعد از reboot خودکار بالا بیاید یا اجرای دستی کافی است

## Assumption
- `Assumption`: Python 3.11 روی سرور قابل نصب است
- `Assumption`: کاربر ادمین ویندوز برای باز کردن Firewall و تنظیم IIS وجود دارد
- `Assumption`: برای Reverse Proxy، ماژول‌های IIS URL Rewrite و ARR قابل نصب هستند

---

# سناریو A — LAN مستقیم با BAT

## 1) Extract package
بسته نهایی را روی سرور extract کنید.

## 2) باز کردن Firewall
بهتر است این فایل را با دسترسی Administrator اجرا کنید:

```bat
ENABLE_WINDOWS_FIREWALL_8000.bat
```

یا مستقیم:

```bat
deploy\windows\install_firewall_rule_8000.bat 8000
```

## 3) اجرای برنامه روی IP سرور
```bat
RUN_ON_SERVER_IP.bat
```

## 4) آدرس دسترسی
- `http://localhost:8000/console`
- `http://SERVER-IP:8000/console`
- `http://SERVER-IP:8000/docs`

---

# سناریو B — IIS Reverse Proxy

## 1) برنامه را محلی بالا بیاورید
**Configurable Parameter:** اگر فقط IIS قرار است به برنامه وصل شود، ترجیحاً API روی localhost گوش بدهد.

نمونه:
```bat
set BORNA_HOST=127.0.0.1
set BORNA_PORT=8000
run_borna_server.bat --no-browser
```

> اگر خواستید از BAT موجود استفاده کنید ولی روی localhost bind شود، کافی است `BORNA_HOST=127.0.0.1` را قبل از اجرا ست کنید.

## 2) نصب IIS Components
در Server Manager یا Windows Features این موارد را فعال/نصب کنید:
- Web Server (IIS)
- IIS Management Console
- URL Rewrite Module
- Application Request Routing (ARR)

## 3) فعال‌سازی Proxy در ARR
در IIS Manager:
- روی سرور کلیک کنید
- `Application Request Routing Cache`
- `Server Proxy Settings`
- گزینه `Enable proxy` را فعال کنید

## 4) ساخت Website یا استفاده از Default Web Site
می‌توانید یک Site جدید بسازید یا روی سایت موجود تنظیم کنید.

## 5) قراردادن فایل نمونه web.config
فایل نمونه در این مسیر قرار گرفته:
- `deploy/windows/iis/web.config.example`

آن را به ریشه سایت IIS کپی کنید و نامش را بگذارید:
- `web.config`

این فایل درخواست‌ها را به:
- `http://127.0.0.1:8000`

forward می‌کند.

## 6) Bind دامنه و SSL
`Required Input`: دامنه داخلی/خارجی و certificate

در IIS برای Site موردنظر:
- HTTP binding یا HTTPS binding تعریف کنید
- اگر HTTPS استفاده می‌کنید، certificate را attach کنید

## 7) تست
بعد از بالا آمدن سایت:
- `https://YOUR-DOMAIN/console`
- `https://YOUR-DOMAIN/docs`

---

# پیشنهاد برای پایداری بیشتر روی Windows Server

## گزینه 1 — Task Scheduler
برای اجرای خودکار بعد از reboot:
- یک Scheduled Task بسازید
- Trigger: At startup
- Action: اجرای `OPEN_ME_FIRST.bat` یا `RUN_ON_SERVER_IP.bat`

## گزینه 2 — Windows Service Wrapper
`Configurable Parameter`: اگر بخواهید Uvicorn به‌صورت سرویس واقعی بالا بیاید، می‌توان از NSSM یا WinSW استفاده کرد.

در این مرحله هنوز wrapper سرویس داخل بسته قرار داده نشده، چون می‌خواستم بسته ساده و بدون وابستگی اضافه بماند.
اگر خواستید، در گام بعد برایتان نسخه Service-based هم می‌سازم.

---

# توصیه امنیتی اجرایی

## Minimum baseline
- اگر دسترسی فقط داخلی است، ترجیحاً در سطح Firewall فقط subnetهای سازمانی مجاز شوند
- اگر IIS جلوی سیستم است، endpoint اصلی FastAPI بهتر است روی `127.0.0.1` بماند
- اگر دامنه دارید، SSL termination روی IIS انجام شود
- حساب‌های دمو فقط برای طراحی و تست هستند و باید در محیط رسمی حذف/تعویض شوند

## Do not use as-is for production without review
این بسته برای MVP عملیاتی و بازبینی طراحی آماده شده، اما برای production رسمی هنوز این موارد باید نهایی شوند:
- secret management
- backup/recovery policy
- service supervision policy
- TLS certificate lifecycle
- centralized logging / SIEM integration
- DB migration / PostgreSQL hardening

---

# فایل‌های مرتبط
- `OPEN_ME_FIRST.bat`
- `RUN_ON_SERVER_IP.bat`
- `ENABLE_WINDOWS_FIREWALL_8000.bat`
- `deploy/windows/install_firewall_rule_8000.bat`
- `deploy/windows/iis/web.config.example`
- `docs/windows_run_guide_fa.md`
