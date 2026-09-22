from datetime import UTC, datetime

from sqlalchemy import func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.models.master import User
from app.models.procurement import PurchaseOrder, PurchaseRequest, RFQ
from app.models.sales import CollectionReceipt, SalesDelivery, SalesInvoice, SalesOrder
from app.models.workflow import Alert, WorkflowInstance
from app.schemas.purchase_request import DashboardSummary
from app.schemas.security_dashboard import SecurityDashboardSummary
from app.services.security_operations_service import SecurityOperationsService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> DashboardSummary:
    pr_counts = dict(
        db.query(PurchaseRequest.status, func.count(PurchaseRequest.id))
        .group_by(PurchaseRequest.status)
        .all()
    )
    rfq_counts = dict(
        db.query(RFQ.status, func.count(RFQ.id))
        .group_by(RFQ.status)
        .all()
    )
    po_counts = dict(
        db.query(PurchaseOrder.status, func.count(PurchaseOrder.id))
        .group_by(PurchaseOrder.status)
        .all()
    )
    so_counts = dict(
        db.query(SalesOrder.status, func.count(SalesOrder.id))
        .group_by(SalesOrder.status)
        .all()
    )
    delivery_counts = dict(
        db.query(SalesDelivery.status, func.count(SalesDelivery.id))
        .group_by(SalesDelivery.status)
        .all()
    )
    sales_invoice_counts = dict(
        db.query(SalesInvoice.status, func.count(SalesInvoice.id))
        .group_by(SalesInvoice.status)
        .all()
    )
    collection_counts = dict(
        db.query(CollectionReceipt.status, func.count(CollectionReceipt.id))
        .group_by(CollectionReceipt.status)
        .all()
    )
    open_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "open").scalar() or 0
    open_workflow_items = db.query(WorkflowInstance).filter(WorkflowInstance.status == "open").all()
    now = datetime.now(UTC)
    overdue_workflow_instances = sum(
        1 for item in open_workflow_items if item.due_at and datetime.fromisoformat(item.due_at) <= now
    )
    escalated_workflow_instances = sum(1 for item in open_workflow_items if item.escalation_level > 0)
    workflow_instances = db.query(func.count(WorkflowInstance.id)).scalar() or 0
    return DashboardSummary(
        purchase_requests_by_status=pr_counts,
        rfqs_by_status=rfq_counts,
        purchase_orders_by_status=po_counts,
        sales_orders_by_status=so_counts,
        sales_deliveries_by_status=delivery_counts,
        sales_invoices_by_status=sales_invoice_counts,
        collections_by_status=collection_counts,
        open_alerts=int(open_alerts),
        overdue_workflow_instances=int(overdue_workflow_instances),
        escalated_workflow_instances=int(escalated_workflow_instances),
        workflow_instances=int(workflow_instances),
    )


@router.get("/security", response_model=SecurityDashboardSummary)
def security_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Master Data Admin", "Security Officer")),
) -> SecurityDashboardSummary:
    return SecurityOperationsService(db).dashboard_summary()
