from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.master import AuditLog
from app.models.procurement import (
    GoodsReceipt,
    Payment,
    PurchaseOrder,
    PurchaseRequest,
    QualityInspection,
    RFQ,
    SupplierInvoice,
    SupplierQuotation,
)
from app.models.sales import CollectionReceipt, PriceList, SalesDelivery, SalesInvoice, SalesOrder
from app.models.workflow import Alert, Approval, WorkflowInstance
from app.schemas.alert import AlertRead
from app.schemas.approval import ApprovalRead
from app.schemas.traceability import (
    TraceabilityDocument,
    TraceabilityOverview,
    TraceabilityResponse,
    TraceabilityTimelineEvent,
)


class TraceabilityError(Exception):
    pass


class TraceabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _workflow(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    @staticmethod
    def _normalize_object_type(object_type: str) -> str:
        return object_type.strip().lower().replace("-", "").replace("_", "")

    @staticmethod
    def _code_for(obj: Any) -> str:
        return str(
            getattr(obj, "code", None)
            or getattr(obj, "quote_no", None)
            or getattr(obj, "invoice_no", None)
            or f"{obj.__class__.__name__}-{getattr(obj, 'id', 'NA')}"
        )

    @staticmethod
    def _amount_for(obj: Any) -> float | None:
        for attr in ("total_amount", "amount", "total_estimated_amount"):
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                return float(value) if value is not None else None
        return None

    @staticmethod
    def _currency_for(obj: Any) -> str | None:
        if hasattr(obj, "currency"):
            return getattr(obj, "currency")
        return None

    def _document_summary(self, object_type: str, relation: str, obj: Any) -> TraceabilityDocument:
        wf = self._workflow(getattr(obj, "workflow_instance_id", None))
        return TraceabilityDocument(
            object_type=object_type,
            object_id=obj.id,
            relation=relation,
            code=self._code_for(obj),
            status=getattr(obj, "status", None),
            workflow_instance_id=getattr(obj, "workflow_instance_id", None),
            current_state=wf.current_state if wf else None,
            current_owner=wf.current_owner if wf else None,
            current_role=wf.current_role if wf else None,
            due_at=wf.due_at if wf else None,
            escalation_level=wf.escalation_level if wf else 0,
            financial_impact=float(wf.financial_impact) if wf else 0,
            amount=self._amount_for(obj),
            currency=self._currency_for(obj),
        )

    def _active_document(self, documents: list[TraceabilityDocument]) -> TraceabilityDocument | None:
        open_docs = [doc for doc in documents if doc.current_state and doc.status not in {"closed"}]
        if open_docs:
            return sorted(open_docs, key=lambda item: (item.workflow_instance_id or 0, item.object_id), reverse=True)[0]
        return documents[-1] if documents else None

    def _alerts_for_documents(self, docs: list[TraceabilityDocument]) -> list[AlertRead]:
        results: list[AlertRead] = []
        for doc in docs:
            rows = (
                self.db.query(Alert)
                .filter(Alert.related_object_type == doc.object_type, Alert.related_object_id == doc.object_id)
                .order_by(Alert.id.asc())
                .all()
            )
            results.extend(AlertRead.model_validate(row) for row in rows)
        return results

    def _approvals_for_documents(self, docs: list[TraceabilityDocument]) -> list[ApprovalRead]:
        results: list[ApprovalRead] = []
        for doc in docs:
            rows = (
                self.db.query(Approval)
                .filter(Approval.object_type == doc.object_type, Approval.object_id == doc.object_id)
                .order_by(Approval.id.asc())
                .all()
            )
            results.extend(ApprovalRead.model_validate(row) for row in rows)
        return results

    def _audit_events_for_documents(self, docs: list[TraceabilityDocument]) -> list[TraceabilityTimelineEvent]:
        entity_map = {
            "PurchaseRequest": "purchase_requests",
            "RFQ": "rfqs",
            "SupplierQuotation": "supplier_quotations",
            "PO": "purchase_orders",
            "GoodsReceipt": "goods_receipts",
            "QualityInspection": "quality_inspections",
            "SupplierInvoice": "supplier_invoices",
            "Payment": "payments",
            "PriceList": "price_lists",
            "SalesOrder": "sales_orders",
            "SalesDelivery": "sales_deliveries",
            "SalesInvoice": "sales_invoices",
            "CollectionReceipt": "collection_receipts",
        }
        timeline: list[TraceabilityTimelineEvent] = []
        for doc in docs:
            entity_name = entity_map.get(doc.object_type)
            if not entity_name:
                continue
            rows = (
                self.db.query(AuditLog)
                .filter(AuditLog.entity_name == entity_name, AuditLog.entity_id == str(doc.object_id))
                .order_by(AuditLog.id.asc())
                .all()
            )
            for row in rows:
                timeline.append(
                    TraceabilityTimelineEvent(
                        event_time=row.event_time,
                        source_type=doc.object_type,
                        source_id=doc.object_id,
                        source_code=doc.code,
                        event_type=row.action,
                        actor=row.user_name,
                        status=None,
                        message=row.reason or row.new_value or row.old_value,
                    )
                )
        return timeline

    def _timeline(
        self,
        docs: list[TraceabilityDocument],
        alerts: list[AlertRead],
        approvals: list[ApprovalRead],
    ) -> list[TraceabilityTimelineEvent]:
        timeline = self._audit_events_for_documents(docs)
        code_map = {(doc.object_type, doc.object_id): doc.code for doc in docs}
        for item in approvals:
            timeline.append(
                TraceabilityTimelineEvent(
                    event_time=item.decided_at,
                    source_type=item.object_type,
                    source_id=item.object_id,
                    source_code=code_map.get((item.object_type, item.object_id)),
                    event_type=f"approval:{item.approval_stage}",
                    actor=item.approver_name,
                    status=item.decision,
                    message=item.decision_note,
                )
            )
        for item in alerts:
            timeline.append(
                TraceabilityTimelineEvent(
                    event_time=item.created_at.isoformat() if item.created_at else datetime.now(UTC).isoformat(),
                    source_type=item.related_object_type,
                    source_id=item.related_object_id,
                    source_code=code_map.get((item.related_object_type, item.related_object_id)),
                    event_type=f"alert:{item.alert_type}",
                    actor=item.owner,
                    status=item.status,
                    message=item.message,
                )
            )
        timeline.sort(key=lambda item: item.event_time)
        return timeline

    def _build_response(self, process_name: str, docs: list[TraceabilityDocument]) -> TraceabilityResponse:
        root = docs[0]
        active = self._active_document(docs)
        alerts = self._alerts_for_documents(docs)
        approvals = self._approvals_for_documents(docs)
        timeline = self._timeline(docs, alerts, approvals)

        due_at = active.due_at if active else None
        is_overdue = False
        if due_at:
            is_overdue = datetime.fromisoformat(due_at) <= datetime.now(UTC)

        overview = TraceabilityOverview(
            process_name=process_name,
            root_object_type=root.object_type,
            root_object_id=root.object_id,
            root_code=root.code,
            root_status=root.status,
            active_object_type=active.object_type if active else None,
            active_object_id=active.object_id if active else None,
            active_object_code=active.code if active else None,
            current_owner=active.current_owner if active else None,
            current_role=active.current_role if active else None,
            current_state=active.current_state if active else None,
            due_at=due_at,
            escalation_level=active.escalation_level if active else 0,
            is_overdue=is_overdue,
            financial_impact=active.financial_impact if active else 0,
            open_alerts=sum(1 for alert in alerts if alert.status == "open"),
            linked_document_count=len(docs),
        )
        return TraceabilityResponse(
            overview=overview,
            linked_documents=docs,
            approvals=approvals,
            alerts=alerts,
            timeline=timeline,
        )

    def _procurement_chain(self, pr_id: int) -> list[TraceabilityDocument]:
        pr = self.db.query(PurchaseRequest).filter(PurchaseRequest.id == pr_id).first()
        if not pr:
            raise TraceabilityError("purchase request not found")
        docs: list[TraceabilityDocument] = [self._document_summary("PurchaseRequest", "root", pr)]

        rfqs = self.db.query(RFQ).filter(RFQ.purchase_request_id == pr.id).order_by(RFQ.id.asc()).all()
        for rfq in rfqs:
            docs.append(self._document_summary("RFQ", "rfq", rfq))
            quotes = (
                self.db.query(SupplierQuotation)
                .filter(SupplierQuotation.rfq_id == rfq.id)
                .order_by(SupplierQuotation.id.asc())
                .all()
            )
            for quote in quotes:
                relation = "selected_quotation" if quote.is_selected else "quotation"
                docs.append(self._document_summary("SupplierQuotation", relation, quote))

        pos = self.db.query(PurchaseOrder).filter(PurchaseOrder.purchase_request_id == pr.id).order_by(PurchaseOrder.id.asc()).all()
        for po in pos:
            docs.append(self._document_summary("PO", "purchase_order", po))
            receipts = (
                self.db.query(GoodsReceipt)
                .filter(GoodsReceipt.purchase_order_id == po.id)
                .order_by(GoodsReceipt.id.asc())
                .all()
            )
            for receipt in receipts:
                docs.append(self._document_summary("GoodsReceipt", "goods_receipt", receipt))
                qcs = (
                    self.db.query(QualityInspection)
                    .filter(QualityInspection.goods_receipt_id == receipt.id)
                    .order_by(QualityInspection.id.asc())
                    .all()
                )
                for qc in qcs:
                    docs.append(self._document_summary("QualityInspection", "quality_inspection", qc))

            invoices = (
                self.db.query(SupplierInvoice)
                .filter(SupplierInvoice.purchase_order_id == po.id)
                .order_by(SupplierInvoice.id.asc())
                .all()
            )
            for invoice in invoices:
                docs.append(self._document_summary("SupplierInvoice", "supplier_invoice", invoice))
                payments = (
                    self.db.query(Payment)
                    .filter(Payment.supplier_invoice_id == invoice.id)
                    .order_by(Payment.id.asc())
                    .all()
                )
                for payment in payments:
                    docs.append(self._document_summary("Payment", "payment", payment))

        return docs

    def procurement_traceability(self, pr_id: int) -> TraceabilityResponse:
        return self._build_response("procurement", self._procurement_chain(pr_id))

    def _sales_chain(self, sales_order_id: int) -> list[TraceabilityDocument]:
        sales_order = self.db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()
        if not sales_order:
            raise TraceabilityError("sales order not found")

        docs: list[TraceabilityDocument] = [self._document_summary("SalesOrder", "root", sales_order)]

        price_list = self.db.query(PriceList).filter(PriceList.id == sales_order.price_list_id).first()
        if price_list:
            docs.append(self._document_summary("PriceList", "approved_price_list", price_list))

        deliveries = (
            self.db.query(SalesDelivery)
            .filter(SalesDelivery.sales_order_id == sales_order.id)
            .order_by(SalesDelivery.id.asc())
            .all()
        )
        for delivery in deliveries:
            docs.append(self._document_summary("SalesDelivery", "sales_delivery", delivery))
            invoices = (
                self.db.query(SalesInvoice)
                .filter(SalesInvoice.sales_delivery_id == delivery.id)
                .order_by(SalesInvoice.id.asc())
                .all()
            )
            for invoice in invoices:
                docs.append(self._document_summary("SalesInvoice", "sales_invoice", invoice))
                collections = (
                    self.db.query(CollectionReceipt)
                    .filter(CollectionReceipt.sales_invoice_id == invoice.id)
                    .order_by(CollectionReceipt.id.asc())
                    .all()
                )
                for collection in collections:
                    docs.append(self._document_summary("CollectionReceipt", "collection_receipt", collection))

        return docs

    def sales_traceability(self, sales_order_id: int) -> TraceabilityResponse:
        return self._build_response("sales", self._sales_chain(sales_order_id))

    def _resolve_purchase_request_id(self, object_type: str, object_id: int) -> int:
        normalized = self._normalize_object_type(object_type)
        if normalized in {"purchaserequest", "pr"}:
            return object_id
        if normalized == "rfq":
            rfq = self.db.query(RFQ).filter(RFQ.id == object_id).first()
            if not rfq:
                raise TraceabilityError("rfq not found")
            return rfq.purchase_request_id
        if normalized in {"supplierquotation", "quotation", "quote"}:
            quote = self.db.query(SupplierQuotation).filter(SupplierQuotation.id == object_id).first()
            if not quote:
                raise TraceabilityError("quotation not found")
            rfq = self.db.query(RFQ).filter(RFQ.id == quote.rfq_id).first()
            if not rfq:
                raise TraceabilityError("rfq not found")
            return rfq.purchase_request_id
        if normalized in {"po", "purchaseorder"}:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == object_id).first()
            if not po:
                raise TraceabilityError("purchase order not found")
            return po.purchase_request_id
        if normalized in {"goodsreceipt", "grn", "receipt"}:
            receipt = self.db.query(GoodsReceipt).filter(GoodsReceipt.id == object_id).first()
            if not receipt:
                raise TraceabilityError("goods receipt not found")
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == receipt.purchase_order_id).first()
            if not po:
                raise TraceabilityError("purchase order not found")
            return po.purchase_request_id
        if normalized in {"qualityinspection", "qc"}:
            qc = self.db.query(QualityInspection).filter(QualityInspection.id == object_id).first()
            if not qc:
                raise TraceabilityError("quality inspection not found")
            receipt = self.db.query(GoodsReceipt).filter(GoodsReceipt.id == qc.goods_receipt_id).first()
            if not receipt:
                raise TraceabilityError("goods receipt not found")
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == receipt.purchase_order_id).first()
            if not po:
                raise TraceabilityError("purchase order not found")
            return po.purchase_request_id
        if normalized in {"supplierinvoice", "invoice"}:
            invoice = self.db.query(SupplierInvoice).filter(SupplierInvoice.id == object_id).first()
            if not invoice:
                raise TraceabilityError("supplier invoice not found")
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == invoice.purchase_order_id).first()
            if not po:
                raise TraceabilityError("purchase order not found")
            return po.purchase_request_id
        if normalized == "payment":
            payment = self.db.query(Payment).filter(Payment.id == object_id).first()
            if not payment:
                raise TraceabilityError("payment not found")
            invoice = self.db.query(SupplierInvoice).filter(SupplierInvoice.id == payment.supplier_invoice_id).first()
            if not invoice:
                raise TraceabilityError("supplier invoice not found")
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == invoice.purchase_order_id).first()
            if not po:
                raise TraceabilityError("purchase order not found")
            return po.purchase_request_id
        raise TraceabilityError("unsupported procurement object type")

    def _resolve_sales_order_id(self, object_type: str, object_id: int) -> int:
        normalized = self._normalize_object_type(object_type)
        if normalized in {"salesorder", "so"}:
            return object_id
        if normalized in {"salesdelivery", "delivery", "shipment"}:
            delivery = self.db.query(SalesDelivery).filter(SalesDelivery.id == object_id).first()
            if not delivery:
                raise TraceabilityError("sales delivery not found")
            return delivery.sales_order_id
        if normalized in {"salesinvoice", "arinvoice"}:
            invoice = self.db.query(SalesInvoice).filter(SalesInvoice.id == object_id).first()
            if not invoice:
                raise TraceabilityError("sales invoice not found")
            return invoice.sales_order_id
        if normalized in {"collectionreceipt", "collection"}:
            collection = self.db.query(CollectionReceipt).filter(CollectionReceipt.id == object_id).first()
            if not collection:
                raise TraceabilityError("collection receipt not found")
            invoice = self.db.query(SalesInvoice).filter(SalesInvoice.id == collection.sales_invoice_id).first()
            if not invoice:
                raise TraceabilityError("sales invoice not found")
            return invoice.sales_order_id
        raise TraceabilityError("unsupported sales object type")

    def document_traceability(self, object_type: str, object_id: int) -> TraceabilityResponse:
        normalized = self._normalize_object_type(object_type)
        procurement_types = {
            "purchaserequest",
            "pr",
            "rfq",
            "supplierquotation",
            "quotation",
            "quote",
            "po",
            "purchaseorder",
            "goodsreceipt",
            "grn",
            "receipt",
            "qualityinspection",
            "qc",
            "supplierinvoice",
            "invoice",
            "payment",
        }
        sales_types = {
            "salesorder",
            "so",
            "salesdelivery",
            "delivery",
            "shipment",
            "salesinvoice",
            "arinvoice",
            "collectionreceipt",
            "collection",
        }
        if normalized in procurement_types:
            pr_id = self._resolve_purchase_request_id(object_type, object_id)
            return self.procurement_traceability(pr_id)
        if normalized in sales_types:
            sales_order_id = self._resolve_sales_order_id(object_type, object_id)
            return self.sales_traceability(sales_order_id)
        raise TraceabilityError("unsupported object type")
