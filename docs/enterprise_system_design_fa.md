# طرح جامع سامانه مدیریت فرآیندهای عملیاتی و کنترلی سازمان

## دامنه
این سند طراحی، سامانه‌ای Process-Controlled را برای دو جریان اصلی پوشش می‌دهد:

1. **Need → Request → Approval → Procurement → Supplier → Purchase → Receipt → QC → Inventory → Production → Costing → Pricing → Sales → Delivery → Invoice → Collection → Profitability**
2. **Idea → Feasibility → Business Case → Investment Approval → Project → Procurement → Implementation → Commissioning → Commercialization → Post-Implementation Review**

---

## مفروضات، پارامترهای قابل تنظیم و ورودی‌های لازم

### Assumptions
- سازمان دارای ساختار واحدی شامل خرید، انبار، کنترل کیفیت، تولید، فروش، مالی، پروژه، مهندسی، IT و مدیریت ارشد است.
- همه اسناد عملیاتی دارای شماره یکتای سیستمی هستند.
- همه کنترل‌های مهم علاوه بر UI در **Business Layer / Server Layer** نیز اعمال می‌شوند.
- کاربران فقط از طریق حساب‌های نام‌دار و قابل Audit وارد سیستم می‌شوند.

### Configurable Parameters
- SLA هر مرحله
- سطوح Escalation
- آستانه‌های قیمت خرید و فروش
- حدود اعتبار مشتری
- حدود مبلغ در DOA
- حداقل تعداد استعلام‌ها
- سیاست‌های سه‌طرفه/چهارطرفه تطبیق اسناد
- Rule Severity: Warning / Block / Escalate / Exception

### Required Inputs برای پیاده‌سازی نهایی
- ساختار سازمانی و چارت نقش‌ها
- حدود ریالی/ارزی مجاز برای تأییدها
- تقویم کاری و تعطیلات
- سیاست بودجه و مراکز هزینه
- روش بهای تمام‌شده و مبانی جذب سربار
- سیاست قیمت‌گذاری هر خانواده محصول
- سیاست اعتبار مشتری و شرایط وصول

---

## نقشه تطبیق با خروجی‌های درخواستی A تا Z

| کد | خروجی | محل در سند |
|---|---|---|
| A | Business Process Architecture | Phase 1 |
| B | End-to-End Process Map | Phase 1 |
| C | BPMN | Phase 1 |
| D | Workflow State Machine | Phase 2 |
| E | Business Rules | Phase 2 |
| F | RACI | Phase 2 |
| G | SoD Matrix | Phase 2 |
| H | DOA Matrix | Phase 2 |
| I | Data Model | Phase 3 |
| J | Database Schema | Phase 3 + `docs/database_schema.sql` |
| K | Screen List | Phase 4 |
| L | User Roles | Phase 4 |
| M | Permission Matrix | Phase 4 |
| N | Dashboard Design | Phase 5 |
| O | Alert Engine | Phase 5 |
| P | Escalation Engine | Phase 5 |
| Q | Error Detection Rules | Phase 2 و 5 |
| R | Costing Engine | Phase 2 و 3 |
| S | Pricing Engine | Phase 2 و 3 |
| T | Project Module | Phase 1 و 2 |
| U | Exception Management | Phase 2 |
| V | Audit Trail | Phase 3 و 7 |
| W | KPI Dictionary | Phase 5 |
| X | Excel Prototype Architecture | Phase 6 |
| Y | Software Architecture | Phase 7 |
| Z | Test Scenarios | Phase 8 |

---

# Phase 1 — Business & Process Architecture

## 1) اصول معماری سامانه

### اصل محوری
**هر عملیات یک Workflow Object است** و باید دارای این ابعاد باشد:
- شناسه یکتا
- نوع فرآیند و سند مبنا
- وضعیت جاری
- مسئول جاری
- تأییدکننده بعدی
- پیش‌شرط‌ها
- خروجی مورد انتظار
- SLA و Due Date
- تاریخچه تغییرات
- ریسک، خطا، استثنا و اثر مالی

### اصول کنترل‌محور
1. **فرآیندمحور، نه فرم‌محور**
2. **State Machine اجباری** برای هر فرآیند
3. **Hard Control** برای موارد حیاتی
4. **Traceability انتها به انتها**
5. **تفکیک وظایف (SoD)**
6. **Escalation و SLA بومی‌سازی‌پذیر**
7. **Audit Trail غیرقابل حذف**
8. **Rule Engine قابل پیکربندی**
9. **Dashboard عملیاتی بلادرنگ**
10. **کنترل در لایه سرور، نه فقط رابط کاربر**

## 2) معماری فرآیندی کلان

### لایه L0 — Capability Map
- Governance & Master Data
- Workflow & Approvals
- Procurement & Supplier Management
- Inventory & Quality
- Production & Costing
- Pricing & Sales
- Finance & Collection
- Project & CAPEX Management
- Internal Control, Audit & Risk
- Dashboard, KPI & Analytics

### لایه L1 — Process Domains
1. **Master Data**: Users, Roles, Materials, Products, Suppliers, Customers, BOM, Cost Centers
2. **Source-to-Pay**: PR, Approval, RFQ, Quotation, Evaluation, PO, Receipt, QC, Match, Payment
3. **Plan-to-Produce**: Plan, Material Allocation, Production Order, Consumption, Output, Scrap, Rework, Costing
4. **Price-to-Cash**: Inquiry, Quotation, Price Approval, Sales Order, Delivery, Invoice, Collection, Profitability
5. **Idea-to-Value**: Idea, Feasibility, Business Case, Approval, Project, Procurement, Commissioning, PIR
6. **Control Layer**: Rule Engine, Alerts, Exceptions, Audit, Escalation, KPI

## 3) نقشه End-to-End فرآیندها

### 3.1 زنجیره تأمین و خرید
```text
Need Identification
→ Purchase Request
→ Budget Check
→ Approval
→ RFQ
→ Supplier Response
→ Commercial/Technical Evaluation
→ Price Approval
→ Purchase Order
→ Delivery Tracking
→ Goods Receipt
→ Quality Inspection
→ Inventory Release / Rejection
→ Invoice Matching
→ Payment Approval
→ Payment
→ Supplier Performance Update
→ Case Closure
```

