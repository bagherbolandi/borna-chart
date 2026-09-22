from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.procurement import GoodsReceipt, Payment, PurchaseOrder, QualityInspection, SupplierInvoice
from app.models.workflow import WorkflowInstance
from app.services.alert_service import AlertService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.rfq_service import ProcurementFlowError
from app.services.workflow_service import WorkflowService


class DownstreamProcurementService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.audit = AuditService(db)
        self.approvals = ApprovalService(db)
        self.alerts = AlertService(db)

    def _next_code(self, model, prefix: str) -> str:
        last = self.db.query(model).order_by(model.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"{prefix}-{next_no:06d}"

    def _get_po(self, po_id: int) -> PurchaseOrder | None:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    def _get_receipt(self, receipt_id: int) -> GoodsReceipt | None:
        return self.db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()

    def _get_qc(self, qc_id: int) -> QualityInspection | None:
        return self.db.query(QualityInspection).filter(QualityInspection.id == qc_id).first()

    def _get_invoice(self, invoice_id: int) -> SupplierInvoice | None:
        return self.db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()

    def _get_payment(self, payment_id: int) -> Payment | None:
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_workflow_instance(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def list_receipts(self) -> list[GoodsReceipt]:
        return self.db.query(GoodsReceipt).order_by(GoodsReceipt.id.desc()).all()

    def list_quality_inspections(self) -> list[QualityInspection]:
        return self.db.query(QualityInspection).order_by(QualityInspection.id.desc()).all()

    def list_supplier_invoices(self) -> list[SupplierInvoice]:
        return self.db.query(SupplierInvoice).order_by(SupplierInvoice.id.desc()).all()

    def list_payments(self) -> list[Payment]:
        return self.db.query(Payment).order_by(Payment.id.desc()).all()

    def get_receipt(self, receipt_id: int) -> GoodsReceipt | None:
        return self._get_receipt(receipt_id)

    def get_quality_inspection(self, qc_id: int) -> QualityInspection | None:
        return self._get_qc(qc_id)

    def get_supplier_invoice(self, invoice_id: int) -> SupplierInvoice | None:
        return self._get_invoice(invoice_id)

    def get_payment(self, payment_id: int) -> Payment | None:
        return self._get_payment(payment_id)

    def create_goods_receipt(self, payload) -> GoodsReceipt:
        po = self._get_po(payload.purchase_order_id)
        if not po:
            raise ProcurementFlowError("GRN-001: purchase order not found")
        if po.status in {"received", "inventory_released", "closed"}:
            raise ProcurementFlowError("receipt already registered or PO is closed")

        po_instance = self.get_workflow_instance(po.workflow_instance_id)
        if not po_instance:
            raise ProcurementFlowError("workflow instance not found")
        if po_instance.current_state == "po_issued":
            self.workflow.apply_transition(
                instance=po_instance,
                process_name="procurement",
                action="release_supplier",
                actor="system",
                actor_role="System",
            )
        if po_instance.current_state != "waiting_delivery":
            raise ProcurementFlowError("GRN-001: PO must be waiting delivery before receipt")

        self.workflow.apply_transition(
            instance=po_instance,
            process_name="procurement",
            action="record_receipt",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )

        receipt = GoodsReceipt(
            code=self._next_code(GoodsReceipt, "GRN"),
            purchase_order_id=po.id,
            receipt_date=payload.receipt_date.isoformat(),
            warehouse_code=payload.warehouse_code,
            supplier_delivery_ref=payload.supplier_delivery_ref,
            received_qty=Decimal(str(payload.received_qty)),
            status="received",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(receipt)
        self.db.flush()
        receipt_instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="GoodsReceipt",
            object_id=receipt.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(po.total_amount),
            initial_state="received",
        )
        receipt.workflow_instance_id = receipt_instance.id
        po.status = "received"
        po.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="goods_receipts",
            entity_id=str(receipt.id),
            action="create",
            new_value=receipt.code,
            reason=f"po {po.code}",
        )
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def create_quality_inspection(self, payload) -> QualityInspection:
        receipt = self._get_receipt(payload.goods_receipt_id)
        if not receipt:
            raise ProcurementFlowError("goods receipt not found")
        if receipt.status != "received":
            raise ProcurementFlowError("quality inspection can only start after receipt")

        qc = QualityInspection(
            code=self._next_code(QualityInspection, "QC"),
            goods_receipt_id=receipt.id,
            inspection_date=payload.inspection_date.isoformat(),
            inspector=payload.inspector,
            result=None,
            accepted_qty=Decimal("0"),
            rejected_qty=Decimal("0"),
            defect_code=None,
            corrective_action=None,
            status="qc_pending",
            created_by=payload.inspector,
            modified_by=payload.inspector,
        )
        self.db.add(qc)
        self.db.flush()
        qc_instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="QualityInspection",
            object_id=qc.id,
            current_owner=payload.inspector,
            current_role=payload.actor_role,
            initial_state="qc_pending",
        )
        qc.workflow_instance_id = qc_instance.id
        self.audit.log(
            user_name=payload.inspector,
            entity_name="quality_inspections",
            entity_id=str(qc.id),
            action="create",
            new_value=qc.code,
            reason=f"receipt {receipt.code}",
        )
        self.db.commit()
        self.db.refresh(qc)
        return qc

    def finalize_quality_inspection(self, qc_id: int, payload) -> QualityInspection:
        qc = self._get_qc(qc_id)
        if not qc:
            raise ProcurementFlowError("quality inspection not found")
        if qc.status != "qc_pending":
            raise ProcurementFlowError("quality inspection already finalized")
        if payload.accepted_qty + payload.rejected_qty <= 0:
            raise ProcurementFlowError("accepted or rejected quantity is required")

        receipt = self._get_receipt(qc.goods_receipt_id)
        if not receipt:
            raise ProcurementFlowError("goods receipt not found")
        instance = self.get_workflow_instance(qc.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")

        normalized = payload.result.lower()
        if normalized not in {"accepted", "rejected"}:
            raise ProcurementFlowError("result must be accepted or rejected")

        if normalized == "accepted":
            self.workflow.apply_transition(
                instance=instance,
                process_name="procurement",
                action="accept_qc",
                actor=payload.actor,
                actor_role=payload.actor_role,
            )
            self.workflow.apply_transition(
                instance=instance,
                process_name="procurement",
                action="release_inventory",
                actor="warehouse.system",
                actor_role="Warehouse Receiver",
            )
            qc.result = "accepted"
            qc.status = "inventory_released"
            receipt.status = "inventory_released"
            po = self._get_po(receipt.purchase_order_id)
            if po:
                po.status = "inventory_released"
                po.modified_by = payload.actor
        else:
            self.workflow.apply_transition(
                instance=instance,
                process_name="procurement",
                action="reject_qc",
                actor=payload.actor,
                actor_role=payload.actor_role,
            )
            qc.result = "rejected"
            qc.status = "rejected"
            receipt.status = "rejected"
            self.alerts.create(
                alert_code="QC-REJECT",
                related_object_type="QualityInspection",
                related_object_id=qc.id,
                alert_type="QC Rejection",
                severity="high",
                owner=payload.actor,
                created_by=payload.actor,
            )

        qc.accepted_qty = Decimal(str(payload.accepted_qty))
        qc.rejected_qty = Decimal(str(payload.rejected_qty))
        qc.defect_code = payload.defect_code
        qc.corrective_action = payload.corrective_action
        qc.modified_by = payload.actor
        receipt.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="quality_inspections",
            entity_id=str(qc.id),
            action="finalize",
            new_value=qc.status,
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(qc)
        return qc

    def _find_qc_by_receipt(self, receipt_id: int) -> QualityInspection | None:
        return self.db.query(QualityInspection).filter(QualityInspection.goods_receipt_id == receipt_id).order_by(QualityInspection.id.desc()).first()

    def create_supplier_invoice(self, payload) -> SupplierInvoice:
        po = self._get_po(payload.purchase_order_id)
        if not po:
            raise ProcurementFlowError("purchase order not found")
        receipt = self._get_receipt(payload.goods_receipt_id)
        if not receipt or receipt.purchase_order_id != po.id:
            raise ProcurementFlowError("INV-001: goods receipt must belong to purchase order")
        if po.supplier_id != payload.supplier_id:
            raise ProcurementFlowError("INV-001: supplier invoice supplier must match purchase order supplier")

        invoice = SupplierInvoice(
            code=self._next_code(SupplierInvoice, "INV"),
            supplier_id=payload.supplier_id,
            purchase_order_id=po.id,
            goods_receipt_id=receipt.id,
            invoice_no=payload.invoice_no,
            invoice_date=payload.invoice_date.isoformat(),
            due_date=payload.due_date.isoformat() if payload.due_date else None,
            currency=payload.currency,
            total_amount=Decimal(str(payload.total_amount)),
            match_status="pending",
            status="open",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(invoice)
        self.db.flush()
        instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="SupplierInvoice",
            object_id=invoice.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(payload.total_amount),
            initial_state="inventory_released",
        )
        invoice.workflow_instance_id = instance.id
        self.audit.log(
            user_name=payload.actor,
            entity_name="supplier_invoices",
            entity_id=str(invoice.id),
            action="create",
            new_value=invoice.code,
            reason=f"po {po.code}",
        )
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def match_supplier_invoice(self, invoice_id: int, payload) -> SupplierInvoice:
        invoice = self._get_invoice(invoice_id)
        if not invoice:
            raise ProcurementFlowError("supplier invoice not found")
        if invoice.match_status == "matched":
            raise ProcurementFlowError("invoice already matched")

        qc = self._find_qc_by_receipt(invoice.goods_receipt_id)
        if not qc:
            raise ProcurementFlowError("INV-001: QC record is required before matching")
        if qc.status != "inventory_released":
            raise ProcurementFlowError("INV-001: QC must be accepted and inventory released before match")

        instance = self.get_workflow_instance(invoice.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="match_invoice",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        invoice.match_status = "matched"
        invoice.status = "invoice_matched"
        invoice.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="supplier_invoices",
            entity_id=str(invoice.id),
            action="match",
            old_value="pending",
            new_value="matched",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_payment(self, payload) -> Payment:
        invoice = self._get_invoice(payload.supplier_invoice_id)
        if not invoice:
            raise ProcurementFlowError("supplier invoice not found")
        if invoice.match_status != "matched":
            raise ProcurementFlowError("PAY-001: payment cannot be created before successful match")
        if payload.amount > float(invoice.total_amount):
            raise ProcurementFlowError("PAY-001: payment amount cannot exceed matched invoice amount")

        payment = Payment(
            code=self._next_code(Payment, "PAY"),
            supplier_invoice_id=invoice.id,
            payment_date=payload.payment_date.isoformat() if payload.payment_date else None,
            amount=Decimal(str(payload.amount)),
            currency=payload.currency,
            payment_method=payload.payment_method,
            bank_reference=payload.bank_reference,
            status="created",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(payment)
        self.db.flush()
        instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="Payment",
            object_id=payment.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(payload.amount),
            initial_state="invoice_matched",
        )
        payment.workflow_instance_id = instance.id
        self.audit.log(
            user_name=payload.actor,
            entity_name="payments",
            entity_id=str(payment.id),
            action="create",
            new_value=payment.code,
            reason=f"invoice {invoice.code}",
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def approve_payment(self, payment_id: int, payload) -> Payment:
        payment = self._get_payment(payment_id)
        if not payment:
            raise ProcurementFlowError("payment not found")
        invoice = self._get_invoice(payment.supplier_invoice_id)
        if not invoice or invoice.match_status != "matched":
            raise ProcurementFlowError("PAY-001: payment approval requires successful invoice match")

        instance = self.get_workflow_instance(payment.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="approve_payment",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        payment.status = "payment_approved"
        payment.modified_by = payload.actor
        self.approvals.record(
            object_type="Payment",
            object_id=payment.id,
            approval_stage="payment",
            approver_name=payload.actor,
            approver_role=payload.actor_role,
            decision="approved",
            decision_note=payload.note,
        )
        self.audit.log(
            user_name=payload.actor,
            entity_name="payments",
            entity_id=str(payment.id),
            action="approve",
            old_value="created",
            new_value="payment_approved",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def execute_payment(self, payment_id: int, payload) -> Payment:
        payment = self._get_payment(payment_id)
        if not payment:
            raise ProcurementFlowError("payment not found")
        if payment.status != "payment_approved":
            raise ProcurementFlowError("payment must be approved before execution")
        invoice = self._get_invoice(payment.supplier_invoice_id)
        if payment.created_by == payload.actor or (invoice and invoice.modified_by == payload.actor):
            raise ProcurementFlowError("SOD-001: payment executor must be independent from matcher/creator")

        instance = self.get_workflow_instance(payment.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="execute_payment",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        payment.status = "paid"
        payment.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="payments",
            entity_id=str(payment.id),
            action="execute",
            old_value="payment_approved",
            new_value="paid",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(payment)
        return payment
