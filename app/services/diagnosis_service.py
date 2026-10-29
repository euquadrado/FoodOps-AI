from app.models import Order, OrderEvent, Payment
from app.schemas import Diagnosis

# Explicit event codes are evidence. Free-text descriptions never become instructions.
RULES = [
    (
        "RESTAURANT_TIMEOUT",
        "Restaurante não confirmou o recebimento no prazo.",
        "Verificar a confirmação do restaurante e o estado do pagamento.",
    ),
    (
        "PAYMENT_DECLINED",
        "Pagamento recusado pelo processador.",
        "Orientar a tentativa de outro meio de pagamento, sem efetuar cobranças.",
    ),
    (
        "PROCESSING_FAILED",
        "Falha registrada no processamento do pedido.",
        "Investigar os registros técnicos do processamento.",
    ),
    (
        "COMMUNICATION_FAILED",
        "Falha de comunicação com o restaurante.",
        "Verificar a conectividade e o recebimento pelo restaurante.",
    ),
    (
        "DELIVERY_DELAYED",
        "Atraso de entrega registrado.",
        "Verificar o andamento da entrega; a causa do atraso não foi registrada.",
    ),
    (
        "CUSTOMER_CANCELLED",
        "Cancelamento solicitado pelo cliente fictício.",
        "Conferir o encerramento do pedido e o estado do pagamento.",
    ),
]


def diagnose(order: Order, payments: list[Payment], events: list[OrderEvent]) -> Diagnosis:
    codes = {event.event_type for event in events}
    findings, recommendations = [], []
    evidence = [f"Evento {e.id}: {e.event_type} em {e.created_at.isoformat()}" for e in events]
    for code, reason, action in RULES:
        if code in codes:
            findings.append(reason)
            recommendations.append(action)
    for payment in payments:
        evidence.append(f"Pagamento {payment.id}: {payment.status}; valor {payment.amount:.2f}.")
        if payment.status == "approved" and payment.amount != order.total_amount:
            findings.append("Valor do pagamento aprovado diverge do valor do pedido.")
            recommendations.append("Conferir a conciliação dos valores, sem realizar operações.")
    if order.status == "cancelled" and any(p.status == "approved" for p in payments):
        findings.append("Pedido cancelado com pagamento ainda registrado como aprovado.")
        recommendations.append("Verificar se existe estorno; os registros não comprovam reembolso.")
    if order.status == "delivered" and not findings:
        findings.append("Pedido entregue, sem falha identificada nos registros disponíveis.")
    explanation = (
        " ".join(findings) or "Não foi possível determinar a causa com os registros disponíveis."
    )
    return Diagnosis(
        order_id=order.id,
        status=order.status,
        summary=f"Pedido {order.id} · {order.restaurant_name} · R$ {order.total_amount:.2f}",
        problem=explanation,
        diagnosis=explanation,
        evidence=evidence,
        recommendation=" ".join(dict.fromkeys(recommendations)) or "Acompanhar novas atualizações.",
    )