### 3.2 زنجیره تولید و بهای تمام‌شده
```text
Demand / Sales Order / Forecast
→ Production Planning
→ Material Availability Check
→ Production Order
→ Material Issue
→ Operation Confirmation
→ Output Receipt
→ QC
→ Scrap/Rework Registration
→ Cost Collection
→ Standard vs Actual Analysis
→ Cost Approval
→ Price Feed
```

### 3.3 زنجیره فروش و وصول
```text
Customer Need / Inquiry
→ Commercial Proposal
→ Price Validation
→ Discount / Credit Check
→ Sales Order
→ ATP / Production Link
→ Delivery
→ Invoice
→ Collection Follow-up
→ Receipt Allocation
→ Margin Analysis
→ Case Closure
```

### 3.4 زنجیره پروژه‌های توسعه‌ای
```text
Idea
→ Screening
→ Feasibility
→ Business Case
→ Investment Approval
→ Project Charter
→ Budget Baseline
→ Procurement / Contracting
→ Implementation
→ Commissioning
→ Launch / Commercialization
→ Post Implementation Review
```

## 4) BPMN سطح طراحی

### 4.1 BPMN مفهومی خرید
```text
Pool: Organization
  Lane: Requester           -> Create PR
  Lane: Department Manager  -> Review / Approve PR
  Lane: Budget Controller   -> Budget Check
  Lane: Procurement         -> Create RFQ / Receive Quotations / Evaluate
  Lane: Technical Team      -> Technical Evaluation
  Lane: Finance             -> Price & Payment Terms Validation
  Lane: Approver            -> Final Approval
  Lane: Supplier            -> Deliver Goods
  Lane: Warehouse           -> Receive Goods
  Lane: QC                  -> Inspect
  Lane: AP                  -> Match Invoice
  Lane: Treasury            -> Pay
End Event: Procurement Closed
```

### 4.2 BPMN مفهومی فروش
```text
Pool: Organization
  Lane: Sales               -> Create Opportunity / Offer
  Lane: Pricing             -> Calculate Price
  Lane: Sales Manager       -> Discount Approval
  Lane: Credit Control      -> Credit Check
  Lane: Planning/Production -> Confirm Availability
  Lane: Logistics           -> Delivery
  Lane: Finance             -> Invoice
  Lane: Collections         -> Follow-up / Allocate Receipt
End Event: Order Collected and Closed
```

### 4.3 BPMN مفهومی پروژه
```text
Pool: Organization
  Lane: Sponsor             -> Submit Idea
  Lane: PMO                 -> Screening
  Lane: Engineering         -> Feasibility
  Lane: Finance             -> Business Case / NPV / Budget
  Lane: Investment Committee-> Approval
  Lane: Project Manager     -> Execution
  Lane: Procurement         -> CAPEX Procurement
  Lane: Operations          -> Commissioning / Launch
  Lane: Internal Audit      -> Post Implementation Review
End Event: Project Closed with PIR
```

## 5) معماری ماژول‌ها

### Core Modules
- Identity & Access
- Organization & Master Data
- Workflow Engine
- Rule Engine
- Procurement
- Supplier Management
- Inventory & QC
- Production & Costing
- Pricing
- Sales & Credit
- Finance Match & Payment
- Projects & Change Management
- Alerts & Escalations
- Audit & Reporting

### Cross-Cutting Services
- Notification Service
- Document Management
- Numbering Service
- Approval Service
- Integration Service
- Analytics Service

---

# Phase 2 — Detailed Workflow & Business Rules

## 6) مدل استاندارد Workflow Object

هر Workflow Object باید این ساختار را داشته باشد:
- `object_type`: PR, RFQ, PO, GRN, QC, SO, Project, ChangeRequest, ...
- `object_id`
- `workflow_definition_id`
- `current_state`
- `current_owner_user_id`
- `current_owner_role_id`
- `due_at`
- `priority`
- `business_impact_amount`
- `risk_level`
- `source_document_ref`
- `previous_object_ref`
- `next_object_ref`
- `exception_flag`
- `hold_reason`
- `closure_reason`

## 7) State Machine — فرآیند خرید عادی

```text
Draft
↓ Submit
Submitted
↓ Budget/Policy Validation
Under Review
↓ Approval Passed
Approved
↓ Procurement Action
RFQ Created
↓ Supplier Responses
Quotation Received
↓ Evaluation
Commercial Evaluated
↓ Technical Validation
Technically Approved
↓ Price/DOA Approval
Price Approved
↓ Issue PO
PO Issued
↓ Supplier Delivery Window
Waiting Delivery
↓ Warehouse Receipt
Received
↓ QC Inspection
QC Pending
↓ Pass/Fail
Accepted / Rejected
↓ If Accepted
Inventory Released
↓ Invoice + Match
Invoice Matched
↓ Payment Approval
Payment Approved
↓ Treasury Payment
Paid
↓ Close
Closed
```

### قواعد انتقال اصلی خرید
| From | To | شرط | کنترل |
|---|---|---|---|
| Draft | Submitted | حداقل یک ردیف کالا، مرکز هزینه، علت نیاز | Block |
| Submitted | Under Review | PR کامل و سند پیوست شده | Block |
| Under Review | Approved | Approval مطابق DOA | Block |
| Approved | RFQ Created | بودجه/استثنا مشخص | Block |
| RFQ Created | Quotation Received | حداقل تعداد استعلام یا مجوز استثنا | Block |
| Quotation Received | Commercial Evaluated | ثبت مقایسه قیمت | Block |
| Commercial Evaluated | Technically Approved | تأیید فنی برای اقلام فنی | Block |
| Technically Approved | Price Approved | Variance > Threshold نیازمند Approval | Escalate/Block |
| Price Approved | PO Issued | Supplier Approved, Terms Approved | Block |
| PO Issued | Received | PO معتبر و باز | Block |
| Received | QC Pending | GRN ثبت شده | Block |
| QC Pending | Inventory Released | QC=Pass | Block |
| Inventory Released | Invoice Matched | Match موفق PO/GRN/Invoice | Block |
| Invoice Matched | Payment Approved | تأیید مالی و سررسید | Block |
| Payment Approved | Paid | مجوز پرداخت + اطلاعات بانکی معتبر | Block |

## 8) State Machine — خرید اضطراری

