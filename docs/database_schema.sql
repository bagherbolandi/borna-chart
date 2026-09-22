-- PostgreSQL logical schema for the enterprise process-control platform
-- Scope: workflow, procurement, sales, costing, projects, alerts, audit

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- 1) SECURITY & ORG
-- =========================

CREATE TABLE departments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id uuid REFERENCES departments(id),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(200) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(200) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    resource varchar(100) NOT NULL,
    action varchar(50) NOT NULL,
    description text,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(resource, action)
);

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id uuid REFERENCES departments(id),
    username varchar(100) NOT NULL UNIQUE,
    full_name varchar(200) NOT NULL,
    email varchar(200),
    mobile varchar(50),
    password_hash text,
    auth_source varchar(30) NOT NULL DEFAULT 'local',
    is_locked boolean NOT NULL DEFAULT false,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE user_roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id),
    role_id uuid NOT NULL REFERENCES roles(id),
    department_id uuid REFERENCES departments(id),
    valid_from date,
    valid_to date,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(user_id, role_id, department_id)
);

CREATE TABLE role_permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id uuid NOT NULL REFERENCES roles(id),
    permission_id uuid NOT NULL REFERENCES permissions(id),
    effect varchar(20) NOT NULL DEFAULT 'allow',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(role_id, permission_id)
);

-- =========================
-- 2) WORKFLOW CORE
-- =========================

CREATE TABLE workflow_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    process_name varchar(200) NOT NULL,
    object_type varchar(100) NOT NULL,
    version_no integer NOT NULL DEFAULT 1,
    is_active boolean NOT NULL DEFAULT true,
    description text,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_states (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id uuid NOT NULL REFERENCES workflow_definitions(id),
    state_code varchar(50) NOT NULL,
    state_name varchar(200) NOT NULL,
    state_type varchar(30) NOT NULL DEFAULT 'normal',
    is_initial boolean NOT NULL DEFAULT false,
    is_final boolean NOT NULL DEFAULT false,
    sla_hours integer,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(workflow_definition_id, state_code)
);

CREATE TABLE workflow_transitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id uuid NOT NULL REFERENCES workflow_definitions(id),
    from_state_id uuid NOT NULL REFERENCES workflow_states(id),
    to_state_id uuid NOT NULL REFERENCES workflow_states(id),
    action_code varchar(50) NOT NULL,
    action_name varchar(200) NOT NULL,
    requires_approval boolean NOT NULL DEFAULT false,
    rule_expression text,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workflow_instances (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_definition_id uuid NOT NULL REFERENCES workflow_definitions(id),
    object_type varchar(100) NOT NULL,
    object_id uuid NOT NULL,
    current_state_id uuid REFERENCES workflow_states(id),
    current_owner_user_id uuid REFERENCES users(id),
    current_owner_role_id uuid REFERENCES roles(id),
    priority varchar(20) NOT NULL DEFAULT 'normal',
    due_at timestamptz,
    completed_at timestamptz,
    risk_level varchar(20) NOT NULL DEFAULT 'medium',
    financial_impact numeric(18,2) NOT NULL DEFAULT 0,
    hold_reason text,
    exception_flag boolean NOT NULL DEFAULT false,
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(object_type, object_id)
);

