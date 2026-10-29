"""Seed idempotente: insere apenas IDs ausentes; nunca apaga dados existentes."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Order, OrderEvent, Payment

SCENARIOS = [
    (
        "cancelled",
        "approved",
        ["PAYMENT_APPROVED", "SENT_TO_RESTAURANT", "RESTAURANT_TIMEOUT", "ORDER_CANCELLED"],
    ),
    ("cancelled", "declined", ["PAYMENT_DECLINED", "ORDER_CANCELLED"]),
    ("delivered", "approved", ["PAYMENT_APPROVED", "RESTAURANT_CONFIRMED", "ORDER_DELIVERED"]),
    ("awaiting_confirmation", "approved", ["PAYMENT_APPROVED", "SENT_TO_RESTAURANT"]),
    ("delayed", "approved", ["PAYMENT_APPROVED", "RESTAURANT_CONFIRMED", "DELIVERY_DELAYED"]),
    ("failed", "pending", ["PROCESSING_FAILED"]),
    (
        "cancelled",
        "refunded",
        ["PAYMENT_APPROVED", "CUSTOMER_CANCELLED", "ORDER_CANCELLED", "PAYMENT_REFUNDED"],
    ),
    ("failed", "approved", ["PAYMENT_APPROVED", "COMMUNICATION_FAILED"]),
    ("processing", "approved", ["PAYMENT_APPROVED"]),  # divergence in amount
    ("cancelled", "pending", ["ORDER_CANCELLED"]),  # unknown reason
]
DESCRIPTIONS = {
    "ORDER_CREATED": "Pedido fictício criado.",
    "PAYMENT_APPROVED": "Processador simulou aprovação.",
    "SENT_TO_RESTAURANT": "Pedido enviado ao restaurante fictício.",
    "RESTAURANT_TIMEOUT": "Prazo de confirmação de 15 minutos excedido.",
    "ORDER_CANCELLED": "Pedido encerrado como cancelado.",
    "PAYMENT_DECLINED": "Processador simulou recusa, sem motivo detalhado.",
    "RESTAURANT_CONFIRMED": "Restaurante confirmou o pedido.",
    "ORDER_DELIVERED": "Entrega fictícia concluída.",
    "DELIVERY_DELAYED": "Entrega com atraso; causa não informada.",
    "PROCESSING_FAILED": "Falha técnica simulada no processamento.",
    "CUSTOMER_CANCELLED": "Cliente fictício solicitou cancelamento.",
    "PAYMENT_REFUNDED": "Processador simulou estorno concluído.",
    "COMMUNICATION_FAILED": "Comunicação com restaurante falhou.",
}


def seed(db: Session):
    base = datetime(2026, 1, 15, 19, 20, tzinfo=timezone.utc)
    inserted = 0
    for offset in range(100):
        order_id = 1052 + offset
        if db.get(Order, order_id):
            continue
        scenario = offset % len(SCENARIOS)
        status, payment_status, codes = SCENARIOS[scenario]
        start = base + timedelta(days=offset // 10)
        amount = Decimal("45.90") + Decimal(offset)
        timeline = [("ORDER_CREATED", 0)]
        for index, code in enumerate(codes, 1):
            minute = 17 if code == "RESTAURANT_TIMEOUT" else index
            if code == "ORDER_CANCELLED" and scenario == 0:
                minute = 18
            timeline.append((code, minute))
        db.add(
            Order(
                id=order_id,
                customer_name=f"Cliente Fictício {offset + 1}",
                restaurant_name=f"Cozinha Simulada {offset % 5 + 1}",
                total_amount=amount,
                status=status,
                created_at=start,
                updated_at=start + timedelta(minutes=max(m for _, m in timeline)),
            )
        )
        db.flush()
        db.add(
            Payment(
                order_id=order_id,
                payment_method="pix" if offset % 2 else "card",
                amount=amount - Decimal("10") if scenario == 8 else amount,
                status=payment_status,
                created_at=start + timedelta(minutes=1),
            )
        )
        for code, minute in timeline:
            db.add(
                OrderEvent(
                    order_id=order_id,
                    event_type=code,
                    description=DESCRIPTIONS[code],
                    created_at=start + timedelta(minutes=minute),
                )
            )
        inserted += 1
    db.commit()
    return inserted


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        print(f"Pedidos inseridos: {seed(session)}")