```text
Emergency Draft
↓
Emergency Submitted
↓
Emergency Approval
↓
Direct Purchase Allowed
↓
Receipt / Service Confirmation
↓
Post Review
↓
Root Cause Review
↓
Closed
```

### کنترل‌های اجباری خرید اضطراری
- علت اضطرار الزامی
- تأییدکننده اضطراری الزامی
- مبلغ و Supplier الزامی
- انحراف از فرآیند عادی ثبت می‌شود
- Post Review و Root Cause الزامی است
- تکرار اضطرار برای یک کالا/واحد هشدار سیستمی تولید می‌کند
- خرید اضطراری **گزینه پیش‌فرض نیست** و نیازمند مجوز سطح بالاتر است

## 9) State Machine — فروش

```text
Draft Inquiry
↓
Quoted
↓
Pricing Review
↓
Price Approved
↓
Credit Check
↓
Sales Order Confirmed
↓
Planning / Production Allocation
↓
Ready to Deliver
↓
Delivered
↓
Invoiced
↓
Collection Open
↓
Collected / Partially Collected
↓
Profitability Reviewed
↓
Closed
```

### کنترل‌های کلیدی فروش
- قیمت فروش زیر کف → Approval Escalation یا Block طبق DOA
- مشتری بالاتر از Credit Limit → Block یا Hold
- سفارش بدون موجودی/برنامه تولید → Hold
- Delivery بدون SO معتبر → Block
- Invoice بدون Delivery/Service Confirmation → Block
- Receipt allocation ناقص → پرونده وصول باز می‌ماند

## 10) State Machine — پروژه توسعه‌ای

```text
Idea Logged
↓
Screening
↓
Feasibility
↓
Business Case Prepared
↓
Investment Approved
↓
Project Initiated
↓
Execution
↓
Commissioning
↓
Launch
↓
Post Implementation Review
↓
Closed
```

### کنترل‌های پروژه
- Feasibility بدون Sponsor و Owner ثبت نمی‌شود
- Business Case بدون CAPEX/OPEX/Benefit قابل Submit نیست
- شروع اجرای پروژه بدون Investment Approval ممنوع
- تغییر بودجه/زمان‌بندی فقط از مسیر Change Request
- هر Milestone باید تاریخ مبنا، تاریخ واقعی، مسئول و وضعیت داشته باشد

## 11) State Machine — Change Management

```text
Draft Change Request
↓
Submitted
↓
Impact Analysis
↓
Approval
↓
Implementation
↓
Verification
↓
Closed / Rejected
```

### انواع Change تحت پوشش
- Price Change
- Supplier Change
- BOM Change
- Product Spec Change
- Project Budget Change
- Schedule Change
- Contract Change

## 12) Business Rule Engine Design

### طبقه‌بندی Rule
1. **Precondition Rule**: پیش‌نیاز شروع یا انتقال
2. **Validation Rule**: بررسی صحت داده
3. **Policy Rule**: انطباق با سیاست سازمان
4. **Matching Rule**: تطبیق بین اسناد
5. **Threshold Rule**: عبور از حد مجاز
6. **SLA Rule**: تأخیر و Escalation
7. **Segregation Rule**: تضاد نقش‌ها
8. **Audit Rule**: تغییرات حساس
9. **Exception Rule**: مسیرهای غیرعادی
10. **Calculation Rule**: هزینه، قیمت، واریانس

### ساختار پیشنهادی Rule
- `rule_code`
- `process`
- `applies_to_document`
- `event`: Create / Submit / Approve / Transition / Update / Close
- `condition_expression`
- `severity`: Info / Warning / Block / Escalate / Exception
- `owner_role`
- `escalation_profile`
- `effective_from / effective_to`

## 13) کاتالوگ قواعد کلیدی کسب‌وکار

| Rule Code | شرح | نوع | شدت |
|---|---|---|---|
| PR-001 | PR بدون مرکز هزینه و دلیل نیاز ثبت نهایی نشود | Validation | Block |
| PR-002 | PR بالاتر از بودجه بدون مجوز استثنا به RFQ نرود | Budget | Block |
| RFQ-001 | قبل از Approval، RFQ ممنوع | Precondition | Block |
| RFQ-002 | حداقل تعداد استعلام طبق Policy کنترل شود | Policy | Block/Exception |
| QUO-001 | مقایسه قیمت و شرایط قبل از PO الزامی است | Policy | Block |
| SUP-001 | Supplier فاقد Approved Status قابل انتخاب برای PO نیست | Master Data | Block |
| SUP-002 | Supplier پرریسک نیازمند تأیید اضافی است | Risk | Escalate |
| PO-001 | PO بدون Evaluation و Approval معتبر صادر نشود | Workflow | Block |
| PO-002 | Variance قیمت خرید بالاتر از Threshold نیازمند Escalation | Threshold | Escalate |
| GRN-001 | Receipt بدون PO معتبر مجاز نیست مگر Exception ثبت‌شده | Matching | Block/Exception |
| QC-001 | کالای مردود وارد موجودی قابل مصرف نشود | Quality | Block |
| INV-001 | Invoice بدون GRN/Service Confirmation پرداخت نشود | Matching | Block |
| PAY-001 | Payment بدون 3-way match ممنوع | Financial | Block |
| CST-001 | Cost Sheet بدون نرخ جذب مصوب تأیید نشود | Calculation | Block |
| PRC-001 | Final Price بدون Approved Cost منتشر نشود | Precondition | Block |
| PRC-002 | فروش زیر کف قیمت طبق DOA Escalation بخورد | Threshold | Escalate/Block |
| SAL-001 | SO مشتری بدهکار از Credit Limit عبور نکند | Credit | Block |
| DEL-001 | Delivery بدون SO/Production Release ممنوع | Matching | Block |
| AR-001 | مطالبات سررسید گذشته هشدار وصول ایجاد کند | SLA | Alert |
| BOM-001 | تغییر BOM بدون CR و Approval ممنوع | Engineering | Block |
| PROJ-001 | اجرای پروژه بدون Investment Approval ممنوع | Governance | Block |
| PROJ-002 | Budget overrun بیش از آستانه Escalate شود | Budget | Escalate |
| AUD-001 | تغییر قیمت/شرایط پرداخت حتماً Audit شود | Audit | Alert |
| SOD-001 | درخواست‌کننده و تأییدکننده نهایی یک نفر نباشند | SoD | Block |

## 14) ماتریس Error Detection Rules

