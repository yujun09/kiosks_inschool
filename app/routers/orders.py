from fastapi import APIRouter, HTTPException

from app import store
from app.models import Order, OrderCreate

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=Order)
def place_order(order_in: OrderCreate) -> Order:
    if not order_in.items:
        raise HTTPException(status_code=400, detail="장바구니가 비어 있습니다.")
    try:
        return store.create_order(order_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{order_id}", response_model=Order)
def read_order(order_id: str) -> Order:
    order = store.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order
