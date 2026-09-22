# MVP نسخه Server با Python + FastAPI + PostgreSQL

## آنچه در این گام پیاده‌سازی شد

### 1) اسکلت فنی پروژه
- `app/main.py`
- `app/core/`
- `app/models/`
- `app/schemas/`
- `app/services/`
- `app/api/`

### 2) قابلیت‌های پیاده‌سازی‌شده
- FastAPI app factory
- اتصال دیتابیس با SQLAlchemy
- ایجاد جداول پایه در Startup
- Seed اولیه Workflow Definitionها از فایل‌های `config/workflows/*.json`
- API خواندن Workflow / Rules / SLA / DOA / SoD
- Authentication با Login و Bearer Token
- Seed خودکار کاربران تستی
- Role-Based Access Control در سطح Endpoint
- API Users برای مدیریت پایه کاربر در MVP
- Web Console سبک برای تست تعاملی و بازبینی API در `/` و `/console`
- Inbox برای My Tasks و Approval Actions
- API پایه Supplier Master
- API پایه Purchase Request
- Approval Flow برای Review و Approve PR
- API برای RFQ
- API برای Supplier Quotation
- API برای Commercial Evaluation / Technical Approval / Price Approval
- API برای تبدیل RFQ به Purchase Order
- API برای Goods Receipt
- API برای Quality Inspection و نهایی‌سازی Accepted / Rejected
- API برای Supplier Invoice و 3-way Match پایه
- API برای Payment Creation / Approval / Execution
- API برای Customer Master و Product Master
- API برای Price Proposal / Pricing Approval
- API برای Sales Order / Credit Control / Sales Confirmation
- Alert Engine پایه و API مشاهده Alertها
- SLA / Escalation Scheduler قابل اجرا از طریق API
- Traceability API برای Procurement و Sales Linked Document View و Timeline Summary
- Dashboard summary اولیه
- Security Monitoring Dashboard و Token Cleanup API
- Audit Log پایه برای Create/Submit/Approve/Create RFQ/Create PO/Create Receipt/Create Invoice/Payment Actions و Security/Sales Lifecycle Events
- ثبت Approval History برای PR، RFQ، PO، Payment، Price Approval و Sales Confirmation

### 3) Hard Controlهایی که بالفعل در کد اعمال شده‌اند
در مسیرهای فعلی این کنترل‌ها در **Service Layer + Workflow Layer** اعمال می‌شوند:

#### Purchase Request
- PR بدون Line → Block
- PR بدون Reason → Block
- PR بدون Cost Center → Block
- Line بدون Cost Center → Block
- PR خارج از بودجه بدون Exception Approved → Block
- Transition نامعتبر یا Role نامعتبر → Block

#### RFQ / Quotation / PO
- ایجاد RFQ قبل از Approved شدن PR → Block
- ثبت Record Quotes قبل از حداقل تعداد استعلام و بدون Exception Approved → Block
- Commercial Evaluation بدون Quotation منتخب → Block
- Price Approval بدون Quotation منتخب → Block
- Issue PO قبل از Price Approved شدن RFQ → Block
- Issue PO برای Supplier فاقد Approved Status → Block
- Issue PO برای Quotation غیرمنتخب → Block
- Transition نامعتبر یا Role نامعتبر در مراحل ارزیابی و تأیید → Block

#### Receipt / QC / Match / Payment
- Receipt بدون PO معتبر یا خارج از توالی Workflow → Block
- QC فقط بعد از Receipt → Block
- Inventory Release برای QC Rejected → Block
- Invoice Match بدون QC Accepted / Inventory Released → Block
- Payment Creation قبل از Match موفق → Block
- Payment Amount بالاتر از مبلغ Invoice → Block
- Payment Approval بدون Match موفق → Block
- Execute Payment قبل از Payment Approval → Block

#### Pricing / Sales / Credit Control
- Price Proposal بدون Cost Basis معتبر → Block
- Sales Order بدون Price List تأییدشده → Block
- Price List نامرتبط با Customer/Product → Block
- Confirm Sales Order در صورت عبور از Credit Limit → Block + Alert
- Confirm Sales Order در صورت Credit Status نامعتبر → Block + Alert
- Sales Below Floor → Alert + Manager Approval Flow
- Sales Creator نمی‌تواند Final Approver همان Sales Order باشد → Block

