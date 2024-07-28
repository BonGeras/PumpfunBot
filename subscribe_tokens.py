import asyncio
import websockets
import json


async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            data = json.loads(message)
            required_keys = ['symbol', 'name', 'mint']

            if all(key in data for key in required_keys):
                log_data = f"""
${data['symbol']}
{data['name']}
{data['mint']}
https://pump.fun/{data['mint']}
"""
                with open("token_contract_addresses.txt", "a") as file:
                    file.write(log_data)
            else:
                print(f"Missing keys in received data: {data}")

# TODO:
#  1. Wallet connection
#  2. Trade mechanism
#  3. Time complexity optimisation
#  4. rugcheck.xyz support(?)
#   На данном этапе нету особого смысла подключается api rugcheck.xyz, так
#    так как мы просто пылесосим все токены, а проверка не может быстро проверять
#    токены и отвечать на все запросы. Эту функцию можно будет добавить для других
#    токенов уже в будущем, но это будет уже другой бот


asyncio.get_event_loop().run_until_complete(subscribe())
