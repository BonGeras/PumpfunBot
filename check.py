import asyncio
import websockets
import json
import aiohttp

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            data = json.loads(message)
            required_keys = ['symbol', 'name', 'mint']

            if all(key in data for key in required_keys):
                mint_address = data['mint']
                score = await get_risk_score(mint_address)
                log_data = f"""
${data['symbol']} - {score}
{data['name']}
{data['mint']}
https://pump.fun/{data['mint']}
"""
                with open("token_contract_addresses.txt", "a") as file:
                    file.write(log_data)
            else:
                print(f"Missing keys in received data: {data}")

async def get_risk_score(mint_address):
    url = f"https://api.rugcheck.xyz/v1/tokens/{mint_address}/report/summary"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    summary = await response.json()
                    return summary.get('score', 'N/A')
                else:
                    print(f"Unexpected Content-Type: {content_type} for {url}")
            else:
                print(f"Failed to fetch score for {mint_address}, status code: {response.status}")
    return 'N/A'


asyncio.get_event_loop().run_until_complete(subscribe())


#   Вот тут я добавил эту функцию, но проблемы все те же, а именно:
#   1. Замедление бота ожиданием ответа и дополнительными линиями кода с вызовами проверки
#   2. Лимит количества запросов
#   3. Неточность получаемых данных (будет слишком муторно и медленно вручную смотреть каждый лог
# и принимать решение по каждому говнотокену. Надо быстро забрать свои 5-15 процентов и по съебам