#### Delivery / Sales Invoice / Collection
- Delivery Planning فقط بعد از Confirmed Sales Order → Block
- Planned Qty یا Delivered Qty بالاتر از Qty سفارش → Block
- Delivery Execution قبل از Release Delivery → Block
- Sales Invoice قبل از Delivered شدن سفارش → Block
- Sales Invoice Amount بالاتر از Delivered Value → Block
- Collection فقط برای Invoice باز و هم‌ارز با Currency آن → Block
- Collection Amount بالاتر از مانده باز Invoice → Block
- Profitability Review فقط بعد از Full Collection → Block
- Case Closure فقط بعد از Profitability Review → Block

#### Authentication / RBAC / SoD
- همه Endpointهای عملیاتی نیازمند Authentication هستند
- هر Endpoint نقش مجاز خود را کنترل می‌کند
- Actor و Actor Role باید با کاربر لاگین‌شده منطبق باشند
- Requester نمی‌تواند Final Approver همان PR باشد
- Goods Receiver نمی‌تواند QC همان Receipt را نهایی کند
- Payment Executor باید مستقل از Creator / Matcher باشد
- Logout باعث Revocation Token می‌شود
- Token Expired یا Revoked پذیرفته نمی‌شود

#### Security / Brute-force / Session Hardening
- Password به‌صورت Hash ذخیره می‌شود و Plain Text نگهداری نمی‌شود
- Password Policy برای کاربران عملیاتی جدید enforce می‌شود
- Forced Password Reset و Self-service Change Password پشتیبانی می‌شود
- تا قبل از تغییر Password اجباری، استفاده از Endpointهای عملیاتی → Block
- پس از چند Login Failed متوالی، Account Lockout اعمال می‌شود
- روی Login Endpoint Rate Limit پایه اعمال می‌شود
- Session Inventory و Revocation از طریق API پشتیبانی می‌شود
- Cleanup عملیاتی Tokenهای Revoked / Expired از طریق API انجام‌پذیر است
- رویدادهای امنیتی مانند `login_failed`، `account_locked`، `login_blocked`، `rate_limit_block`، `invalid_token`، `revoked_token`، `password_changed` و `logout` در Audit ثبت می‌شوند
- Headerهای امنیتی پایه روی Responseها اعمال می‌شوند

#### SLA / Escalation
- Due Date بر اساس `config/sla_profiles.json` روی Workflow Instance تنظیم می‌شود
- Scheduler موارد Overdue را شناسایی می‌کند
- Escalation Level بر اساس پروفایل Escalation محاسبه می‌شود
- Alertهای SLA با Severity و Escalation Level ثبت می‌شوند
- با تغییر State یا رفع Overdue، Alertهای باز Resolve می‌شوند

#### Traceability / Linked Documents
- از Purchase Request تا Payment زنجیره اسناد مرتبط قابل بازیابی است
- از Sales Order تا Collection Receipt نیز زنجیره اسناد مرتبط قابل بازیابی است
- از هر Document پشتیبانی‌شده می‌توان Root سند بالادستی را تشخیص داد
- وضعیت جاری، مسئول جاری، Due Date، Escalation Level و اثر مالی در Overview بازگردانده می‌شود
- Timeline ترکیبی از Audit Log، Approvalها و Alertها ارائه می‌شود

#### Central Audit / Incident Review
- Audit Eventها به‌صورت متمرکز با فیلترهای Entity / User / Action / Time / Text قابل جست‌وجو هستند
- Security Incident به‌صورت Workflow Object مستقل ثبت می‌شود
- Incident فقط در توالی `open → under_review → contained → resolved → closed` پیش می‌رود
- Containment بدون اقدام مهاری مستند → Block
- Resolve بدون Resolution Note → Block

یعنی منطق فقط در UI نیست؛ در Service Layer و Workflow Layer نیز اعمال می‌شود.

---

## Endpointهای فعلی

### Health
- `GET /api/v1/health`

### Config Registry
- `GET /api/v1/config/workflows`
- `GET /api/v1/config/rules`
- `GET /api/v1/config/sla`
- `GET /api/v1/config/doa`
- `GET /api/v1/config/sod`

### Auth / Users / Inbox / Alerts
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/inbox/my-tasks`
- `GET /api/v1/inbox/approvals`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/my`
- `POST /api/v1/scheduler/run-sla`
- `GET /api/v1/security/dashboard`
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

### Supplier Master
- `POST /api/v1/suppliers`
- `GET /api/v1/suppliers`

