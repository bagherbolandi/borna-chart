from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.master import Customer
from app.models.sales import PriceList, Product, SalesOrder
from app.models.workflow import WorkflowInstance
from app.services.alert_service import AlertService
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.config_registry import ConfigRegistry
from app.services.workflow_service import WorkflowService


class SalesFlowError(Exception):
    pass


class PricingSalesService:
    def __init__(self, db: Session, registry: ConfigRegistry) -> None:
        self.db = db
        self.registry = registry
        self.workflow = WorkflowService(db, registry)
        self.alerts = AlertService(db)
        self.approvals = ApprovalService(db)
        self.audit = AuditService(db)

    def _next_code(self, model, prefix: str) -> str:
        last = self.db.query(model).order_by(model.id.desc()).first()
        next_no = 1 if not last else last.id + 1
        return f"{prefix}-{next_no:06d}"

    def _get_product(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def _get_customer(self, customer_id: int) -> Customer | None:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()

    def _get_price_list(self, price_list_id: int) -> PriceList | None:
        return self.db.query(PriceList).filter(PriceList.id == price_list_id).first()

    def _get_sales_order(self, sales_order_id: int) -> SalesOrder | None:
        return self.db.query(SalesOrder).filter(SalesOrder.id == sales_order_id).first()

    def get_workflow_instance(self, workflow_instance_id: int | None) -> WorkflowInstance | None:
        if not workflow_instance_id:
            return None
        return self.db.query(WorkflowInstance).filter(WorkflowInstance.id == workflow_instance_id).first()

    def list_price_lists(self) -> list[PriceList]:
        return self.db.query(PriceList).order_by(PriceList.id.desc()).all()

    def get_price_list(self, price_list_id: int) -> PriceList | None:
        return self._get_price_list(price_list_id)

    def list_sales_orders(self) -> list[SalesOrder]:
        return self.db.query(SalesOrder).order_by(SalesOrder.id.desc()).all()

    def get_sales_order(self, sales_order_id: int) -> SalesOrder | None:
        return self._get_sales_order(sales_order_id)

    def create_price_list(self, payload) -> PriceList:
        product = self._get_product(payload.product_id)
        if not product:
            raise SalesFlowError("product not found")
        if payload.customer_id is not None and not self._get_customer(payload.customer_id):
            raise SalesFlowError("customer not found")
        if payload.cost_basis <= 0:
            raise SalesFlowError("PRC-001: approved cost basis is required")
        if payload.approved_min_price <= 0:
            raise SalesFlowError("approved minimum price is required")
        if payload.proposed_price <= 0:
            raise SalesFlowError("proposed price must be positive")

        price_list = PriceList(
            code=self._next_code(PriceList, "PRC"),
            product_id=payload.product_id,
            customer_id=payload.customer_id,
            pricing_method=payload.pricing_method,
            cost_basis=Decimal(str(payload.cost_basis)),
            target_margin_pct=Decimal(str(payload.target_margin_pct)),
            logistics_cost=Decimal(str(payload.logistics_cost)),
            financial_cost=Decimal(str(payload.financial_cost)),
            risk_cost=Decimal(str(payload.risk_cost)),
            proposed_price=Decimal(str(payload.proposed_price)),
            approved_min_price=Decimal(str(payload.approved_min_price)),
            valid_from=payload.valid_from.isoformat(),
            valid_to=payload.valid_to.isoformat() if payload.valid_to else None,
            status="pricing_review",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(price_list)
        self.db.flush()
        instance = self.workflow.create_instance(
            process_name="sales",
            object_type="PriceList",
            object_id=price_list.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(payload.proposed_price),
            initial_state="pricing_review",
        )
        price_list.workflow_instance_id = instance.id
        self.audit.log(
            user_name=payload.actor,
            entity_name="price_lists",
            entity_id=str(price_list.id),
            action="create",
            new_value=price_list.code,
            reason=f"product {product.code}",
        )
        self.db.commit()
        self.db.refresh(price_list)
        return price_list

    def approve_price_list(self, price_list_id: int, actor: str, actor_role: str, note: str | None = None) -> PriceList:
        price_list = self._get_price_list(price_list_id)
        if not price_list:
            raise SalesFlowError("price list not found")
        if price_list.status != "pricing_review":
            raise SalesFlowError("only pricing review price list can be approved")
        instance = self.get_workflow_instance(price_list.workflow_instance_id)
        if not instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="sales",
            action="approve_price",
            actor=actor,
            actor_role=actor_role,
        )
        price_list.status = "price_approved"
        price_list.modified_by = actor
        self.approvals.record(
            object_type="PriceList",
            object_id=price_list.id,
            approval_stage="pricing",
            approver_name=actor,
            approver_role=actor_role,
            decision="approved",
            decision_note=note,
        )
        self.audit.log(
            user_name=actor,
            entity_name="price_lists",
            entity_id=str(price_list.id),
            action="approve_price",
            old_value="pricing_review",
            new_value="price_approved",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(price_list)
        return price_list

    def create_sales_order(self, payload) -> SalesOrder:
        customer = self._get_customer(payload.customer_id)
        if not customer:
            raise SalesFlowError("customer not found")
        product = self._get_product(payload.product_id)
        if not product:
            raise SalesFlowError("product not found")
        price_list = self._get_price_list(payload.price_list_id)
        if not price_list:
            raise SalesFlowError("price list not found")
        if price_list.status != "price_approved":
            raise SalesFlowError("PRC-001: sales order requires approved price list")
        if price_list.product_id != payload.product_id:
            raise SalesFlowError("price list does not belong to product")
        if price_list.customer_id is not None and price_list.customer_id != payload.customer_id:
            raise SalesFlowError("price list does not belong to customer")

        total_amount = Decimal(str(payload.qty)) * Decimal(str(payload.unit_price))
        below_floor = Decimal(str(payload.unit_price)) < price_list.approved_min_price

        sales_order = SalesOrder(
            code=self._next_code(SalesOrder, "SO"),
            customer_id=payload.customer_id,
            product_id=payload.product_id,
            price_list_id=payload.price_list_id,
            sales_owner=payload.actor,
            order_date=payload.order_date.isoformat(),
            requested_delivery_date=payload.requested_delivery_date.isoformat() if payload.requested_delivery_date else None,
            qty=Decimal(str(payload.qty)),
            unit_price=Decimal(str(payload.unit_price)),
            total_amount=total_amount,
            credit_check_status="pending",
            pricing_status="below_floor" if below_floor else "approved",
            status="credit_check",
            created_by=payload.actor,
            modified_by=payload.actor,
        )
        self.db.add(sales_order)
        self.db.flush()

        instance = self.workflow.create_instance(
            process_name="sales",
            object_type="SalesOrder",
            object_id=sales_order.id,
            current_owner=payload.actor,
            current_role=payload.actor_role,
            financial_impact=float(total_amount),
            initial_state="credit_check",
        )
        sales_order.workflow_instance_id = instance.id
        if below_floor:
            self.alerts.create(
                alert_code="SALES-BELOW-FLOOR",
                related_object_type="SalesOrder",
                related_object_id=sales_order.id,
                alert_type="Sales Below Floor",
                severity="high",
                owner=payload.actor,
                financial_impact=float(total_amount),
                created_by=payload.actor,
                message="Sales order created below approved minimum price and requires approval confirmation.",
            )
        self.audit.log(
            user_name=payload.actor,
            entity_name="sales_orders",
            entity_id=str(sales_order.id),
            action="create",
            new_value=sales_order.code,
            reason=f"customer {customer.code}",
        )
        self.db.commit()
        self.db.refresh(sales_order)
        return sales_order

    def _customer_exposure(self, customer_id: int, exclude_sales_order_id: int | None = None) -> Decimal:
        query = self.db.query(SalesOrder).filter(SalesOrder.customer_id == customer_id, SalesOrder.status != "closed")
        if exclude_sales_order_id is not None:
            query = query.filter(SalesOrder.id != exclude_sales_order_id)
        total = Decimal("0")
        for row in query.all():
            total += Decimal(str(row.total_amount))
        return total

    def confirm_sales_order(self, sales_order_id: int, actor: str, actor_role: str, note: str | None = None) -> SalesOrder:
        so = self._get_sales_order(sales_order_id)
        if not so:
            raise SalesFlowError("sales order not found")
        if so.status != "credit_check":
            raise SalesFlowError("only credit check sales order can be confirmed")
        customer = self._get_customer(so.customer_id)
        if not customer:
            raise SalesFlowError("customer not found")
        price_list = self._get_price_list(so.price_list_id)
        if not price_list:
            raise SalesFlowError("price list not found")
        if so.sales_owner == actor:
            raise SalesFlowError("SOD-001: sales creator cannot be final approver for the same sales order")

        exposure = self._customer_exposure(customer.id, exclude_sales_order_id=so.id)
        new_exposure = exposure + Decimal(str(so.total_amount))
        if customer.credit_status != "open" or new_exposure > Decimal(str(customer.credit_limit)):
            self.alerts.create(
                alert_code="CREDIT-LIMIT",
                related_object_type="SalesOrder",
                related_object_id=so.id,
                alert_type="Credit Limit Exceeded",
                severity="high",
                owner=actor,
                financial_impact=float(so.total_amount),
                created_by=actor,
                message="Customer credit limit exceeded. Sales order confirmation is blocked.",
            )
            so.credit_check_status = "blocked"
            so.modified_by = actor
            self.db.commit()
            raise SalesFlowError("SAL-001: customer credit limit exceeded or credit status is blocked")

        if Decimal(str(so.unit_price)) < Decimal(str(price_list.approved_min_price)):
            self.alerts.create(
                alert_code="SALES-BELOW-FLOOR",
                related_object_type="SalesOrder",
                related_object_id=so.id,
                alert_type="Sales Below Floor",
                severity="medium",
                owner=actor,
                financial_impact=float(so.total_amount),
                created_by=actor,
                message="Sales order confirmed below approved minimum price by manager approval.",
            )

        instance = self.get_workflow_instance(so.workflow_instance_id)
        if not instance:
            raise SalesFlowError("workflow instance not found")
        self.workflow.apply_transition(
            instance=instance,
            process_name="sales",
            action="confirm_so",
            actor=actor,
            actor_role=actor_role,
        )
        so.credit_check_status = "passed"
        so.status = "sales_order_confirmed"
        so.modified_by = actor
        self.approvals.record(
            object_type="SalesOrder",
            object_id=so.id,
            approval_stage="sales_confirm",
            approver_name=actor,
            approver_role=actor_role,
            decision="approved",
            decision_note=note,
        )
        self.audit.log(
            user_name=actor,
            entity_name="sales_orders",
            entity_id=str(so.id),
            action="confirm",
            old_value="credit_check",
            new_value="sales_order_confirmed",
            reason=note,
        )
        self.db.commit()
        self.db.refresh(so)
        return so