| خطا | مرحله تشخیص | مکانیزم | نتیجه |
|---|---|---|---|
| خرید بدون تأیید | قبل از RFQ/PO | Workflow Rule | Block |
| PO بدون مقایسه پیشنهادها | قبل از Issue PO | Business Rule | Block |
| دریافت بدون PO | Receipt | Matching | Block/Exception |
| Invoice بدون GRN | AP Match | 3-way Match | Block |
| پرداخت بدون Match | Payment | Financial Control | Block |
| قیمت خرید غیرعادی | Evaluation | Variance Engine | Warning/Escalate |
| فروش زیر قیمت | SO Approval | Pricing Rule | Escalate |
| تأخیر تأمین‌کننده | Delivery Tracking | Date Rule | Alert |
| تأخیر کاربر | هر Task | SLA Engine | Alert/Escalate |
| تغییر غیرمجاز قیمت | Update Event | Audit Rule | Alert |
| تغییر BOM بدون Approval | Change Event | Engineering Rule | Block |
| پروژه خارج از بودجه | Monthly/Real-time | Budget Rule | Escalate |

## 15) مدل تشخیص مسئول خطا

### طبقه‌بندی علت‌ها
- User Error
- Process Error
- System Error
- Supplier Delay
- Customer Delay
- Management Approval Delay
- Missing Information
- External Constraint

### داده‌های لازم برای تحلیل مسئولیت
- فرآیند
- شیء/سند
- مرحله ایجاد خطا
- مرحله کشف خطا
- نقش مسئول در زمان وقوع
- SLA و Delay Days
- علت اولیه
- علت ریشه‌ای
- اقدام اصلاحی
- تصمیم کنترلی: Block / Warning / Escalation / Exception

## 16) SLA Model

### اجزای SLA
- `sla_code`
- `process`
- `stage`
- `base_duration`
- `duration_unit`: hour/day
- `working_calendar`
- `pause_conditions`
- `escalation_profile`
- `breach_action`

### نمونه SLAهای قابل پیکربندی
| مرحله | مقدار نمونه | یادداشت |
|---|---|---|
| PR Review | 1 روز کاری | Configurable |
| Supplier Evaluation | 2 روز کاری | Configurable |
| Quotation Analysis | 2 روز کاری | Configurable |
| Approval | 1 روز کاری | Configurable |
| PO Issue | 1 روز کاری | Configurable |
| QC | طبق استاندارد کالا | Configurable |
| Invoice Match | 1 روز کاری | Configurable |

## 17) Escalation Engine

### منطق Escalation
```text
On Task Created -> Set Due Date
If T-Reminder reached -> Notify Owner
If Due Date passed -> Level 1 Reminder
If Breach + X hours/days -> Level 2 Supervisor
If Breach + Y -> Level 3 Process Owner
If Breach + Z -> Level 4 Management
All escalations -> Audit Trail
```

### اجزای پیکربندی
- Trigger time
- Recipients by role
- Channel: in-app / email / SMS / Teams
- Severity
- Auto-hold / Auto-escalate / Auto-reassign

## 18) RACI سطح کلان

| فعالیت | Requester | Dept Mgr | Procurement | Technical | Warehouse | QC | Finance/AP | Sales | PMO/PM | Mgmt |
|---|---|---|---|---|---|---|---|---|---|---|
| Create PR | R | A | C | C | I | I | I | I | I | I |
| Approve PR | I | A | C | C | I | I | C | I | I | I |
| Create RFQ | I | I | R/A | C | I | I | I | I | I | I |
| Evaluate Quotations | I | I | R | C/A | I | I | C | I | I | I |
| Issue PO | I | I | R | C | I | I | A | I | I | I |
| Receive Goods | I | I | I | I | R/A | C | I | I | I | I |
| Perform QC | I | I | I | C | I | R/A | I | I | I | I |
| Match Invoice | I | I | C | I | C | C | R/A | I | I | I |
| Approve Price | I | I | C | I | I | I | A | R | I | C |
| Create SO | I | I | I | I | I | I | C | R/A | I | I |
| Project Approval | I | I | C | C | I | I | C | I | R | A |

## 19) SoD Matrix

| نقش 1 | نقش 2 | وضعیت |
|---|---|---|
| Requester | Final Approver همان سند | ممنوع |
| Buyer | Goods Receiver همان PO | ممنوع |
| Goods Receiver | QC Approver همان Receipt | ممنوع |
| AP Matcher | Payment Executor همان سند | ممنوع |
| Sales Creator | Discount Final Approver همان SO | ممنوع |
| Project Requester | Budget Final Approver همان CR/Project | ممنوع |
| Master Data Admin | Audit Log Admin | ممنوع |

## 20) DOA Matrix پیشنهادی

> اعداد صرفاً نمونه‌اند و باید به‌صورت Configurable Parameter نگهداری شوند.

| دامنه | تا سقف 1 | سقف 2 | سقف 3 | بالاتر |
|---|---|---|---|---|
| خرید | سرپرست واحد | مدیر واحد | مدیر مالی/عملیاتی | مدیرعامل/کمیته |
| فروش زیر کف | مدیر فروش | مدیر فروش + مالی | COO/CFO | CEO |
| پروژه CAPEX | مدیر پروژه | PMO + مالی | کمیته سرمایه‌گذاری | هیئت‌مدیره |
| Change Budget | مدیر واحد | مالی + Sponsor | CFO/COO | CEO/Board |

---

# Phase 3 — Data Architecture

## 21) معماری داده

### گروه‌بندی موجودیت‌ها
1. **Security & Org**: Users, Roles, Permissions, Departments, UserRoles
2. **Workflow Core**: WorkflowDefinitions, WorkflowStates, WorkflowTransitions, WorkflowInstances, WorkflowTasks, Approvals
3. **Master Data**: Suppliers, Customers, Materials, Products, BOM
4. **Procurement**: PurchaseRequests, RFQs, Quotations, PurchaseOrders, GoodsReceipts, QualityInspections
5. **Sales & Finance**: PriceLists, SalesOrders, Deliveries, Invoices, Payments, Collections
6. **Production & Costing**: ProductionOrders, MaterialIssues, CostSheets, CostElements
7. **Projects & Changes**: Projects, Milestones, ChangeRequests, Exceptions
8. **Control & Analytics**: Alerts, AuditLogs, KPI