### Purchase Request
- `POST /api/v1/purchase-requests`
- `GET /api/v1/purchase-requests`
- `GET /api/v1/purchase-requests/{id}`
- `POST /api/v1/purchase-requests/{id}/submit`
- `POST /api/v1/purchase-requests/{id}/route-review`
- `POST /api/v1/purchase-requests/{id}/approve`

### RFQ & Quotations
- `POST /api/v1/rfqs`
- `GET /api/v1/rfqs`
- `GET /api/v1/rfqs/{id}`
- `POST /api/v1/rfqs/{id}/quotations`
- `POST /api/v1/rfqs/{id}/record-quotes`
- `POST /api/v1/rfqs/{id}/commercial-evaluate`
- `POST /api/v1/rfqs/{id}/technical-approve`
- `POST /api/v1/rfqs/{id}/price-approve`

### Purchase Orders
- `POST /api/v1/purchase-orders`
- `GET /api/v1/purchase-orders`
- `GET /api/v1/purchase-orders/{id}`

### Goods Receipts
- `POST /api/v1/goods-receipts`
- `GET /api/v1/goods-receipts`
- `GET /api/v1/goods-receipts/{id}`

### Quality Inspections
- `POST /api/v1/quality-inspections`
- `POST /api/v1/quality-inspections/{id}/finalize`
- `GET /api/v1/quality-inspections`
- `GET /api/v1/quality-inspections/{id}`

### Supplier Invoices
- `POST /api/v1/supplier-invoices`
- `POST /api/v1/supplier-invoices/{id}/match`
- `GET /api/v1/supplier-invoices`
- `GET /api/v1/supplier-invoices/{id}`

### Payments
- `POST /api/v1/payments`
- `POST /api/v1/payments/{id}/approve`
- `POST /api/v1/payments/{id}/execute`
- `GET /api/v1/payments`
- `GET /api/v1/payments/{id}`

### Approvals
- `GET /api/v1/approvals/{object_type}/{object_id}`

### Traceability
- `GET /api/v1/traceability/purchase-requests/{id}`
- `GET /api/v1/traceability/sales-orders/{id}`
- `GET /api/v1/traceability/document/{object_type}/{object_id}`

### Dashboard
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/security`

---

## روش اجرا

### Web Console برای بازبینی تعاملی
- `/`
- `/console`

این کنسول سبک برای Login، Dashboard، Audit Search، Security Incident Review، Traceability و ارسال Requestهای دلخواه به API طراحی شده است.

در نسخه فعلی، کنسول علاوه بر کنترل‌های امنیتی، دو مسیر بازبینی سناریومحور هم دارد:
- Procurement workflow runner برای PR create / submit / review / approve
- Downstream procurement runner برای RFQ / quotation / commercial eval / technical approve / price approve / PO / GRN / QC / invoice / payment

### حالت ساده محلی
```bash
cp .env.example .env
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### حالت Docker Compose
```bash
docker compose up --build
```

---

## گام بعدی پیشنهادی در توسعه

### Wave 1
- Authentication / User Management
- Role/Permission enforcement
- Approval Center
- Workflow Task Inbox

### Wave 2
- RFQ
- Quotation Comparison
- PO
- GRN
- QC

> بخش RFQ / Quotation / PO در این گام به‌صورت MVP اولیه پیاده‌سازی شده است.

### Wave 3
- 3-way match
- Payment Approval
- Alerts & Escalation Scheduler
- Traceability View

> بخش Goods Receipt / QC / Supplier Invoice Match / Payment Controls در این گام به‌صورت MVP اولیه پیاده‌سازی شده است.

### Wave 4
- Costing
- Delivery / Invoice / Collection

> بخش Pricing / Sales Order / Credit Control در این گام به‌صورت MVP اولیه پیاده‌سازی شده است.

---

## محدودیت فعلی این Skeleton
- همه Entityهای نهایی SQL هنوز به Modelهای FastAPI تبدیل نشده‌اند
- Migration tool مثل Alembic هنوز اضافه نشده
- Auth و RBAC کامل هنوز پیاده‌سازی نشده
- Rule Engine در سطح MVP فقط بخشی از قواعد را به‌صورت کدنویسی‌شده enforce می‌کند
- PostgreSQL هدف اصلی است ولی برای شروع، SQLite هم برای اجرای سریع محلی پشتیبانی می‌شود
