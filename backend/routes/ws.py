from fastapi import APIRouter, WebSocket
from security.Authorization import Authorization
from services.orderBookManager import gateway


router = APIRouter(prefix="/ws")



@router.websocket("/")
async def connect_websocket(websocket: WebSocket):
    token = Authorization.create_token(1)
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(
            code=1008,
            reason="Missing token"
        )
        return

    try:
        user_id = Authorization.check_token(token)

        if user_id is None:
            await websocket.close(
                code=1008,
                reason="Invalid token"
            )
            return

        await gateway.handle_client(
            websocket,
            user_id
        )

    except Exception as e:
        await websocket.close(
            code=1011,
            reason="Internal server error"
        )