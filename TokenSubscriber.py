import asyncio
import json

import websockets

from TokenTradeHandler import TokenTradeHandler


class TokenSubscriber:
    def __init__(self, uri):
        self.uri = uri

    async def subscribe(self):
        balance1 = 2.0
        balance2 = 2.0
        balance3 = 2.0
        balance4 = 2.0
        balance5 = 2.0

        async with websockets.connect(self.uri) as websocket:
            payload = {
                "method": "subscribeNewToken",
            }
            await websocket.send(json.dumps(payload))

            await websocket.recv()

            handler = TokenTradeHandler(websocket, balance1, balance2, balance3, balance4, balance5)
            await handler.handle_token_creation()


if __name__ == "__main__":
    uri = "wss://pumpportal.fun/api/data"
    subscriber = TokenSubscriber(uri)
    asyncio.run(subscriber.subscribe())