## 22) Traceability Model

### زنجیره خرید
`PurchaseRequest -> RFQ -> SupplierQuotation -> Evaluation -> PurchaseOrder -> GoodsReceipt -> QualityInspection -> SupplierInvoice -> Payment`

### زنجیره فروش
`CustomerInquiry -> Pricing -> SalesQuotation -> SalesOrder -> ProductionOrder/Allocation -> Delivery -> CustomerInvoice -> Collection -> Profitability`

### زنجیره پروژه
`Idea -> Feasibility -> BusinessCase -> InvestmentApproval -> Project -> Procurement Package -> Milestone -> Commissioning -> PIR`

### اصل کلیدی دیتامدل
هر سند باید این فیلدها را داشته باشد:
- `id`
- `code`
- `status`
- `workflow_instance_id`
- `parent_document_type`
- `parent_document_id`
- `created_by`
- `created_at`
- `modified_by`
- `modified_at`

## 23) موجودیت‌ها و فیلدهای کلیدی

| Entity | PK | FKهای مهم | فیلدهای ضروری |
|---|---|---|---|
| Users | id | department_id | username, full_name, status |
| Roles | id | - | code, name, status |
| Permissions | id | - | resource, action |
| Departments | id | parent_id | code, name |
| WorkflowDefinitions | id | - | code, process_name, version |
| WorkflowInstances | id | workflow_definition_id | object_type, object_id, current_state, current_owner |
| WorkflowTasks | id | workflow_instance_id | task_type, assigned_to, due_at, status |
| Approvals | id | workflow_task_id | approver_id, decision, decided_at |
| Suppliers | id | - | code, name, approval_status, risk_level |
| Customers | id | - | code, name, credit_limit, payment_terms |
| Materials | id | - | code, uom, category, status |
| Products | id | - | code, family, standard_cost, min_price |
| BOMHeaders | id | product_id | revision_no, status, effective_from |
| BOMItems | id | bom_header_id, material_id | qty, scrap_factor |
| PurchaseRequests | id | requester_id, department_id | code, need_date, budget_status, status |
| RFQs | id | purchase_request_id | code, close_date, status |
| SupplierQuotations | id | rfq_id, supplier_id | quoted_at, currency, total_amount |
| PurchaseOrders | id | supplier_id, purchase_request_id | code, order_date, delivery_date, status |
| GoodsReceipts | id | purchase_order_id | code, receipt_date, warehouse_id, status |
| QualityInspections | id | goods_receipt_id | result, inspected_at, status |
| SupplierInvoices | id | purchase_order_id, goods_receipt_id | invoice_no, invoice_date, amount |
| Payments | id | supplier_invoice_id | payment_date, amount, status |
| CostSheets | id | product_id, production_order_id | standard_cost, actual_cost, variance |
| PriceLists | id | product_id, customer_id | pricing_method, proposed_price, approved_min_price |
| SalesOrders | id | customer_id | code, order_date, requested_date, status |
| Deliveries | id | sales_order_id | code, delivery_date, status |
| CustomerInvoices | id | sales_order_id, delivery_id | invoice_no, amount, status |
| Collections | id | customer_invoice_id | receipt_date, amount, status |
| Projects | id | sponsor_id, project_manager_id | code, capex_budget, status |
| ProjectMilestones | id | project_id | name, baseline_date, actual_date, status |
| ChangeRequests | id | related_object_type, related_object_id | reason, impact_summary, status |
| Exceptions | id | related_object_type, related_object_id | exception_type, justification, status |
| Alerts | id | related_object_type, related_object_id | alert_type, severity, due_at |
| AuditLogs | id | user_id | entity_name, entity_id, action, old_value, new_value |
| KPI | id | owner_role_id | kpi_code, value, as_of_date |

## 24) قواعد مدل داده
- همه اسناد دارای `status` و `workflow_instance_id` هستند.
- حذف فیزیکی برای اسناد تراکنشی و Audit ممنوع؛ فقط Soft Delete یا Inactive.
- مقادیر حساس مانند قیمت، شرایط پرداخت، سقف اعتبار، BOM revision باید نسخه‌دار باشند.
- تغییر Master Data حساس از مسیر Approval یا Change Request عبور می‌کند.
- اسناد بین‌فرآیندی با Reference Table یا Parent/Child Links متصل می‌شوند.

## 25) شاخص‌های فنی دیتابیس
- کلید اصلی: UUID یا BIGINT Sequence
- ایندکس اجباری بر روی `code`, `status`, `created_at`, `workflow_instance_id`, FKها
- ایندکس ترکیبی برای گزارش‌های پرتکرار: `(status, current_owner)`, `(supplier_id, status)`, `(customer_id, due_date)`
- Partition پیشنهادی برای AuditLogs، Alerts، Task History در مقیاس بالا
- Audit immutable در لایه DB و Application

> اسکیما تفصیلی در فایل `docs/database_schema.sql` ارائه شده است.

---

# Phase 4 — UI/UX & Screen Specification

## 26) اصول UX
- Inbox محور: هر کاربر ابتدا **My Tasks** را ببیند.
- از هر سند، **Timeline و Linked Documents** قابل مشاهده باشد.
- وضعیت، SLA، مسئول جاری و Block Reason همیشه در Header صفحه نمایش داده شود.
- اقدامات نامجاز نمایش داده نشود؛ حتی اگر نمایش داده شد، سرور باید آن را رد کند.
- فرم‌ها Context-Aware باشند: فیلدهای اضافی بر اساس نوع فرآیند فعال شوند.

## 27) فهرست صفحات اصلی

### Core
1. Login
2. Home Dashboard
3. My Tasks
4. My Alerts
5. Workflow Inbox
6. Approval Center
7. Document Timeline / Traceability View
8. Search & Global Registry

### Master Data
9. Users
10. Roles
11. Permissions
12. Departments
13. Suppliers
14. Customers
15. Materials
16. Products
17. BOM
18. Cost Centers

### Procurement
19. PR List
20. PR Create/Edit/View
21. RFQ List
22. RFQ Create/View
23. Quotation Entry & Comparison
24. Commercial Evaluation
25. Technical Evaluation
26. PO List
27. PO Create/View
28. Goods Receipt
29. QC Inspection
30. Supplier Invoice Match
31. Payment Approval

