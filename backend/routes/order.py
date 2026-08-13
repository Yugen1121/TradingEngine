from fastapi import APIRouter, Header, HTTPException
from services.orderBookManager import orderRoute
from Models.typeModels import Order as reqOrder
from Models.model import Orders
from security.Authorization import Authorization
router = APIRouter(prefix="/order")


@router.post("/sell")
def sell(order: reqOrder, authorization: str = Header(...)):
    try:
        parts = authorization.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header"
            )
        token = parts[1]
        user_id = Authorization.check_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Unauthorized request")

        new_order = Orders(
            id=orderRoute.getNewId(),
            user_id=user_id,
            price=order.price,
            type= "sell",
            order_type=order.orderType,
            quantity=order.quantity,
            stock=order.symbol
        )
        orderRoute.order_handler(new_order)
        
    except Exception as e:
        raise

@router.post("/buy")
def buy(order: reqOrder, authorization: str = Header(...)):
    try:
        parts = authorization.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header"
            )
        token = parts[1]
        user_id = Authorization.check_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Unauthorized request")

        new_order = Orders(
            id=orderRoute.getNewId(),
            user_id=user_id,
            price=order.price,
            type= "buy",
            order_type=order.orderType,
            quantity=order.quantity,
            stock=order.symbol
        )
        orderRoute.order_handler(new_order)
        
    except Exception as e:
        raise

@router.put("/")
async def update():
    pass

@router.delete("/")
async def cancle():
    pass