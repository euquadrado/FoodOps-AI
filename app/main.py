from fastapi import Depends, FastAPI, HTTPException, Query
from openai import OpenAIError
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Order, Payment
from app.schemas import DiagnoseRequest, Diagnosis, EventOut, OrderOut, PaymentOut
from app.services.agent_service import AgentError, AgentService, InvalidQuestion
from app.tools.order_tools import OrderTools

app = FastAPI(title="FoodOps AI", version="0.1.0")


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Banco de dados indisponível."})


@app.get("/health")
def health(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "mode": settings.active_mode}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    declined = db.scalar(
        select(func.count(func.distinct(Payment.order_id))).where(Payment.status == "declined")
    )
    return {
        "total": sum(counts.values()),
        "delivered": counts.get("delivered", 0),
        "cancelled": counts.get("cancelled", 0),
        "declined_payments": declined,
    }


@app.get("/orders", response_model=list[OrderOut])
def orders(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Order).order_by(Order.id).offset(offset).limit(limit)).all()


def require_order(order_id, db):
    if order_id <= 0 or order_id > 2147483647:
        raise HTTPException(422, "Número de pedido inválido.")
    if db.get(Order, order_id) is None:
        raise HTTPException(404, "Pedido não encontrado.")


@app.get("/orders/{order_id}", response_model=OrderOut)
def order_details(order_id: int, db: Session = Depends(get_db)):
    require_order(order_id, db)
    return OrderTools(db).get_order_details(order_id)


@app.get("/orders/{order_id}/events", response_model=list[EventOut])
def order_events(order_id: int, db: Session = Depends(get_db)):
    require_order(order_id, db)
    return OrderTools(db).get_order_events(order_id)


@app.get("/orders/{order_id}/payments", response_model=list[PaymentOut])
def order_payments(order_id: int, db: Session = Depends(get_db)):
    require_order(order_id, db)
    return OrderTools(db).get_order_payment(order_id)


@app.post("/agent/diagnose", response_model=Diagnosis)
def agent(
    body: DiagnoseRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    try:
        return AgentService(OrderTools(db), settings).run(body.message)
    except InvalidQuestion as exc:
        raise HTTPException(422, str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except (OpenAIError, AgentError):
        raise HTTPException(503, "IA indisponível ou resposta não fundamentada. Tente DEMO.")