### Costing / Pricing / Sales
32. Production Orders
33. Cost Sheet
34. Price Proposal
35. Price Approval
36. Sales Order
37. Delivery
38. Customer Invoice
39. Collection / Receivables Follow-up
40. Profitability Analysis

### Projects / Control
41. Project Register
42. Project Detail & Milestones
43. Change Request
44. Exception Register
45. Alert Console
46. Audit Trail Viewer
47. KPI Dashboard
48. Settings / Rules / SLA / DOA

## 28) مشخصات اطلاعاتی هدر هر سند
- Document Code
- Process Name
- Status
- Current Owner
- Current Role
- Due Date / Overdue Days
- Financial Impact
- Blocking Issues Count
- Linked Documents Count
- Audit Trail Shortcut

## 29) نقش‌ها
- System Admin
- Master Data Admin
- Requester
- Department Manager
- Procurement Officer
- Procurement Manager
- Technical Evaluator
- Warehouse Receiver
- QC Inspector
- AP Accountant
- Treasury Officer
- Cost Accountant
- Pricing Analyst
- Sales Officer
- Sales Manager
- Credit Controller
- Project Manager
- PMO
- Internal Auditor
- Executive Management

## 30) Permission Matrix سطح بالا

| ماژول/اقدام | View | Create | Edit | Submit | Approve | Reject | Return | Cancel | Export | Admin |
|---|---|---|---|---|---|---|---|---|---|---|
| PR | ✔ | ✔ | محدود تا Draft | ✔ | Mgr | Mgr | Mgr | محدود | ✔ | Admin |
| RFQ | ✔ | Procurement | Draft only | ✔ | Procurement Mgr | ✔ | ✔ | محدود | ✔ | Admin |
| PO | ✔ | Procurement | قبل از Issue | ✔ | Finance/DOA | ✔ | ✔ | با کنترل | ✔ | Admin |
| GRN | ✔ | Warehouse | همان روز | ✔ | Warehouse Lead | - | - | محدود | ✔ | Admin |
| QC | ✔ | QC | تا قبل از Finalize | ✔ | QC Lead | ✔ | ✔ | محدود | ✔ | Admin |
| Costing | ✔ | Costing | تا Approval | ✔ | Finance | ✔ | ✔ | محدود | ✔ | Admin |
| Pricing | ✔ | Pricing | تا Approval | ✔ | Sales/Finance/CEO | ✔ | ✔ | محدود | ✔ | Admin |
| SO | ✔ | Sales | تا Confirm | ✔ | Sales Mgr | ✔ | ✔ | محدود | ✔ | Admin |
| Project | ✔ | PMO/PM | طبق Stage | ✔ | Sponsor/Committee | ✔ | ✔ | محدود | ✔ | Admin |
| Audit Log | محدود | - | - | - | - | - | - | - | محدود | Audit Admin |

> کنترل دسترسی نهایی بر مبنای **Role + Department + Process + Document + Status** اعمال می‌شود.

---

# Phase 5 — Dashboard / Alert / Escalation

## 31) داشبوردهای مدیریتی

### Executive Dashboard
- Open items by process and stage
- Total overdue count and financial exposure
- Purchase pipeline value
- Sales pipeline and margin at risk
- Receivables overdue aging
- Project budget/schedule variance
- Top 10 blocked cases

### Procurement Dashboard
- Open PR, RFQ, PO
- PO overdue by supplier
- Price variance by category
- Emergency purchases
- PR without action
- Receipts pending QC
- Invoices pending match

### Production Dashboard
- Production plan adherence
- Capacity load
- Material shortage
- Scrap and rework
- Standard vs actual cost variance

### Sales Dashboard
- Open quotations
- Orders pending price approval
- Orders on credit hold
- Revenue, GM%, Net Margin
- Customer profitability
- Overdue receivables

### Finance Dashboard
- Payables due
- Receivables due
- Cash requirement forecast
- Blocked payments
- Collection efficiency

### Project Dashboard
- Budget baseline vs actual
- Schedule baseline vs actual
- Milestones overdue
- Open risks/issues
- Change requests impact

## 32) داشبورد فرآیندی

نمونه برای خرید:
```text
کل درخواست‌ها: 128
43 در انتظار تأیید
22 در استعلام
17 در ارزیابی
12 در انتظار PO
8 در انتظار دریافت
4 در QC
7 در پرداخت
```

قابلیت Drill-down اجباری:
- کلیک روی هر عدد → لیست رکوردها
- کلیک روی رکورد → Traceability, Current Owner, Delay, Root Cause, Amount

## 33) داشبورد شخصی کاربر
- وظایف امروز
- وظایف Overdue
- وظایف آینده
- موارد برگشتی
- موارد نیازمند اصلاح
- هشدارهای مرتبط با نقش
- میانگین زمان رسیدگی شخصی

## 34) Alert Engine

### انواع Alert
- SLA Overdue
- Missing Approval
- Budget Overrun
- Price Variance
- Credit Limit Exceeded
- Delivery Delay
- QC Rejection
- 3-way Match Failure
- Unusual Discount
- Emergency Purchase Review Pending
- Project Milestone Delay
- Unauthorized Change Attempt

### ساختار Alert
- alert_code
- source_process
- source_document
- severity
- alert_owner
- generated_at
- reason
- financial_impact
- due_at
- resolution_status

## 35) Escalation Profiles

| پروفایل | سطح 1 | سطح 2 | سطح 3 | سطح 4 |
|---|---|---|---|---|
| Approval Delay | Owner | Supervisor | Process Owner | Management |
| Supplier Delay | Buyer | Procurement Manager | Ops/Planning | Management |
| Credit Breach | Sales | Credit Control | Finance Head | CEO |
| Project Delay | PM | PMO | Sponsor | Committee |

## 36) KPI Dictionary

| KPI | تعریف | فرمول |
|---|---|---|
| PR Cycle Time | زمان از ایجاد تا Approval | ApprovedAt - CreatedAt |
| RFQ Response Rate | نرخ پاسخ تأمین‌کنندگان | پاسخ / دعوت |
| PO On-Time Delivery | درصد تحویل به‌موقع | OnTime / Total PO |
| QC Rejection Rate | درصد مردودی QC | Rejected Qty / Inspected Qty |
| 3-Way Match Success | نرخ تطبیق موفق | Matched / Invoices |
| Purchase Price Variance | انحراف قیمت خرید | (Current - Benchmark) / Benchmark |
| Cost Variance | انحراف بهای تمام‌شده | Actual - Standard |
| Margin Variance | انحراف سود | Actual Margin - Planned Margin |
| DSO | روزهای وصول مطالبات | AR / Avg Daily Sales |
| Project Cost Variance | انحراف هزینه پروژه | Actual - Budget |
| Project Schedule Variance | انحراف زمان پروژه | Actual Progress - Planned |

