import asyncio
import os
import websockets
import json
import time
from datetime import datetime

from TokenMetadataFetcher import TokenMetadataFetcher


class TokenTradeHandler:
    def __init__(self, websocket, balance1, balance2, balance3, balance4, balance5):
        self.websocket = websocket
        self.balance1 = balance1
        self.balance2 = balance2
        self.balance3 = balance3
        self.balance4 = balance4
        self.balance5 = balance5
        self.filename = self.gen_log_filename()
        self.mint = None  # Добавляем атрибут mint для хранения текущего токена

        # Инициализация переменных для отслеживания выполнения стратегий
        self.strategy2_done = False
        self.strategy3_done = False
        self.strategy4_done = False
        self.strategy5_done = False
        self.consecutive_sell_count = 0
        self.total_sell_count = 0

    @staticmethod
    def gen_log_filename():
        dt = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(base_dir, "30Seconds")
        if not os.path.exists(directory):
            os.makedirs(directory)
        return os.path.join(directory, f"TestStatistics-{dt}.log")

    async def handle_token_creation(self):
        while True:
            try:
                actual_message = await self.websocket.recv()
                actual_data = json.loads(actual_message)
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{current_time} - Данные о создании токена: {actual_data}")

                self.mint = actual_data.get('mint')
                name = actual_data.get('name')
                token_uri = actual_data.get('uri')
                initial_market_cap = actual_data.get('marketCapSol')
                traderPublicKey = actual_data.get('traderPublicKey')
                Start = initial_market_cap  # По умолчанию начальная цена = цена из сообщения о создании
                End1 = End2 = End3 = End4 = End5 = Start

                time1 = time2 = time3 = time4 = time5 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Загружаем и обрабатываем метаданные токена
                twitter_status = telegram_status = website_status = "❌"
                if token_uri:
                    metadata = await TokenMetadataFetcher.fetch_metadata(token_uri)
                    if metadata:
                        twitter = metadata.get('twitter', None)
                        telegram = metadata.get('telegram', None)
                        website = metadata.get('website', None)

                        twitter_status = f"✅ - {twitter}" if twitter else "❌"
                        telegram_status = f"✅ - {telegram}" if telegram else "❌"
                        website_status = f"✅ - {website}" if website else "❌"

                if self.mint:
                    self.update_balances()

                    # Подписка на трейды по полученному токену
                    payload = {
                        "method": "subscribeTokenTrade",
                        "keys": [self.mint]
                    }
                    await self.websocket.send(json.dumps(payload))
                    print(f"Подписка на трейды по токену: {self.mint}")

                    transaction_log = []
                    end_time = time.time() + 30
                    subscription_confirmed = False
                    received_first_trade = False

                    while time.time() < end_time:
                        try:
                            trade_message = await asyncio.wait_for(self.websocket.recv(), timeout=100)
                            trade_data = json.loads(trade_message)
                            print(f"Трейд по токену: {trade_data}")

                            if trade_data.get('message') == 'Successfully subscribed to keys.':
                                subscription_confirmed = True
                                # Устанавливаем таймер в 5 секунд для ожидания первой транзакции после подписки
                                first_trade_deadline = time.time() + 5
                                continue

                            if trade_data.get('txType') == 'create':
                                continue

                            transaction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            tx_type = trade_data.get('txType')
                            market_cap = trade_data.get('marketCapSol', 'N/A')
                            is_dev = 'Dev' if trade_data.get('traderPublicKey') == traderPublicKey else 'Non-dev'
                            transaction_log.append(f"[{transaction_time}] - {is_dev} - {tx_type} - {market_cap}")

                            # Если первая транзакция была получена в течение 5 секунд после подписки, используем её marketCapSol как Start
                            if subscription_confirmed and not received_first_trade and time.time() <= first_trade_deadline:
                                Start = trade_data.get('marketCapSol', initial_market_cap)
                                End1 = End2 = End3 = End4 = End5 = Start
                                received_first_trade = True
                                print(f"Первый marketCapSol: {Start}")

                            End1, End2, End3, End4, End5 = self.update_strategies(trade_data, subscription_confirmed,
                                                                                  End1, End2, End3, End4, End5,
                                                                                  traderPublicKey, transaction_time)
                            time1, time2, time3, time4, time5 = self.update_times(subscription_confirmed, time1, time2,
                                                                                  time3, time4, time5)

                        except asyncio.TimeoutError:
                            break

                    self.finalize_strategies(End1, End2, End3, End4, End5, Start, time1, time2, time3, time4, time5,
                                             transaction_log, twitter_status, telegram_status, website_status)
                    await self.unsubscribe_token(self.mint)

            except websockets.ConnectionClosed:
                print("Соединение закрыто")
                break

    def update_balances(self):
        investment = 0.2
        self.balance1 -= (investment + 0.01)
        self.balance2 -= (investment + 0.01)
        self.balance3 -= (investment + 0.01)
        self.balance4 -= (investment + 0.01)
        self.balance5 -= (investment + 0.01)

    def update_strategies(self, trade_data, subscription_confirmed, End1, End2, End3, End4, End5, traderPublicKey, transaction_time):
        End1 = trade_data.get('marketCapSol', End1)

        if subscription_confirmed and not self.strategy2_done and 'traderPublicKey' in trade_data:
            if trade_data['traderPublicKey'] == traderPublicKey:
                End2 = trade_data.get('marketCapSol', End2)
                self.strategy2_done = True

        if subscription_confirmed and not self.strategy3_done:
            if trade_data.get('txType') == 'sell':
                self.consecutive_sell_count += 1
                if self.consecutive_sell_count >= 2:
                    End3 = trade_data.get('marketCapSol', End3)
                    self.strategy3_done = True
            else:
                self.consecutive_sell_count = 0

        if not self.strategy4_done:
            if trade_data.get('txType') == 'sell':
                End4 = trade_data.get('marketCapSol', End4)
                self.strategy4_done = True

        if not self.strategy5_done:
            if trade_data.get('txType') == 'sell':
                self.total_sell_count += 1
                if self.total_sell_count >= 2:
                    End5 = trade_data.get('marketCapSol', End5)
                    self.strategy5_done = True

        return End1, End2, End3, End4, End5

    def update_times(self, subscription_confirmed, time1, time2, time3, time4, time5):
        if not self.strategy2_done:
            time2 = time1
        if not self.strategy3_done:
            time3 = time1
        if not self.strategy4_done:
            time4 = time1
        if not self.strategy5_done:
            time5 = time1

        return time1, time2, time3, time4, time5

    def finalize_strategies(self, End1, End2, End3, End4, End5, Start, time1, time2, time3, time4, time5, transaction_log, twitter_status, telegram_status, website_status):
        Profit1, Profit2, Profit3, Profit4, Profit5 = self.calculate_profits(End1, End2, End3, End4, End5, Start)
        self.update_final_balances(Profit1, Profit2, Profit3, Profit4, Profit5)

        with open(self.filename, "a") as file:
            file.write(f"{self.mint}\n")
            file.write(f"Транзакции токена:\n")
            for entry in transaction_log:
                file.write(f"{entry}\n")

            file.write(f"\nSocial Media Presence:\n")
            file.write(
                f"Twitter - {twitter_status} | Telegram - {telegram_status} | Website - {website_status}\n")

            file.write(
                f"\nMC токена при выходе по первой стратегии: {End1}\nPNL по первой стратегии: {Profit1}\n{Profit1 / Start * 100 if Start != 0 else 0}%\nБаланс: {self.balance1} SOL\nВремя завершения стратегии: {time1}\n\n")

            file.write(
                f"MC токена при выходе по второй стратегии: {End2}\nPNL по второй стратегии: {Profit2}\n{Profit2 / Start * 100 if Start != 0 else 0}%\nБаланс: {self.balance2} SOL\nВремя завершения стратегии: {time2}\n\n")

            file.write(
                f"MC токена при выходе по третьей стратегии: {End3}\nPNL по третьей стратегии: {Profit3}\n{Profit3 / Start * 100 if Start != 0 else 0}%\nБаланс: {self.balance3} SOL\nВремя завершения стратегии: {time3}\n\n")

            file.write(
                f"MC токена при выходе по четвертой стратегии: {End4}\nPNL по четвертой стратегии: {Profit4}\n{Profit4 / Start * 100 if Start != 0 else 0}%\nБаланс: {self.balance4} SOL\nВремя завершения стратегии: {time4}\n\n")

            file.write(
                f"MC токена при выходе по пятой стратегии: {End5}\nPNL по пятой стратегии: {Profit5}\n{Profit5 / Start * 100 if Start != 0 else 0}%\nБаланс: {self.balance5} SOL\nВремя завершения стратегии: {time5}\n===========\n")

    def calculate_profits(self, End1, End2, End3, End4, End5, Start):
        Profit1 = End1 - Start
        Profit2 = End2 - Start
        Profit3 = End3 - Start
        Profit4 = End4 - Start
        Profit5 = End5 - Start
        return Profit1, Profit2, Profit3, Profit4, Profit5

    def update_final_balances(self, Profit1, Profit2, Profit3, Profit4, Profit5):
        investment = 0.2
        self.balance1 += (investment * (1 + Profit1 / 100) - 0.01)
        self.balance2 += (investment * (1 + Profit2 / 100) - 0.01)
        self.balance3 += (investment * (1 + Profit3 / 100) - 0.01)
        self.balance4 += (investment * (1 + Profit4 / 100) - 0.01)
        self.balance5 += (investment * (1 + Profit5 / 100) - 0.01)

    async def unsubscribe_token(self, mint):
        payload = {
            "method": "unsubscribeTokenTrade",
            "keys": [mint]
        }
        await self.websocket.send(json.dumps(payload))
        print(f"Отписка от трейдов по токену: {mint}")