CREATE TABLE workflow_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_instance_id uuid NOT NULL REFERENCES workflow_instances(id),
    state_id uuid REFERENCES workflow_states(id),
    task_code varchar(50),
    task_type varchar(50) NOT NULL,
    assigned_user_id uuid REFERENCES users(id),
    assigned_role_id uuid REFERENCES roles(id),
    assigned_department_id uuid REFERENCES departments(id),
    opened_at timestamptz NOT NULL DEFAULT now(),
    due_at timestamptz,
    closed_at timestamptz,
    escalation_level integer NOT NULL DEFAULT 0,
    outcome varchar(30),
    status varchar(30) NOT NULL DEFAULT 'open',
    comments text,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE approvals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_task_id uuid REFERENCES workflow_tasks(id),
    object_type varchar(100) NOT NULL,
    object_id uuid NOT NULL,
    approval_stage varchar(50) NOT NULL,
    approver_user_id uuid NOT NULL REFERENCES users(id),
    approver_role_id uuid REFERENCES roles(id),
    decision varchar(20) NOT NULL,
    decision_note text,
    decided_at timestamptz,
    delegated_from_user_id uuid REFERENCES users(id),
    status varchar(30) NOT NULL DEFAULT 'completed',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE business_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code varchar(50) NOT NULL UNIQUE,
    process_name varchar(100) NOT NULL,
    object_type varchar(100) NOT NULL,
    event_name varchar(50) NOT NULL,
    severity varchar(20) NOT NULL,
    condition_expression text NOT NULL,
    error_message text NOT NULL,
    owner_role_id uuid REFERENCES roles(id),
    is_active boolean NOT NULL DEFAULT true,
    effective_from date,
    effective_to date,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sla_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sla_code varchar(50) NOT NULL UNIQUE,
    process_name varchar(100) NOT NULL,
    stage_code varchar(50) NOT NULL,
    duration_value integer NOT NULL,
    duration_unit varchar(20) NOT NULL,
    working_calendar varchar(50) NOT NULL DEFAULT 'default',
    escalation_profile_code varchar(50),
    is_active boolean NOT NULL DEFAULT true,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 3) MASTER DATA
-- =========================

CREATE TABLE suppliers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(250) NOT NULL,
    tax_id varchar(100),
    category varchar(100),
    approval_status varchar(30) NOT NULL DEFAULT 'pending',
    payment_terms varchar(100),
    lead_time_days integer,
    currency_code varchar(10),
    risk_level varchar(20) NOT NULL DEFAULT 'medium',
    quality_score numeric(5,2),
    delivery_score numeric(5,2),
    performance_score numeric(5,2),
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(250) NOT NULL,
    tax_id varchar(100),
    payment_terms varchar(100),
    credit_limit numeric(18,2) NOT NULL DEFAULT 0,
    credit_status varchar(30) NOT NULL DEFAULT 'open',
    risk_level varchar(20) NOT NULL DEFAULT 'medium',
    market_segment varchar(100),
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE materials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(250) NOT NULL,
    uom varchar(20) NOT NULL,
    material_type varchar(50) NOT NULL,
    category varchar(100),
    specification text,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(250) NOT NULL,
    family varchar(100),
    uom varchar(20) NOT NULL,
    standard_cost numeric(18,2) NOT NULL DEFAULT 0,
    approved_min_price numeric(18,2) NOT NULL DEFAULT 0,
    pricing_method varchar(50),
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE bom_headers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL REFERENCES products(id),
    revision_no varchar(30) NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    status varchar(30) NOT NULL DEFAULT 'draft',
    approved_by uuid REFERENCES users(id),
    approved_at timestamptz,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(product_id, revision_no)
);

CREATE TABLE bom_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bom_header_id uuid NOT NULL REFERENCES bom_headers(id) ON DELETE CASCADE,
    material_id uuid NOT NULL REFERENCES materials(id),
    operation_no integer,
    qty numeric(18,6) NOT NULL,
    scrap_factor numeric(10,4) NOT NULL DEFAULT 0,
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 4) PROCUREMENT
-- =========================