---

# Phase 6 — Excel Advanced Prototype

## 37) معماری Workbook

### Sheet Structure
1. Dashboard
2. Workflow
3. Users
4. Roles
5. Suppliers
6. Customers
7. Materials
8. Products
9. BOM
10. PR
11. RFQ
12. Quotations
13. Purchase Orders
14. Receipts
15. QC
16. Costing
17. Pricing
18. Sales Orders
19. Delivery
20. Invoices
21. Payments
22. Projects
23. Approvals
24. Exceptions
25. Alerts
26. Audit Trail
27. KPI
28. Settings

## 38) قواعد طراحی Excel
- هر Sheet یک Table رسمی با نام یکتا داشته باشد
- کلیدها با Prefix تعریف شوند: PR-000001, PO-000001, SO-000001
- روابط از طریق ID نه فقط متن آزاد
- Data Validation برای Status, Role, Supplier, Customer, Product
- Conditional Formatting برای Overdue / Blocked / Exception
- Pivot و Dashboard فقط از جداول ساختاریافته تغذیه شوند
- ستون‌های سیستمی ثابت: `ID, Status, CreatedBy, CreatedAt, ModifiedBy, ModifiedAt`
- Sheet Workflow وضعیت جاری و مرحله بعد را برای هر سند نگهداری کند
- Sheet Settings شامل Thresholdها، SLAها، DOA و لیست‌های مرجع باشد

## 39) محدودیت‌های نسخه Excel
- مناسب MVP و کنترل‌های نیمه‌متمرکز
- Rule Engine پیچیده محدود است
- همزمانی کاربران ضعیف است
- Audit قابل اعتمادتر از فرم آزاد است ولی در سطح Enterprise نیست
- برای Hard Control کامل نیاز به نسخه Server وجود دارد

---

# Phase 7 — Server Application Architecture

## 40) سطوح نسخه‌بندی

| Level | بستر | قابلیت‌ها | محدودیت‌ها |
|---|---|---|---|
| Level 1 | Excel Advanced Prototype | ثبت ساختاریافته، داشبورد پایه، Traceability اولیه | کنترل سروری ندارد، همزمانی محدود |
| Level 2 | Web App / Internal Server | Workflow Engine, Rule Engine, RBAC, Audit, Alerts, Dashboards | Integration محدودتر از ERP کامل |
| Level 3 | Enterprise / ERP Integration | API/ESB, SSO, Accounting, MES/WMS/CRM Integration, High Availability | پیچیدگی و هزینه بالاتر |

## 41) معماری منطقی نسخه Server

### Frontend
- Web SPA برای کاربران عملیاتی و مدیریتی
- صفحه Inboxes, Dashboards, Document Detail, Timeline, Rule Violations

### Backend Services
- Identity Service
- Master Data Service
- Workflow Service
- Rule Engine Service
- Procurement Service
- Inventory & QC Service
- Costing Service
- Pricing Service
- Sales & Credit Service
- Finance Match & Payment Service
- Project Service
- Alert & Notification Service
- Audit Service
- Reporting Service

### Data Layer
- RDBMS اصلی برای تراکنش‌ها
- Object Storage برای پیوست‌ها
- Cache برای داشبورد و Read Models
- Search Index برای جستجوی سراسری

## 42) الگوی فنی پیشنهادی
- API-first
- Transactional integrity در عملیات مالی/تأییدی
- Event-driven برای Alerts, Notifications, KPI snapshots
- CQRS سبک برای Dashboardها در صورت نیاز مقیاس
- Immutable audit log
- Server-side validation اجباری

## 43) امنیت
- Authentication: SSO/AD/OIDC یا Local Secure Auth
- Authorization: RBAC + ABAC سبک بر پایه Department/Status
- Password Policy: طول، پیچیدگی، چرخش، قفل حساب
- Session Management: timeout, device/IP logging
- Encryption: TLS in transit + DB encryption at rest for sensitive data
- File Security: malware scan, MIME validation, access tokenized download
- Database Security: least privilege, audit on DDL/DML حساس
- Backup/Restore: روزانه + تست Restore دوره‌ای
- Change Tracking: نسخه‌سازی اسناد حساس
- Anti-bypass: همه Ruleها در API enforce شوند

## 44) MVP پیشنهادی

### ماژول‌های MVP
1. User Management
2. Workflow
3. PR
4. Supplier
5. RFQ
6. Quotation
7. Purchase Approval
8. PO
9. Receipt
10. QC
11. Invoice Matching
12. Costing
13. Pricing
14. Sales Order
15. Dashboard
16. Alert
17. Audit Trail

### ترتیب اجرای MVP
- Wave 1: Identity, Master Data, Workflow Core
- Wave 2: Procurement E2E
- Wave 3: QC + Match + Basic Finance Control
- Wave 4: Costing + Pricing + Sales Order
- Wave 5: Dashboards + Alerts + Audit Hardening

---

# Phase 8 — Testing & Acceptance

## 45) Acceptance Criteria ماژول‌ها

### Purchase
- PR ایجاد، Submit و Approval شود.
- RFQ فقط پس از Approval ایجاد شود.
- حداقل تعداد استعلام طبق Policy کنترل شود.
- Quotation ثبت و مقایسه شود.
- Price approval طبق Threshold عمل کند.
- PO فقط برای Supplier معتبر صادر شود.
- Receipt با PO مرتبط ثبت شود.
- QC نتیجه Pass/Reject داشته باشد.
- Invoice Match انجام شود.
- Payment بدون Match ممکن نباشد.
- Traceability از PR تا Payment کامل باشد.

### Pricing & Sales
- Price Proposal بر اساس Cost Method ایجاد شود.
- فروش زیر کف قیمت Escalate شود.
- Credit control قبل از تأیید SO اعمال شود.
- Delivery بدون SO معتبر ممکن نباشد.
- Invoice و Collection قابل ردیابی باشند.

