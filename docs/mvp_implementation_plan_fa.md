# برنامه اجرایی گام‌های بعدی برای تبدیل طرح به نمونه عملیاتی

## هدف
این برنامه، مسیر تبدیل طراحی مفهومی و دیتامدل به یک MVP قابل اجرا را مشخص می‌کند.

---

## Stage 1 — تثبیت طراحی و کنترل‌ها

### خروجی‌های لازم
- نهایی‌سازی Workflowهای JSON در `config/workflows/`
- نهایی‌سازی Rule Catalog در `config/rules/business_rules.json`
- نهایی‌سازی SLA، DOA و SoD در `config/`
- بازبینی توسط مالک فرآیند، مالی، خرید، فروش و پروژه

### معیار خروجی
- هر Transition یک Role مالک داشته باشد
- هر Transition حیاتی Rule مرجع داشته باشد
- همه موارد Block/Warning/Escalate مشخص باشند

---

## Stage 2 — نمونه Excel کنترل‌محور

### خروجی‌های آماده‌شده
- فایل: `prototype/Borna_Process_Control_Prototype.xlsx`
- قالب‌های CSV: `prototype/csv/`

### کارهای بعدی روی Excel
1. افزودن Data Validation بین شیت‌ها
2. تعریف Conditional Formatting برای Overdue / Blocked / Exception
3. ساخت Pivot Dashboard
4. ساخت شماره‌گذار سند
5. افزودن ماکرو یا Office Script برای کنترل Submit/Approve

### معیار پذیرش
- از PR تا Payment بتوان رکورد را ردیابی کرد
- وضعیت جاری و مسئول جاری قابل مشاهده باشد
- هشدارهای پایه قابل استخراج باشد

---

## Stage 3 — Backlog فنی نسخه Server

### Epic 1 — Identity & Access
- Login/SSO
- User / Role / Department Management
- Permission Enforcement
- SoD check on sensitive actions

### Epic 2 — Workflow Core
- Workflow definition loader از JSON
- State transition service
- Task inbox
- Approval engine
- SLA timer / escalation scheduler

### Epic 3 — Procurement MVP
- PR CRUD + submit
- Approval routing
- RFQ creation
- Quotation entry & comparison
- PO issue
- GRN
- QC
- Invoice matching
- Payment approval

### Epic 4 — Costing / Pricing / Sales MVP
- Cost sheet
- Price proposal
- Sales order
- Delivery
- Invoice
- Collection follow-up

### Epic 5 — Dashboards / Alerts / Audit
- Alert service
- Audit log service
- Executive dashboard
- Procurement dashboard
- My Tasks / My Alerts

---

## Stage 4 — ترتیب پیشنهادی اسپرینت‌ها

### Sprint 0 — Foundation
- Repository structure
- DB migration baseline
- Seed master tables
- Config loader
- Auth skeleton

### Sprint 1 — Workflow Core
- Workflow instances
- Tasks
- Approvals
- Transition validation
- Audit log

### Sprint 2 — Procurement Flow
- PR
- RFQ
- Quotations
- PO
- Basic dashboards

### Sprint 3 — Receipt / QC / Match
- GRN
- QC
- Exception handling
- 3-way match
- Payment hold logic

### Sprint 4 — Costing / Pricing / Sales
- Cost sheets
- Pricing approval
- Sales order
- Credit control
- Delivery & invoice

### Sprint 5 — Project / Change / Hardening
- Projects
- Change requests
- Escalation scheduler
- KPI snapshots
- Security hardening

---

## Stage 5 — تصمیمات موردنیاز قبل از توسعه کامل

### Required Input
- تکنولوژی ترجیحی نسخه Server
  - .NET / Java / Node.js / Python
- نوع احراز هویت
  - Local / LDAP / AD / OIDC
- پایگاه داده هدف
  - PostgreSQL / SQL Server / Oracle
- روش اعلان
  - Email / SMS / Teams / WhatsApp داخلی
- واحد پول پایه و تقویم کاری
- DOA واقعی سازمان
- آستانه‌های Variance واقعی

---

## پیشنهاد عملی بعدی
اگر بخواهیم بلافاصله وارد فاز اجرایی شویم، ترتیب بهینه این است:

1. تأیید Workflow و Ruleها توسط ذی‌نفعان
2. تست Prototype Excel با 5 سناریوی واقعی سازمان
3. انتخاب Tech Stack نسخه Server
4. ساخت Skeleton فنی پروژه
5. پیاده‌سازی Procurement MVP

---

## خروجی‌های آماده در این ریپو
- `docs/enterprise_system_design_fa.md`
- `docs/database_schema.sql`
- `docs/erd_mermaid.md`
- `config/`
- `prototype/Borna_Process_Control_Prototype.xlsx`
- `prototype/csv/`
- `scripts/build_excel_prototype.py`