CREATE TABLE purchase_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    requester_user_id uuid NOT NULL REFERENCES users(id),
    department_id uuid NOT NULL REFERENCES departments(id),
    need_date date,
    request_type varchar(50) NOT NULL DEFAULT 'normal',
    budget_status varchar(30) NOT NULL DEFAULT 'pending',
    total_estimated_amount numeric(18,2) NOT NULL DEFAULT 0,
    currency_code varchar(10) NOT NULL DEFAULT 'IRR',
    reason text NOT NULL,
    priority varchar(20) NOT NULL DEFAULT 'normal',
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE purchase_request_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_request_id uuid NOT NULL REFERENCES purchase_requests(id) ON DELETE CASCADE,
    material_id uuid REFERENCES materials(id),
    product_id uuid REFERENCES products(id),
    description text NOT NULL,
    qty numeric(18,6) NOT NULL,
    uom varchar(20) NOT NULL,
    estimated_unit_price numeric(18,2),
    warehouse_code varchar(50),
    cost_center_code varchar(50) NOT NULL,
    project_id uuid,
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rfqs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    purchase_request_id uuid NOT NULL REFERENCES purchase_requests(id),
    issue_date date NOT NULL,
    close_date date,
    rfq_type varchar(30) NOT NULL DEFAULT 'standard',
    minimum_quote_count integer NOT NULL DEFAULT 3,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rfq_suppliers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id uuid NOT NULL REFERENCES rfqs(id) ON DELETE CASCADE,
    supplier_id uuid NOT NULL REFERENCES suppliers(id),
    invitation_status varchar(30) NOT NULL DEFAULT 'sent',
    response_status varchar(30) NOT NULL DEFAULT 'pending',
    invited_at timestamptz,
    responded_at timestamptz,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(rfq_id, supplier_id)
);

CREATE TABLE supplier_quotations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    rfq_id uuid NOT NULL REFERENCES rfqs(id),
    supplier_id uuid NOT NULL REFERENCES suppliers(id),
    quote_no varchar(100),
    quote_date date,
    currency_code varchar(10) NOT NULL,
    validity_date date,
    total_amount numeric(18,2) NOT NULL DEFAULT 0,
    commercial_score numeric(5,2),
    technical_score numeric(5,2),
    delivery_days integer,
    payment_terms varchar(100),
    is_selected boolean NOT NULL DEFAULT false,
    status varchar(30) NOT NULL DEFAULT 'received',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE supplier_quotation_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_quotation_id uuid NOT NULL REFERENCES supplier_quotations(id) ON DELETE CASCADE,
    purchase_request_line_id uuid REFERENCES purchase_request_lines(id),
    material_id uuid REFERENCES materials(id),
    description text,
    qty numeric(18,6) NOT NULL,
    unit_price numeric(18,2) NOT NULL,
    discount_amount numeric(18,2) NOT NULL DEFAULT 0,
    freight_amount numeric(18,2) NOT NULL DEFAULT 0,
    landed_cost numeric(18,2),
    price_variance_pct numeric(9,4),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE purchase_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    purchase_request_id uuid REFERENCES purchase_requests(id),
    rfq_id uuid REFERENCES rfqs(id),
    selected_quotation_id uuid REFERENCES supplier_quotations(id),
    supplier_id uuid NOT NULL REFERENCES suppliers(id),
    order_date date NOT NULL,
    delivery_date date,
    currency_code varchar(10) NOT NULL,
    payment_terms varchar(100),
    total_amount numeric(18,2) NOT NULL DEFAULT 0,
    price_variance_pct numeric(9,4),
    emergency_flag boolean NOT NULL DEFAULT false,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE purchase_order_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id uuid NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    purchase_request_line_id uuid REFERENCES purchase_request_lines(id),
    material_id uuid REFERENCES materials(id),
    description text NOT NULL,
    qty numeric(18,6) NOT NULL,
    received_qty numeric(18,6) NOT NULL DEFAULT 0,
    unit_price numeric(18,2) NOT NULL,
    line_amount numeric(18,2) NOT NULL,
    tax_amount numeric(18,2) NOT NULL DEFAULT 0,
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE goods_receipts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    purchase_order_id uuid NOT NULL REFERENCES purchase_orders(id),
    receipt_date date NOT NULL,
    warehouse_code varchar(50) NOT NULL,
    supplier_delivery_ref varchar(100),
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'received',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE goods_receipt_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    goods_receipt_id uuid NOT NULL REFERENCES goods_receipts(id) ON DELETE CASCADE,
    purchase_order_line_id uuid NOT NULL REFERENCES purchase_order_lines(id),
    material_id uuid REFERENCES materials(id),
    received_qty numeric(18,6) NOT NULL,
    accepted_qty numeric(18,6) NOT NULL DEFAULT 0,
    rejected_qty numeric(18,6) NOT NULL DEFAULT 0,
    batch_no varchar(100),
    status varchar(30) NOT NULL DEFAULT 'pending_qc',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quality_inspections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    goods_receipt_id uuid NOT NULL REFERENCES goods_receipts(id),
    inspection_date date NOT NULL,
    inspector_user_id uuid REFERENCES users(id),
    result varchar(20) NOT NULL,
    remarks text,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE quality_inspection_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    quality_inspection_id uuid NOT NULL REFERENCES quality_inspections(id) ON DELETE CASCADE,
    goods_receipt_line_id uuid NOT NULL REFERENCES goods_receipt_lines(id),
    criterion varchar(200) NOT NULL,
    result varchar(20) NOT NULL,
    defect_code varchar(50),
    corrective_action text,
    status varchar(30) NOT NULL DEFAULT 'recorded',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE supplier_invoices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    supplier_id uuid NOT NULL REFERENCES suppliers(id),
    purchase_order_id uuid REFERENCES purchase_orders(id),
    goods_receipt_id uuid REFERENCES goods_receipts(id),
    invoice_no varchar(100) NOT NULL,
    invoice_date date NOT NULL,
    due_date date,
    currency_code varchar(10) NOT NULL,
    total_amount numeric(18,2) NOT NULL,
    match_status varchar(30) NOT NULL DEFAULT 'pending',
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(supplier_id, invoice_no)
);

