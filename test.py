import asyncio
import websockets
import json
import time


async def handle_token_creation(websocket, balance):
    while True:
        try:
            # Получаем данные о новом токене
            actual_message = await websocket.recv()
            actual_data = json.loads(actual_message)
            print(f"Данные о создании токена: {actual_data}")

            # Извлечение необходимых данных
            mint = actual_data.get('mint')
            name = actual_data.get('name')
            Start = actual_data.get('marketCapSol')
            End = Start  # Изначально End равно Start

            if mint:
                # Уменьшение баланса на 0.21 SOL (0.2 SOL инвестиции + 0.01 SOL комиссия)
                investment = 0.2
                balance -= (investment + 0.01)
                print(f"Инвестировано 0.2 SOL в {name}. Текущий баланс: {balance} SOL")

                # Подписка на трейды по полученному токену
                payload = {
                    "method": "subscribeTokenTrade",
                    "keys": [mint]  # подписываемся на трейды по токену
                }
                await websocket.send(json.dumps(payload))
                print(f"Подписка на трейды по токену: {mint}")

                # Сбор данных в течение 30 секунд
                end_time = time.time() + 30
                while time.time() < end_time:
                    try:
                        trade_message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        trade_data = json.loads(trade_message)
                        print(f"Трейд по токену: {trade_data}")

                        # Обновление End
                        End = trade_data.get('marketCapSol', End)
                    except asyncio.TimeoutError:
                        break

                # Вычисление Profit и Profit_percent
                Profit = End - Start
                Profit_percent = (Profit / Start) * 100 if Start != 0 else 0

                # Расчет полученной прибыли в SOL
                profit_in_sol = investment * (1 + Profit_percent / 100)

                # Обновление баланса (вычитаем 0.01 SOL комиссии и добавляем прибыль)
                balance += (profit_in_sol - 0.01)
                print(f"Прибыль: {Profit_percent}% ({profit_in_sol} SOL). Текущий баланс: {balance} SOL")

                # Запись данных в файл
                with open("TestRunDevJeeted.txt", "a") as file:
                    file.write(
                        f"{mint}\n{name}\n{Start}\n{End}\n{Profit}\n{Profit_percent}%\nБаланс: {balance} SOL\n===========\n")

                # Отписка от трейдов по токену
                payload = {
                    "method": "unsubscribeTokenTrade",
                    "keys": [mint]
                }
                await websocket.send(json.dumps(payload))
                print(f"Отписка от трейдов по токену: {mint}")

        except websockets.ConnectionClosed:
            print("Соединение закрыто")
            break


async def subscribe_to_new_tokens():
    uri = "wss://pumpportal.fun/api/data"
    balance = 2.0  # Изначальный баланс 2 SOL

    async with websockets.connect(uri) as websocket:
        # Подписка на события создания токенов
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))

        # Игнорирование первого сообщения (подтверждение подписки)
        await websocket.recv()

        # Обработка каждого нового токена
        await handle_token_creation(websocket, balance)


# Запуск функции подписки на новые токены
asyncio.run(subscribe_to_new_tokens())
