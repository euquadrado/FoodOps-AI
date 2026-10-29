from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, OrderEvent, Payment
from app.schemas import EventOut, OrderOut, PaymentOut
from app.services.diagnosis_service import diagnose


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    order_id: int = Field(gt=0, le=2147483647)


class OrderTools:
    def __init__(self, db: Session):
        self.db = db

    def get_order_details(self, order_id):
        order = self.db.get(Order, order_id)
        return OrderOut.model_validate(order).model_dump(mode="json") if order else None

    def get_order_payment(self, order_id):
        rows = self.db.scalars(
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at, Payment.id)
        ).all()
        return [PaymentOut.model_validate(p).model_dump(mode="json") for p in rows]

    def get_order_events(self, order_id):
        rows = self.db.scalars(
            select(OrderEvent)
            .where(OrderEvent.order_id == order_id)
            .order_by(OrderEvent.created_at, OrderEvent.id)
        ).all()
        return [EventOut.model_validate(e).model_dump(mode="json") for e in rows]

    def get_order_diagnosis(self, order_id):
        order = self.db.get(Order, order_id)
        if order is None:
            return None
        payments = self.db.scalars(select(Payment).where(Payment.order_id == order_id)).all()
        events = self.db.scalars(
            select(OrderEvent)
            .where(OrderEvent.order_id == order_id)
            .order_by(OrderEvent.created_at, OrderEvent.id)
        ).all()
        return diagnose(order, payments, events).model_dump(mode="json")

    def execute(self, name, arguments):
        if name not in TOOL_NAMES:
            return {"ok": False, "error": "unknown_tool"}
        try:
            args = ToolArgs.model_validate(arguments)
        except ValidationError:
            return {"ok": False, "error": "invalid_arguments"}
        if self.db.get(Order, args.order_id) is None:
            return {"ok": False, "error": "order_not_found", "order_id": args.order_id}
        return {"ok": True, "data": getattr(self, name)(args.order_id)}


TOOL_NAMES = ("get_order_details", "get_order_payment", "get_order_events", "get_order_diagnosis")
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": name,
        "description": f"Consulta somente leitura: {name}.",
        "parameters": ToolArgs.model_json_schema(),
        "strict": True,
    }
    for name in TOOL_NAMES
]
