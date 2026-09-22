from fastapi import APIRouter

from app.api.routes import (
    alerts,
    approvals,
    audit,
    auth,
    collections,
    customers,
    dashboard,
    goods_receipts,
    health,
    inbox,
    payments,
    pricing,
    products,
    purchase_orders,
    purchase_requests,
    quality_inspections,
    registry,
    rfqs,
    sales_deliveries,
    sales_invoices,
    sales_orders,
    scheduler,
    security_incidents,
    security_ops,
    supplier_invoices,
    suppliers,
    traceability,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(registry.router, prefix="/config", tags=["config"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(security_ops.router, prefix="/security", tags=["security"])
api_router.include_router(security_incidents.router, prefix="/security/incidents", tags=["security-incidents"])
api_router.include_router(traceability.router, prefix="/traceability", tags=["traceability"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(sales_orders.router, prefix="/sales-orders", tags=["sales-orders"])
api_router.include_router(sales_deliveries.router, prefix="/sales-deliveries", tags=["sales-deliveries"])
api_router.include_router(sales_invoices.router, prefix="/sales-invoices", tags=["sales-invoices"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(purchase_requests.router, prefix="/purchase-requests", tags=["purchase-requests"])
api_router.include_router(rfqs.router, prefix="/rfqs", tags=["rfqs"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])
api_router.include_router(goods_receipts.router, prefix="/goods-receipts", tags=["goods-receipts"])
api_router.include_router(quality_inspections.router, prefix="/quality-inspections", tags=["quality-inspections"])
api_router.include_router(supplier_invoices.router, prefix="/supplier-invoices", tags=["supplier-invoices"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