CREATE TABLE payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    supplier_invoice_id uuid NOT NULL REFERENCES supplier_invoices(id),
    payment_date date,
    amount numeric(18,2) NOT NULL,
    currency_code varchar(10) NOT NULL,
    payment_method varchar(50),
    bank_reference varchar(100),
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 5) PRODUCTION & COSTING
-- =========================

CREATE TABLE production_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    product_id uuid NOT NULL REFERENCES products(id),
    sales_order_id uuid,
    planned_qty numeric(18,6) NOT NULL,
    produced_qty numeric(18,6) NOT NULL DEFAULT 0,
    plan_start_date date,
    plan_end_date date,
    actual_start_at timestamptz,
    actual_end_at timestamptz,
    status varchar(30) NOT NULL DEFAULT 'planned',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE cost_sheets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    product_id uuid REFERENCES products(id),
    production_order_id uuid REFERENCES production_orders(id),
    costing_type varchar(30) NOT NULL,
    material_cost numeric(18,2) NOT NULL DEFAULT 0,
    labor_cost numeric(18,2) NOT NULL DEFAULT 0,
    machine_cost numeric(18,2) NOT NULL DEFAULT 0,
    energy_cost numeric(18,2) NOT NULL DEFAULT 0,
    overhead_cost numeric(18,2) NOT NULL DEFAULT 0,
    scrap_cost numeric(18,2) NOT NULL DEFAULT 0,
    rework_cost numeric(18,2) NOT NULL DEFAULT 0,
    packaging_cost numeric(18,2) NOT NULL DEFAULT 0,
    internal_logistics_cost numeric(18,2) NOT NULL DEFAULT 0,
    total_cost numeric(18,2) NOT NULL DEFAULT 0,
    standard_cost numeric(18,2) NOT NULL DEFAULT 0,
    actual_cost numeric(18,2) NOT NULL DEFAULT 0,
    estimated_cost numeric(18,2) NOT NULL DEFAULT 0,
    variance_amount numeric(18,2) NOT NULL DEFAULT 0,
    variance_pct numeric(9,4) NOT NULL DEFAULT 0,
    approved_by uuid REFERENCES users(id),
    approved_at timestamptz,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE price_lists (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    product_id uuid NOT NULL REFERENCES products(id),
    customer_id uuid REFERENCES customers(id),
    market_segment varchar(100),
    pricing_method varchar(50) NOT NULL,
    cost_basis numeric(18,2) NOT NULL DEFAULT 0,
    target_margin_pct numeric(9,4) NOT NULL DEFAULT 0,
    logistics_cost numeric(18,2) NOT NULL DEFAULT 0,
    financial_cost numeric(18,2) NOT NULL DEFAULT 0,
    risk_cost numeric(18,2) NOT NULL DEFAULT 0,
    proposed_price numeric(18,2) NOT NULL,
    approved_min_price numeric(18,2) NOT NULL,
    valid_from date NOT NULL,
    valid_to date,
    approved_by uuid REFERENCES users(id),
    approved_at timestamptz,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 6) SALES & COLLECTION