### Projects
- Project بدون Investment Approval شروع نشود.
- Budget و Milestone Baseline ثبت شود.
- تغییرات از مسیر CR عبور کند.
- Varianceها خودکار محاسبه شوند.

## 46) سناریوهای تست (30 مورد)

| # | سناریو | Input | Expected Workflow | Expected Control | Expected Result |
|---|---|---|---|---|---|
| 1 | خرید عادی | PR کامل و بودجه‌دار | PR→RFQ→Quote→PO→GRN→QC→Match→Pay | Rules عادی | موفق و Closed |
| 2 | PR ناقص | بدون مرکز هزینه | Draft→Submit | Validation | Block |
| 3 | خرید بدون بودجه | PR با Budget Exceed | PR→Review | Budget Rule | Block/Exception |
| 4 | خرید اضطراری | Emergency Flag | Emergency Flow | Emergency Approval | مسیر اضطراری کنترل‌شده |
| 5 | RFQ قبل از Approval | PR تأییدنشده | PR→RFQ | Precondition | Block |
| 6 | تعداد استعلام کم | فقط 1 پیشنهاد | RFQ→Quote | Policy Rule | Block/Exception |
| 7 | Supplier جدید | Supplier not approved | Quote→PO | Supplier Approval Rule | Block تا تأیید |
| 8 | Supplier ردشده | Status=Rejected | PO Issue | Master Rule | Block |
| 9 | اختلاف قیمت بالا | Variance > Threshold | Evaluation→Approval | Threshold Rule | Escalation |
| 10 | PO بدون Evaluation | تلاش برای Issue | Quote→PO | Workflow Rule | Block |
| 11 | دریافت بدون PO | GRN مستقل | Receipt | Matching | Block |
| 12 | اختلاف مقدار دریافت | Qty > PO tolerance | GRN | Quantity Tolerance | Exception/Hold |
| 13 | QC Reject | QC=Fail | GRN→QC | Quality Rule | No inventory release |
| 14 | Invoice بدون GRN | Invoice only | AP Match | 3-way Match | Block |
| 15 | Payment بدون Match | Manual payment | Payment | Financial Control | Block |
| 16 | تأخیر تأمین‌کننده | Delivery date passed | PO Open | SLA/Date | Alert |
| 17 | تأخیر کاربر | Task overdue | Any | Escalation | Multi-level notify |
| 18 | Cost Sheet ناقص | Missing overhead | Costing Approval | Calculation Rule | Block |
| 19 | قیمت‌گذاری بدون Cost Approval | Proposed price | Pricing | Precondition | Block |
| 20 | فروش زیر حد مجاز | Price < Min | SO Approval | Pricing DOA | Escalation |
| 21 | مشتری بدهکار | Credit exceeded | SO Confirm | Credit Rule | Hold/Block |
| 22 | Delivery بدون SO | Delivery create | Delivery | Matching | Block |
| 23 | تغییر قیمت پس از Approval | Update approved price | Update Event | Audit Rule | Alert + version |
| 24 | تغییر BOM بدون CR | BOM edit direct | Engineering | Change Rule | Block |
| 25 | پروژه جدید عادی | Idea کامل | Idea→PIR | Project Flow | Success |
| 26 | افزایش بودجه پروژه | Budget change | CR Flow | Change Rule | Approval required |
| 27 | تأخیر پروژه | Milestone delayed | Execution | SLA/Variance | Escalation |
| 28 | لغو سفارش خرید | Cancel request | PR/PO | Status + approval | Controlled cancel |
| 29 | اصلاح سند | Return for correction | Any stage | Return action | Back to owner |
| 30 | تلاش برای دور زدن UI | API direct call | Any blocked transition | Server Rule | Hard Block + Audit |

## 47) پاسخ به آزمون نهایی ضدخطا

### سؤال 1
**اگر کاربر عمداً یا سهواً بخواهد ترتیب فرآیند را دور بزند، آیا سامانه واقعاً جلوی او را می‌گیرد؟**

**پاسخ طراحی‌شده: بله، در موارد کلیدی باید Hard Control داشته باشد، نه صرفاً Warning.**

#### Hard Blocking Ruleهای اجباری
- RFQ بدون PR Approved → Block
- PO بدون Evaluation/Approval → Block
- Receipt بدون PO/Exception Approved → Block
- Inventory Release برای QC Rejected → Block
- Payment بدون Match → Block
- Price Release بدون Cost Approval → Block
- Sales Order بالاتر از Credit Limit بدون Approval → Block/Hold
- BOM Change بدون CR Approved → Block
- Project Execution بدون Investment Approval → Block

### سؤال 2
**اگر مدیرعامل بخواهد بداند این سفارش خرید دقیقاً دست چه کسی است، چند روز است متوقف شده، چرا متوقف شده، چه کسی باید اقدام کند و اثر مالی آن چیست، آیا سامانه در چند ثانیه پاسخ می‌دهد؟**

**پاسخ طراحی‌شده: بله.** به‌شرط پیاده‌سازی این داده‌ها در Read Model / Dashboard View:
- Current State
- Current Owner
- Current Owner Role
- Due Date / Overdue Days
- Hold Reason / Block Reason
- Next Action
- Escalation Level
- Linked Documents
- Amount / Currency / Financial Impact
- Audit Timeline

این داده‌ها باید در نمای Summary هر Workflow Object ذخیره یا Cache شوند تا پاسخ در چند ثانیه ممکن باشد.

---

## جمع‌بندی اجرایی
این طراحی سامانه را از حالت «ثبت فرم و ارجاع دستی» خارج کرده و به یک **سامانه کنترل فرآیند، کنترل مجوز، کنترل خطا، کنترل زمان و کنترل اثر مالی** تبدیل می‌کند. معیار اصلی پذیرش آن این است که برای هر رکورد در هر لحظه بتوان مشخص کرد:

- چه چیزی؟
- دست چه کسی است؟
- در چه وضعیتی است؟
- چرا متوقف شده؟
- مرحله بعد چیست؟
- آیا تأخیر دارد؟
- آیا خطا دارد؟
- اثر مالی آن چیست؟
- کدام اسناد قبل و بعد به آن متصل‌اند؟
- چه کسی آن را تغییر داده است؟
- و نتیجه واقعی چه بوده است؟
