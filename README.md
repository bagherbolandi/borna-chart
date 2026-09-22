# borna-chart

## Deliverables
- `docs/enterprise_system_design_fa.md` — طرح جامع سامانه مدیریت فرآیندهای عملیاتی و کنترلی سازمان
- `docs/database_schema.sql` — اسکیما منطقی پایگاه داده برای نسخه Server
- `docs/erd_mermaid.md` — ERD و Traceability Diagram به‌صورت Mermaid
- `docs/mvp_implementation_plan_fa.md` — برنامه اجرایی گام‌های بعدی
- `docs/server_mvp_fa.md` — مستند MVP نسخه Server با Python + FastAPI + PostgreSQL
- `docs/security_architecture_fa.md` — معماری امنیتی عملیاتی و الزامات استقرار امن MVP
- `deploy/nginx/borna-api.conf.example` — نمونه Reverse Proxy Hardened Config برای استقرار امن
- `config/` — پیکربندی اولیه Workflow، Rule، SLA، DOA و SoD
- `prototype/Borna_Process_Control_Prototype.xlsx` — Prototype اولیه اکسل
- `prototype/csv/` — قالب CSV شیت‌های اکسل
- `scripts/build_excel_prototype.py` — اسکریپت بازتولید Prototype اکسل و فایل‌های پیکربندی
- `app/` — اسکلت اولیه API و Service Layer نسخه Server
- `requirements.txt` / `pyproject.toml` — وابستگی‌ها و تنظیمات Python
- `Dockerfile` / `docker-compose.yml` — اجرای کانتینری برای API و PostgreSQL

## Quick Start

### Local
```bash
cp .env.example .env
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows BAT
ساده‌ترین حالت:
```bat
OPEN_ME_FIRST.bat
```

اگر بسته را روی Network Share یا درایو مپ‌شده اجرا می‌کنید، بهتر است اول این را بزنید:
```bat
COPY_PACKAGE_TO_LOCAL_AND_RUN.bat
```

برای اجرا روی IP سرور/LAN:
```bat
ENABLE_WINDOWS_FIREWALL_8000.bat
RUN_ON_SERVER_IP.bat
```

برای اجرای دمو تمیز از صفر:
```bat
RESET_AND_RUN_DEMO.bat
```

اگر Python روی سرور نصب نیست:
```bat
INSTALL_PYTHON_FIRST.bat
```

برای راهنمای IIS / Reverse Proxy:
```bat
OPEN_IIS_DEPLOY_GUIDE.bat
```

حالت‌های فنی‌تر هم همچنان موجودند:
```bat
setup_windows_env.bat
run_borna_server.bat
run_borna_server.bat --lan
```

جزئیات بیشتر در `docs/windows_run_guide_fa.md` و `docs/windows_server_deploy_iis_fa.md` آمده است.

### Windows Truly Portable
اگر نسخه‌ای می‌خواهید که به Python نصب‌شده روی سرور وابسته نباشد، از بسته portable استفاده کنید. این بسته:
- embedded Python 3.12 را داخل خود دارد
- wheelhouse وابستگی‌های runtime را داخل خود دارد
- روی اجرای مستقیم از network share تکیه نمی‌کند و خودش به local runtime کپی می‌شود

فایل‌های اصلی نسخه portable:
```bat
PORTABLE_OPEN_ME_FIRST.bat
PORTABLE_RUN_ON_SERVER_IP.bat
PORTABLE_RESET_AND_RUN_DEMO.bat
```

اگر مرحله copy اولیه fail شد، می‌توانید مستقیم این را در CMD اجرا کنید:
```bat
set BORNA_PORTABLE_LOCAL=1
powershell -NoProfile -ExecutionPolicy Bypass -File portable\bootstrap_portable_runtime.ps1
```

اگر Endpoint Security باز شدن خودکار مرورگر را block کرد، این را اجرا کنید و آدرس را دستی باز کنید:
```bat
set BORNA_PORTABLE_LOCAL=1
powershell -NoProfile -ExecutionPolicy Bypass -File portable\bootstrap_portable_runtime.ps1 -NoBrowser
```

جزئیات بیشتر در `docs/windows_truly_portable_fa.md` آمده است.

### Docker
```bash
docker compose up --build
```

### Live review console
- `/`
- `/console`

این صفحه یک Web Console سبک برای تست تعاملی سناریوهای اصلی فراهم می‌کند، شامل:
- login / logout / role shortcuts
- access control review برای create user / force reset / change password / session revoke
- security incident workflow lab
- procurement workflow runner برای PR create / submit / review / approve
- downstream procurement runner برای RFQ / quotation / commercial eval / technical approve / price approve / PO / GRN / QC / invoice / payment
- sales workflow runner
- traceability / audit helpers
- generic request composer

### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Security baseline
- Passwords are stored hashed, not in plain text.
- Operational endpoints require bearer authentication and role checks.
- Account lockout is applied after repeated failed logins.
- Login endpoint has baseline rate limiting.
- Tokens can be revoked through logout.
- Security monitoring is available via dashboard/API.
- Responses include baseline hardening headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control`.

