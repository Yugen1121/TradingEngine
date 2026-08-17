from fastapi import APIRouter, Header, HTTPException
from services.orderBookManager import orderRoute
from Models.typeModels import Order as reqOrder
from Models.model import Orders
from security.Authorization import Authorization
router = APIRouter(prefix="/order")


@router.post("/sell")
async def sell(order: reqOrder, authorization: str = Header(...)):
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
        await orderRoute.order_handler(new_order)
        return {"status": 205, "message": "order received"}
    except Exception as e:
        return {"error": 400, "error": str(e)}

@router.post("/buy")
async def buy(order: reqOrder, authorization: str = Header(...)):
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
        await orderRoute.order_handler(new_order)
        return {"status": 205, "message": "order received"}
        
    except Exception as e:
        return {"status": 400, "error": str(e)}

@router.put("/")
async def update():
    pass

@router.delete("/cancel")
async def cancle(orderid: int, authorization: str = Header(...)):
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
        
        x = await orderRoute.cancel_order(user_id, orderid)

        return {"status": 205, "message": "order cancelled"}
        
    except Exception as e:
        return {"status": 400, "error": str(e)}