-- =========================

CREATE TABLE sales_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    customer_id uuid NOT NULL REFERENCES customers(id),
    order_date date NOT NULL,
    requested_delivery_date date,
    payment_terms varchar(100),
    currency_code varchar(10) NOT NULL,
    total_amount numeric(18,2) NOT NULL DEFAULT 0,
    credit_check_status varchar(30) NOT NULL DEFAULT 'pending',
    pricing_status varchar(30) NOT NULL DEFAULT 'pending',
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sales_order_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_order_id uuid NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    product_id uuid NOT NULL REFERENCES products(id),
    description text,
    qty numeric(18,6) NOT NULL,
    unit_price numeric(18,2) NOT NULL,
    min_approved_price numeric(18,2) NOT NULL,
    discount_pct numeric(9,4) NOT NULL DEFAULT 0,
    line_amount numeric(18,2) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE production_orders
    ADD CONSTRAINT fk_production_orders_sales_order
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id);

CREATE TABLE deliveries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    sales_order_id uuid NOT NULL REFERENCES sales_orders(id),
    delivery_date date,
    warehouse_code varchar(50),
    carrier_name varchar(100),
    proof_of_delivery_ref varchar(100),
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE delivery_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id uuid NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    sales_order_line_id uuid NOT NULL REFERENCES sales_order_lines(id),
    delivered_qty numeric(18,6) NOT NULL,
    status varchar(30) NOT NULL DEFAULT 'delivered',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customer_invoices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    customer_id uuid NOT NULL REFERENCES customers(id),
    sales_order_id uuid REFERENCES sales_orders(id),
    delivery_id uuid REFERENCES deliveries(id),
    invoice_no varchar(100) NOT NULL,
    invoice_date date NOT NULL,
    due_date date,
    currency_code varchar(10) NOT NULL,
    total_amount numeric(18,2) NOT NULL,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(customer_id, invoice_no)
);

CREATE TABLE collections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    customer_invoice_id uuid NOT NULL REFERENCES customer_invoices(id),
    receipt_date date,
    amount numeric(18,2) NOT NULL,
    currency_code varchar(10) NOT NULL,
    receipt_method varchar(50),
    bank_reference varchar(100),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 7) PROJECTS & CHANGES
-- =========================

CREATE TABLE projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(250) NOT NULL,
    project_type varchar(50) NOT NULL,
    sponsor_user_id uuid REFERENCES users(id),
    project_manager_user_id uuid REFERENCES users(id),
    baseline_budget numeric(18,2) NOT NULL DEFAULT 0,
    actual_cost numeric(18,2) NOT NULL DEFAULT 0,
    baseline_start_date date,
    baseline_end_date date,
    actual_start_date date,
    actual_end_date date,
    schedule_variance_days integer NOT NULL DEFAULT 0,
    budget_variance_amount numeric(18,2) NOT NULL DEFAULT 0,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'idea',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE project_milestones (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name varchar(200) NOT NULL,
    baseline_date date,
    actual_date date,
    owner_user_id uuid REFERENCES users(id),
    status varchar(30) NOT NULL DEFAULT 'planned',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE change_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    related_object_type varchar(100) NOT NULL,
    related_object_id uuid NOT NULL,
    requested_by_user_id uuid NOT NULL REFERENCES users(id),
    change_type varchar(50) NOT NULL,
    reason text NOT NULL,
    impact_summary text,
    impact_cost numeric(18,2) NOT NULL DEFAULT 0,
    impact_days integer NOT NULL DEFAULT 0,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'draft',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE exceptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    related_object_type varchar(100) NOT NULL,
    related_object_id uuid NOT NULL,
    exception_type varchar(50) NOT NULL,
    justification text NOT NULL,
    approver_user_id uuid REFERENCES users(id),
    approved_at timestamptz,
    workflow_instance_id uuid UNIQUE REFERENCES workflow_instances(id),
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 8) CONTROL & ANALYTICS
-- =========================

