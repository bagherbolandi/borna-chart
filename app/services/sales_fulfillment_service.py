from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.sales import CollectionReceipt, SalesDelivery, SalesInvoice, SalesOrder
from app.models.workflow import WorkflowInstance
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.pricing_sales_service import SalesFlowError
from app.services.workflow_service import WorkflowService


class SalesFulfillmentService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.audit = AuditService(db)

    def _next_code(self, model, prefix: str) -> str:
        last = self.db.query(model).order_by(model.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"{prefix}-{next_no:06d}"

    def _get_sales_order(self, sales_order_id: int) -> SalesOrder | None:
        return self.db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()

    def _get_delivery(self, delivery_id: int) -> SalesDelivery | None:
        return self.db.query(SalesDelivery).filter(SalesDelivery.id == delivery_id).first()

    def _get_invoice(self, invoice_id: int) -> SalesInvoice | None:
        return self.db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()

    def _get_collection(self, collection_id: int) -> CollectionReceipt | None:
        return self.db.query(CollectionReceipt).filter(CollectionReceipt.id == collection_id).first()

    def get_workflow_instance(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def list_deliveries(self) -> list[SalesDelivery]:
        return self.db.query(SalesDelivery).order_by(SalesDelivery.id.desc()).all()

    def get_delivery(self, delivery_id: int) -> SalesDelivery | None:
        return self._get_delivery(delivery_id)

    def list_sales_invoices(self) -> list[SalesInvoice]:
        return self.db.query(SalesInvoice).order_by(SalesInvoice.id.desc()).all()

    def get_sales_invoice(self, invoice_id: int) -> SalesInvoice | None:
        return self._get_invoice(invoice_id)

    def list_collections(self) -> list[CollectionReceipt]:
        return self.db.query(CollectionReceipt).order_by(CollectionReceipt.id.desc()).all()

    def get_collection(self, collection_id: int) -> CollectionReceipt | None:
        return self._get_collection(collection_id)

    def _find_delivery_by_sales_order(self, sales_order_id: int) -> SalesDelivery | None:
        return (
            self.db.query(SalesDelivery)
            .filter(SalesDelivery.sales_order_id == sales_order_id)
            .order_by(SalesDelivery.id.desc())
            .first()
        )

    def _find_invoice_by_delivery(self, sales_delivery_id: int) -> SalesInvoice | None:
        return (
            self.db.query(SalesInvoice)
            .filter(SalesInvoice.sales_delivery_id == sales_delivery_id)
            .order_by(SalesInvoice.id.desc())
            .first()
        )

    def _collected_amount(self, sales_invoice_id: int) -> Decimal:
        total = Decimal("0")
        rows = self.db.query(CollectionReceipt).filter(CollectionReceipt.sales_invoice_id == sales_invoice_id).all()
        for row in rows:
            total += Decimal(str(row.amount))
        return total

    def create_delivery_plan(self, payload) -> SalesDelivery:
        sales_order = self._get_sales_order(payload.sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if sales_order.status != "sales_order_confirmed":
            raise SalesFlowError("DEL-001: delivery planning requires confirmed sales order")
        if Decimal(str(payload.planned_qty)) > Decimal(str(sales_order.qty)):
            raise SalesFlowError("DEL-001: planned delivery quantity cannot exceed sales order quantity")
        existing = self._find_delivery_by_sales_order(sales_order.id)
        if existing and existing.status != "closed":
            raise SalesFlowError("delivery plan already exists for sales order")

        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="allocate_supply",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )

        delivery = SalesDelivery(
            code=self._next_code(SalesDelivery, "SHP"),
            sales_order_id=sales_order.id,
            planned_date=payload.planned_date.isoformat(),
            warehouse_code=payload.warehouse_code,
            planned_qty=Decimal(str(payload.planned_qty)),
            delivered_qty=Decimal("0"),
            status="planning_allocation",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(delivery)
        self.db.flush()
        delivery_instance = self.workflow.create_instance(
            process_name="sales",
            object_type="SalesDelivery",
            object_id=delivery.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(sales_order.total_amount),
            initial_state="planning_allocation",
        )
        delivery.workflow_instance_id = delivery_instance.id
        sales_order.status = "planning_allocation"
        sales_order.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="sales_deliveries",
            entity_id=str(delivery.id),
            action="create",
            new_value=delivery.code,
            reason=f"sales order {sales_order.code}",
        )
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def release_delivery(self, delivery_id: int, payload) -> SalesDelivery:
        delivery = self._get_delivery(delivery_id)
        if not delivery:
            raise SalesFlowError("sales delivery not found")
        if delivery.status != "planning_allocation":
            raise SalesFlowError("delivery must be in planning allocation status before release")
        sales_order = self._get_sales_order(delivery.sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if sales_order.status != "planning_allocation":
            raise SalesFlowError("sales order must be in planning allocation status before release")

        delivery_instance = self.get_workflow_instance(delivery.workflow_instance_id)
        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not delivery_instance or not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=delivery_instance,
            process_name="sales",
            action="release_delivery",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="release_delivery",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        delivery.released_date = payload.release_date.isoformat() if payload.release_date else delivery.planned_date
        delivery.status = "ready_to_deliver"
        delivery.modified_by = payload.actor
        sales_order.status = "ready_to_deliver"
        sales_order.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="sales_deliveries",
            entity_id=str(delivery.id),
            action="release",
            old_value="planning_allocation",
            new_value="ready_to_deliver",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def deliver(self, delivery_id: int, payload) -> SalesDelivery:
        delivery = self._get_delivery(delivery_id)
        if not delivery:
            raise SalesFlowError("sales delivery not found")
        if delivery.status != "ready_to_deliver":
            raise SalesFlowError("DEL-001: delivery must be released before execution")
        sales_order = self._get_sales_order(delivery.sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if sales_order.status != "ready_to_deliver":
            raise SalesFlowError("sales order must be ready to deliver")
        if Decimal(str(payload.delivered_qty)) > Decimal(str(delivery.planned_qty)):
            raise SalesFlowError("DEL-001: delivered quantity cannot exceed released delivery quantity")

        delivery_instance = self.get_workflow_instance(delivery.workflow_instance_id)
        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not delivery_instance or not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=delivery_instance,
            process_name="sales",
            action="deliver",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="deliver",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        delivery.delivered_date = payload.delivered_date.isoformat()
        delivery.delivered_qty = Decimal(str(payload.delivered_qty))
        delivery.dispatch_reference = payload.dispatch_reference
        delivery.status = "delivered"
        delivery.modified_by = payload.actor
        sales_order.status = "delivered"
        sales_order.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="sales_deliveries",
            entity_id=str(delivery.id),
            action="deliver",
            old_value="ready_to_deliver",
            new_value="delivered",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def create_sales_invoice(self, payload) -> SalesInvoice:
        sales_order = self._get_sales_order(payload.sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        delivery = self._get_delivery(payload.sales_delivery_id)
        if not delivery:
            raise SalesFlowError("sales delivery not found")
        if delivery.sales_order_id != sales_order.id:
            raise SalesFlowError("delivery does not belong to sales order")
        if delivery.status != "delivered" or sales_order.status != "delivered":
            raise SalesFlowError("DEL-001: sales invoice requires delivered sales order")
        if self._find_invoice_by_delivery(delivery.id):
            raise SalesFlowError("sales invoice already exists for delivery")

        max_amount = Decimal(str(delivery.delivered_qty)) * Decimal(str(sales_order.unit_price))
        if Decimal(str(payload.total_amount)) > max_amount:
            raise SalesFlowError("INV-001: sales invoice amount cannot exceed delivered value")

        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="invoice",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="open_collection",
            actor="system",
            actor_role="System",
        )

        invoice = SalesInvoice(
            code=self._next_code(SalesInvoice, "AR"),
            sales_order_id=sales_order.id,
            sales_delivery_id=delivery.id,
            invoice_no=payload.invoice_no,
            invoice_date=payload.invoice_date.isoformat(),
            due_date=payload.due_date.isoformat() if payload.due_date else None,
            currency=payload.currency,
            total_amount=Decimal(str(payload.total_amount)),
            collected_amount=Decimal("0"),
            collection_status="open",
            status="collection_open",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(invoice)
        self.db.flush()
        invoice_instance = self.workflow.create_instance(
            process_name="sales",
            object_type="SalesInvoice",
            object_id=invoice.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(payload.total_amount),
            initial_state="delivered",
        )
        self.workflow.apply_transition(
            instance=invoice_instance,
            process_name="sales",
            action="invoice",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        self.workflow.apply_transition(
            instance=invoice_instance,
            process_name="sales",
            action="open_collection",
            actor="system",
            actor_role="System",
        )
        invoice.workflow_instance_id = invoice_instance.id
        sales_order.status = "collection_open"
        sales_order.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="sales_invoices",
            entity_id=str(invoice.id),
            action="create",
            new_value=invoice.code,
            reason=f"delivery {delivery.code}",
        )
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_collection_receipt(self, payload) -> CollectionReceipt:
        invoice = self._get_invoice(payload.sales_invoice_id)
        if not invoice:
            raise SalesFlowError("sales invoice not found")
        sales_order = self._get_sales_order(invoice.sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if invoice.status != "collection_open" or sales_order.status != "collection_open":
            raise SalesFlowError("COL-001: collection can only be posted for open receivable")
        if payload.currency != invoice.currency:
            raise SalesFlowError("collection currency must match invoice currency")

        current_collected = self._collected_amount(invoice.id)
        new_total = current_collected + Decimal(str(payload.amount))
        if new_total > Decimal(str(invoice.total_amount)):
            raise SalesFlowError("COL-001: collection amount cannot exceed invoice open amount")

        collection = CollectionReceipt(
            code=self._next_code(CollectionReceipt, "COL"),
            sales_invoice_id=invoice.id,
            receipt_date=payload.receipt_date.isoformat(),
            amount=Decimal(str(payload.amount)),
            currency=payload.currency,
            payment_method=payload.payment_method,
            bank_reference=payload.bank_reference,
            collector=payload.actor,
            status="collected",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(collection)
        self.db.flush()
        collection_instance = self.workflow.create_instance(
            process_name="sales",
            object_type="CollectionReceipt",
            object_id=collection.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(payload.amount),
            initial_state="collection_open",
        )
        self.workflow.apply_transition(
            instance=collection_instance,
            process_name="sales",
            action="allocate_receipt",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        collection.workflow_instance_id = collection_instance.id

        invoice.collected_amount = new_total
        invoice.collection_status = "collected" if new_total == Decimal(str(invoice.total_amount)) else "partial"
        invoice.status = "collected" if invoice.collection_status == "collected" else "collection_open"
        invoice.modified_by = payload.actor

        if invoice.collection_status == "collected":
            invoice_instance = self.get_workflow_instance(invoice.workflow_instance_id)
            so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
            if not invoice_instance or not so_instance:
                raise SalesFlowError("workflow instance not found")
            self.workflow.apply_transition(
                instance=invoice_instance,
                process_name="sales",
                action="allocate_receipt",
                actor=payload.actor,
                actor_role=payload.actor_role,
            )
            self.workflow.apply_transition(
                instance=so_instance,
                process_name="sales",
                action="allocate_receipt",
                actor=payload.actor,
                actor_role=payload.actor_role,
            )
            sales_order.status = "collected"
            sales_order.modified_by = payload.actor

        self.audit.log(
            user_name=payload.actor,
            entity_name="collection_receipts",
            entity_id=str(collection.id),
            action="create",
            new_value=collection.code,
            reason=f"invoice {invoice.code}",
        )
        self.db.commit()
        self.db.refresh(collection)
        return collection

    def review_profitability(self, sales_order_id: int, actor: str, actor_role: str, note: str | None = None) -> SalesOrder:
        sales_order = self._get_sales_order(sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if sales_order.status != "collected":
            raise SalesFlowError("profitability review requires fully collected sales order")
        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="analyze_margin",
            actor=actor,
            actor_role=actor_role,
        )
        sales_order.status = "profitability_reviewed"
        sales_order.modified_by = actor
        self.audit.log(
            user_name=actor,
            entity_name="sales_orders",
            entity_id=str(sales_order.id),
            action="analyze_margin",
            old_value="collected",
            new_value="profitability_reviewed",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(sales_order)
        return sales_order

    def close_sales_order(self, sales_order_id: int, actor: str, actor_role: str, note: str | None = None) -> SalesOrder:
        sales_order = self._get_sales_order(sales_order_id)
        if not sales_order:
            raise SalesFlowError("sales order not found")
        if sales_order.status != "profitability_reviewed":
            raise SalesFlowError("sales order must pass profitability review before closure")
        so_instance = self.get_workflow_instance(sales_order.workflow_instance_id)
        if not so_instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=so_instance,
            process_name="sales",
            action="close_case",
            actor=actor,
            actor_role=actor_role,
        )
        sales_order.status = "closed"
        sales_order.modified_by = actor
        self.audit.log(
            user_name=actor,
            entity_name="sales_orders",
            entity_id=str(sales_order.id),
            action="close_case",
            old_value="profitability_reviewed",
            new_value="closed",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(sales_order)
        return sales_order
