from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.master import Supplier
from app.models.procurement import PurchaseOrder, PurchaseRequest, RFQ, SupplierQuotation
from app.models.workflow import WorkflowInstance
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.workflow_service import WorkflowService


class ProcurementFlowError(Exception):
    pass


class RFQService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.audit = AuditService(db)
        self.approvals = ApprovalService(db)

    def _next_code(self, model, prefix: str) -> str:
        last = self.db.query(model).order_by(model.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"{prefix}-{next_no:06d}"

    def _get_pr(self, purchase_request_id: int) -> PurchaseRequest | None:
        return self.db.query(PurchaseRequest).filter(PurchaseRequest.id == purchase_request_id).first()

    def _get_rfq(self, rfq_id: int) -> RFQ | None:
        return self.db.query(RFQ).filter(RFQ.id == rfq_id).first()

    def get_rfq(self, rfq_id: int) -> RFQ | None:
        return self._get_rfq(rfq_id)

    def _get_quote(self, quotation_id: int) -> SupplierQuotation | None:
        return self.db.query(SupplierQuotation).filter(SupplierQuotation.id == quotation_id).first()

    def _get_supplier(self, supplier_id: int) -> Supplier | None:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_workflow_instance(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def list_rfqs(self) -> list[RFQ]:
        return self.db.query(RFQ).order_by(RFQ.id.desc()).all()

    def list_purchase_orders(self) -> list[PurchaseOrder]:
        return self.db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()

    def get_purchase_order(self, po_id: int) -> PurchaseOrder | None:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()

    def get_quotes(self, rfq_id: int) -> list[SupplierQuotation]:
        return (
            self.db.query(SupplierQuotation)
            .filter(SupplierQuotation.rfq_id == rfq_id)
            .order_by(SupplierQuotation.id.asc())
            .all()
        )

    def create_rfq(self, payload) -> RFQ:
        pr = self._get_pr(payload.purchase_request_id)
        if not pr:
            raise ProcurementFlowError("purchase request not found")
        if pr.status != "approved":
            raise ProcurementFlowError("RFQ-001: purchase request must be approved before RFQ creation")

        pr_instance = self.get_workflow_instance(pr.workflow_instance_id)
        if not pr_instance or pr_instance.current_state != "approved":
            raise ProcurementFlowError("RFQ-001: workflow state must be approved before RFQ creation")

        rfq = RFQ(
            code=self._next_code(RFQ, "RFQ"),
            purchase_request_id=payload.purchase_request_id,
            issue_date=payload.issue_date.isoformat(),
            close_date=payload.close_date.isoformat() if payload.close_date else None,
            minimum_quote_count=payload.minimum_quote_count,
            buyer=payload.buyer,
            status="rfq_created",
            created_by=payload.created_by or payload.buyer,
            modified_by=payload.created_by or payload.buyer,
        )
        self.db.add(rfq)
        self.db.flush()

        rfq_instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="RFQ",
            object_id=rfq.id,
            current_owner=payload.buyer,
            current_role="Procurement Officer",
            financial_impact=float(pr.total_estimated_amount),
            initial_state="rfq_created",
        )
        rfq.workflow_instance_id = rfq_instance.id

        self.audit.log(
            user_name=payload.created_by or payload.buyer,
            entity_name="rfqs",
            entity_id=str(rfq.id),
            action="create",
            new_value=rfq.code,
            reason=f"created from {pr.code}",
        )
        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def add_quotation(self, rfq_id: int, payload) -> SupplierQuotation:
        rfq = self._get_rfq(rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        if rfq.status not in {"rfq_created", "quotation_received"}:
            raise ProcurementFlowError("quotation can only be added before evaluation starts")

        supplier = self._get_supplier(payload.supplier_id)
        if not supplier:
            raise ProcurementFlowError("supplier not found")

        quotation = SupplierQuotation(
            rfq_id=rfq_id,
            supplier_id=payload.supplier_id,
            quote_no=payload.quote_no,
            quote_date=payload.quote_date.isoformat(),
            currency=payload.currency,
            validity_date=payload.validity_date.isoformat() if payload.validity_date else None,
            delivery_days=payload.delivery_days,
            payment_terms=payload.payment_terms,
            total_amount=Decimal(str(payload.total_amount)),
            price_variance_pct=Decimal(str(payload.price_variance_pct)) if payload.price_variance_pct is not None else None,
            commercial_score=Decimal(str(payload.commercial_score)) if payload.commercial_score is not None else None,
            technical_score=Decimal(str(payload.technical_score)) if payload.technical_score is not None else None,
            is_selected=False,
            status="received",
            created_by=payload.created_by or rfq.buyer,
            modified_by=payload.created_by or rfq.buyer,
        )
        self.db.add(quotation)
        self.db.flush()
        self.audit.log(
            user_name=payload.created_by or rfq.buyer,
            entity_name="supplier_quotations",
            entity_id=str(quotation.id),
            action="create",
            new_value=quotation.quote_no,
            reason=f"rfq {rfq.code}",
        )
        self.db.commit()
        self.db.refresh(quotation)
        return quotation

    def mark_quotation_received(self, rfq_id: int, actor: str, actor_role: str, exception_approved: bool = False) -> RFQ:
        rfq = self._get_rfq(rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        quotes = self.get_quotes(rfq_id)
        if len(quotes) < rfq.minimum_quote_count and not exception_approved:
            raise ProcurementFlowError("RFQ-002: minimum quotation count not satisfied")

        instance = self.get_workflow_instance(rfq.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="record_quotes",
            actor=actor,
            actor_role=actor_role,
        )
        rfq.status = "quotation_received"
        rfq.modified_by = actor
        self.audit.log(
            user_name=actor,
            entity_name="rfqs",
            entity_id=str(rfq.id),
            action="record_quotes",
            old_value="rfq_created",
            new_value="quotation_received",
        )
        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def commercial_evaluate(self, rfq_id: int, payload) -> RFQ:
        rfq = self._get_rfq(rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        instance = self.get_workflow_instance(rfq.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")

        quote = self._get_quote(payload.selected_quotation_id)
        if not quote or quote.rfq_id != rfq_id:
            raise ProcurementFlowError("selected quotation not found for rfq")

        for item in self.get_quotes(rfq_id):
            item.is_selected = item.id == payload.selected_quotation_id
            item.modified_by = payload.actor
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="commercial_eval",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        rfq.status = "commercial_evaluated"
        rfq.modified_by = payload.actor
        self.audit.log(
            user_name=payload.actor,
            entity_name="rfqs",
            entity_id=str(rfq.id),
            action="commercial_eval",
            new_value=str(payload.selected_quotation_id),
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def technical_approve(self, rfq_id: int, payload) -> RFQ:
        rfq = self._get_rfq(rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        instance = self.get_workflow_instance(rfq.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="technical_eval",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        rfq.status = "technically_approved"
        rfq.modified_by = payload.actor
        self.approvals.record(
            object_type="RFQ",
            object_id=rfq.id,
            approval_stage="technical",
            approver_name=payload.actor,
            approver_role=payload.actor_role,
            decision="approved",
            decision_note=payload.note,
        )
        self.audit.log(
            user_name=payload.actor,
            entity_name="rfqs",
            entity_id=str(rfq.id),
            action="technical_approve",
            old_value="commercial_evaluated",
            new_value="technically_approved",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def price_approve(self, rfq_id: int, payload) -> RFQ:
        rfq = self._get_rfq(rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        instance = self.get_workflow_instance(rfq.workflow_instance_id)
        if not instance:
            raise ProcurementFlowError("workflow instance not found")

        selected_quote = (
            self.db.query(SupplierQuotation)
            .filter(SupplierQuotation.rfq_id == rfq_id, SupplierQuotation.is_selected.is_(True))
            .first()
        )
        if not selected_quote:
            raise ProcurementFlowError("QUO-001: selected quotation is required before price approval")

        self.workflow.apply_transition(
            instance=instance,
            process_name="procurement",
            action="approve_price",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
        rfq.status = "price_approved"
        rfq.modified_by = payload.actor
        self.approvals.record(
            object_type="RFQ",
            object_id=rfq.id,
            approval_stage="price",
            approver_name=payload.actor,
            approver_role=payload.actor_role,
            decision="approved",
            decision_note=payload.note,
        )
        self.audit.log(
            user_name=payload.actor,
            entity_name="rfqs",
            entity_id=str(rfq.id),
            action="price_approve",
            old_value="technically_approved",
            new_value="price_approved",
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(rfq)
        return rfq

    def create_purchase_order(self, payload) -> PurchaseOrder:
        rfq = self._get_rfq(payload.rfq_id)
        if not rfq:
            raise ProcurementFlowError("rfq not found")
        if rfq.status != "price_approved":
            raise ProcurementFlowError("PO-001: RFQ must be price approved before PO issue")

        quote = self._get_quote(payload.selected_quotation_id)
        if not quote or quote.rfq_id != rfq.id:
            raise ProcurementFlowError("selected quotation not found for rfq")
        if not quote.is_selected:
            raise ProcurementFlowError("PO-001: only selected quotation can be converted to PO")

        supplier = self._get_supplier(quote.supplier_id)
        if not supplier:
            raise ProcurementFlowError("supplier not found")
        if supplier.approval_status != "approved":
            raise ProcurementFlowError("SUP-001: supplier must be approved before PO issue")

        rfq_quotes = self.get_quotes(rfq.id)
        if len(rfq_quotes) < rfq.minimum_quote_count and not payload.exception_approved:
            raise ProcurementFlowError("RFQ-002: minimum quotation count not satisfied for PO issue")

        rfq_instance = self.get_workflow_instance(rfq.workflow_instance_id)
        if not rfq_instance:
            raise ProcurementFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=rfq_instance,
            process_name="procurement",
            action="issue_po",
            actor=payload.actor,
            actor_role=payload.actor_role,
        )

        po = PurchaseOrder(
            code=self._next_code(PurchaseOrder, "PO"),
            purchase_request_id=rfq.purchase_request_id,
            rfq_id=rfq.id,
            selected_quotation_id=quote.id,
            supplier_id=supplier.id,
            order_date=payload.order_date.isoformat(),
            delivery_date=payload.delivery_date.isoformat() if payload.delivery_date else None,
            currency=quote.currency,
            payment_terms=quote.payment_terms,
            total_amount=quote.total_amount,
            price_variance_pct=quote.price_variance_pct,
            emergency_flag=payload.emergency_flag,
            status="po_issued",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(po)
        self.db.flush()

        po_instance = self.workflow.create_instance(
            process_name="procurement",
            object_type="PO",
            object_id=po.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(quote.total_amount),
            initial_state="po_issued",
        )
        po.workflow_instance_id = po_instance.id

        self.approvals.record(
            object_type="PO",
            object_id=po.id,
            approval_stage="issue",
            approver_name=payload.actor,
            approver_role=payload.actor_role,
            decision="approved",
            decision_note=payload.note,
        )
        self.audit.log(
            user_name=payload.actor,
            entity_name="purchase_orders",
            entity_id=str(po.id),
            action="issue_po",
            new_value=po.code,
            reason=payload.note,
        )
        self.db.commit()
        self.db.refresh(po)
        return po