CREATE TABLE alerts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_code varchar(50) NOT NULL,
    related_object_type varchar(100) NOT NULL,
    related_object_id uuid NOT NULL,
    workflow_instance_id uuid REFERENCES workflow_instances(id),
    severity varchar(20) NOT NULL,
    alert_type varchar(50) NOT NULL,
    owner_user_id uuid REFERENCES users(id),
    owner_role_id uuid REFERENCES roles(id),
    generated_at timestamptz NOT NULL DEFAULT now(),
    due_at timestamptz,
    resolved_at timestamptz,
    resolution_note text,
    financial_impact numeric(18,2) NOT NULL DEFAULT 0,
    status varchar(30) NOT NULL DEFAULT 'open',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_time timestamptz NOT NULL DEFAULT now(),
    user_id uuid REFERENCES users(id),
    entity_name varchar(100) NOT NULL,
    entity_id uuid NOT NULL,
    action varchar(50) NOT NULL,
    field_name varchar(100),
    old_value text,
    new_value text,
    reason text,
    authorized_by uuid REFERENCES users(id),
    ip_address inet,
    session_id varchar(100),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE kpi_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_code varchar(50) NOT NULL UNIQUE,
    name varchar(200) NOT NULL,
    formula text NOT NULL,
    owner_role_id uuid REFERENCES roles(id),
    target_value numeric(18,4),
    frequency varchar(20) NOT NULL DEFAULT 'daily',
    status varchar(30) NOT NULL DEFAULT 'active',
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_by uuid,
    modified_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE kpi_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_definition_id uuid NOT NULL REFERENCES kpi_definitions(id),
    as_of_date date NOT NULL,
    dimension_1 varchar(100),
    dimension_2 varchar(100),
    metric_value numeric(18,4) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(kpi_definition_id, as_of_date, dimension_1, dimension_2)
);

-- =========================
-- 9) INDEXES
-- =========================

CREATE INDEX idx_workflow_instances_state_owner ON workflow_instances(current_state_id, current_owner_user_id, status);
CREATE INDEX idx_workflow_tasks_status_due ON workflow_tasks(status, due_at);
CREATE INDEX idx_purchase_requests_status ON purchase_requests(status, created_at);
CREATE INDEX idx_purchase_orders_supplier_status ON purchase_orders(supplier_id, status, delivery_date);
CREATE INDEX idx_goods_receipts_po_status ON goods_receipts(purchase_order_id, status);
CREATE INDEX idx_supplier_invoices_match_status ON supplier_invoices(match_status, due_date);
CREATE INDEX idx_sales_orders_customer_status ON sales_orders(customer_id, status, order_date);
CREATE INDEX idx_customer_invoices_due ON customer_invoices(customer_id, due_date, status);
CREATE INDEX idx_projects_status ON projects(status, baseline_end_date);
CREATE INDEX idx_alerts_open_owner ON alerts(status, owner_user_id, severity);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_name, entity_id, event_time);

-- =========================
-- 10) OPTIONAL GOVERNANCE NOTES
-- =========================
-- 1. Physical DELETE should be disallowed in application/service layer for transactional tables.
-- 2. Sensitive changes (price, BOM, payment terms, credit limit) should create audit_logs and usually change_requests.
-- 3. Workflow transitions must be validated in server-side rule engine before update.
-- 4. 3-way match uses purchase_orders + goods_receipts + supplier_invoices.
-- 5. Profitability analysis can be implemented with reporting views over sales_orders, customer_invoices, collections, cost_sheets.