> Demo users are seeded automatically. For MVP testing, the password is the same as the username.
> Example: `buyer.1 / buyer.1`, `manager.1 / manager.1`, `master.admin / master.admin`, `pricing.1 / pricing.1`, `sales.1 / sales.1`, `sales.mgr / sales.mgr`, `planning.1 / planning.1`, `logistics.1 / logistics.1`, `ar.1 / ar.1`, `collect.1 / collect.1`, `security.1 / security.1`

### Main endpoints
- `GET /api/v1/health`
- `GET /api/v1/config/workflows`
- `GET /api/v1/config/rules`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/inbox/my-tasks`
- `GET /api/v1/inbox/approvals`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/my`
- `POST /api/v1/scheduler/run-sla`
- `GET /api/v1/security/dashboard`
- `GET /api/v1/security/my-sessions`
- `GET /api/v1/security/sessions?username=...`
- `POST /api/v1/security/sessions/{id}/revoke`
- `POST /api/v1/security/tokens/cleanup`
- `POST /api/v1/security/incidents`
- `POST /api/v1/security/incidents/{id}/triage`
- `POST /api/v1/security/incidents/{id}/contain`
- `POST /api/v1/security/incidents/{id}/resolve`
- `POST /api/v1/security/incidents/{id}/close`
- `GET /api/v1/security/incidents`
- `GET /api/v1/security/incidents/{id}`
- `GET /api/v1/audit/events`
- `GET /api/v1/audit/entities/{entity_name}/{entity_id}`
- `POST /api/v1/suppliers`
- `POST /api/v1/customers`
- `GET /api/v1/customers`
- `POST /api/v1/products`
- `GET /api/v1/products`
- `POST /api/v1/pricing`
- `POST /api/v1/pricing/{id}/approve`
- `GET /api/v1/pricing`
- `POST /api/v1/sales-orders`
- `POST /api/v1/sales-orders/{id}/confirm`
- `POST /api/v1/sales-orders/{id}/review-profitability`
- `POST /api/v1/sales-orders/{id}/close`
- `GET /api/v1/sales-orders`
- `POST /api/v1/sales-deliveries`
- `POST /api/v1/sales-deliveries/{id}/release`
- `POST /api/v1/sales-deliveries/{id}/deliver`
- `GET /api/v1/sales-deliveries`
- `GET /api/v1/sales-deliveries/{id}`
- `POST /api/v1/sales-invoices`
- `GET /api/v1/sales-invoices`
- `GET /api/v1/sales-invoices/{id}`
- `POST /api/v1/collections`
- `GET /api/v1/collections`
- `GET /api/v1/collections/{id}`
- `POST /api/v1/purchase-requests`
- `POST /api/v1/purchase-requests/{id}/submit`
- `POST /api/v1/purchase-requests/{id}/route-review`
- `POST /api/v1/purchase-requests/{id}/approve`
- `POST /api/v1/rfqs`
- `POST /api/v1/rfqs/{id}/quotations`
- `POST /api/v1/rfqs/{id}/record-quotes`
- `POST /api/v1/rfqs/{id}/commercial-evaluate`
- `POST /api/v1/rfqs/{id}/technical-approve`
- `POST /api/v1/rfqs/{id}/price-approve`
- `POST /api/v1/purchase-orders`
- `POST /api/v1/goods-receipts`
- `POST /api/v1/quality-inspections`
- `POST /api/v1/quality-inspections/{id}/finalize`
- `POST /api/v1/supplier-invoices`
- `POST /api/v1/supplier-invoices/{id}/match`
- `POST /api/v1/payments`
- `POST /api/v1/payments/{id}/approve`
- `POST /api/v1/payments/{id}/execute`
- `GET /api/v1/approvals/{object_type}/{object_id}`
- `GET /api/v1/traceability/purchase-requests/{id}`
- `GET /api/v1/traceability/sales-orders/{id}`
- `GET /api/v1/traceability/document/{object_type}/{object_id}`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/security`

> For production hardening assumptions and network-security guidance, see `docs/security_architecture_fa.md` and `deploy/nginx/borna-api.conf.example`.
