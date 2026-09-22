# معماری امنیتی عملیاتی MVP

## هدف
این سند برای تعریف یک **Security Baseline عملیاتی، سبک، قابل ارتقاء و مناسب MVP** تهیه شده است؛ به‌گونه‌ای که سامانه در عین کاربردی بودن، از منظر امنیت اطلاعات، امنیت شبکه و مقاومت در برابر سوء‌استفاده‌ها، از ابتدا با رویکرد **Secure by Default** طراحی شود.

## اصول طراحی
- **Least Privilege**: هر کاربر فقط به Endpointهای مرتبط با Role خود دسترسی دارد.
- **Hard Control**: کنترل‌ها فقط در UI نیستند و در Service Layer و Workflow Layer enforce می‌شوند.
- **Traceability**: اقدامات حساس باید Audit Trail داشته باشند.
- **Defense in Depth**: کنترل‌ها در چند لایه اپلیکیشن، هویت، شبکه و استقرار اعمال می‌شوند.
- **Simplicity First**: راهکارهای MVP باید ساده، قابل نگهداری و قابل ارتقاء به معماری Enterprise باشند.

## کنترل‌های پیاده‌سازی‌شده در کد
### Identity / Access
- Login با Bearer Token
- Password Hashing با PBKDF2-HMAC-SHA256
- Password Policy برای کاربران عملیاتی جدید
- Forced Password Reset و Self-service Change Password
- RBAC در سطح Endpoint
- تطبیق Actor و Actor Role با کاربر لاگین‌شده
- Revocation برای Token از طریق Logout
- Session Inventory / Session Revocation برای نقش‌های مجاز

### Brute Force / Session Protection
- Lockout کاربر پس از چند تلاش ناموفق متوالی
- Rate Limit روی Login Endpoint
- انقضای Token
- Reject کردن Tokenهای revoked یا expired

### Response Hardening
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: same-origin`
- `Permissions-Policy`
- `Cache-Control: no-store`

### Monitoring / Audit
- ثبت رویدادهای `login_success`
- ثبت `login_failed`
- ثبت `account_locked`
- ثبت `login_blocked`
- ثبت `rate_limit_block`
- ثبت `logout`
- ثبت `invalid_token` / `expired_token` / `revoked_token`
- ثبت `token_cleanup`
- جست‌وجوی متمرکز Audit از طریق `GET /api/v1/audit/events`
- مشاهده رویدادهای یک Entity از طریق `GET /api/v1/audit/entities/{entity_name}/{entity_id}`
- مشاهده خلاصه رویدادها از طریق `GET /api/v1/dashboard/security`

### Security Incident Review Workflow
- Incident به‌صورت Workflow Object مستقل ثبت می‌شود
- مراحل Incident: `open` → `under_review` → `contained` → `resolved` → `closed`
- ثبت Incident می‌تواند بر اساس Audit Eventهای شناسایی‌شده انجام شود
- Containment بدون `containment_action` مجاز نیست
- Resolve بدون `resolution_note` مجاز نیست
- Incident Review برای Roleهای مجاز امنیتی محدود شده است

## معماری استقرار پیشنهادی
### DMZ / Reverse Proxy
- استقرار API پشت Reverse Proxy یا API Gateway
- TLS termination در لایه Proxy
- اعمال HSTS در لایه Edge
- محدودسازی روش‌های HTTP غیرضروری
- اعمال Rate Limit تکمیلی در Proxy/WAF

### Network Segmentation
- لایه Web/API در Subnet جدا از DB
- دیتابیس فقط از Application Subnet قابل دسترسی باشد
- عدم دسترسی مستقیم کاربر نهایی به DB
- محدودسازی پورت‌ها با Security Group / Firewall

### Secrets / Config
- Secretها در `.env` فقط برای محیط محلی توسعه
- در محیط عملیاتی از Secret Manager استفاده شود
- Rotation برای Secretها و Credentialهای حساس تعریف شود
- `docs_enabled=false` در Production مگر برای محیط‌های کنترل‌شده

### Database Security
- حساب DB با حداقل سطح دسترسی
- Backup رمزگذاری‌شده
- Audit نگهداری تغییرات حساس
- Migration کنترل‌شده و قابل بازگشت

## مواردی که در MVP به‌صورت Assumption باقی مانده‌اند
- **Assumption:** TLS end-to-end در لایه استقرار پیاده می‌شود.
- **Assumption:** WAF یا Reverse Proxy سازمانی Rate Limit و IP Reputation را تکمیل می‌کند.
- **Assumption:** Secret Manager، SIEM، EDR و Centralized Logging در لایه زیرساخت سازمان فعال می‌شوند.
- **Assumption:** تست نفوذ، SAST/DAST و Dependency Scanning در Pipeline CI/CD اضافه می‌شود.

## گام‌های بعدی امنیتی پیشنهادی
1. Refresh Token و Session Risk Scoring
2. IP Allowlist برای Endpointهای حساس ادمین
3. Row-Level Data Authorization برای برخی دامنه‌ها
4. CSP در لایه UI و Header Hardening تکمیلی
5. Background job زمان‌بندی‌شده برای پاکسازی Tokenهای منقضی
6. SIEM integration برای تشخیص الگوهای مشکوک
7. SAST/DAST + Dependency Scanning در CI/CD
8. Correlation Rules بین Alertها، Auditها و Incidentها
9. Step-up Authentication برای عملیات حساس
