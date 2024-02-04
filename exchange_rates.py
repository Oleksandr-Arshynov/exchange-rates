import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import argparse
from aiofile import AIOFile

class CurrencyFetcher:
    API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='

    def __init__(self, days, currencies, log_file):
        self.days = days
        self.currencies = currencies
        self.log_file = log_file

    async def fetch(self, session, date):
        async with session.get(self.API_URL + date.strftime('%d.%m.%Y')) as response:
            if response.content_type == 'application/json':
                return await response.json()
            else:
                raise ValueError(f"Unexpected content type: {response.content_type}")

    async def get_exchange_rates(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, (datetime.now() - timedelta(days=i))) for i in range(self.days)]
            return await asyncio.gather(*tasks)

    def parse_response(self, response):
        rates = {}
        currency_info = response.get('exchangeRate')
        if currency_info:
            for rate_info in currency_info:
                currency = rate_info.get('currency')
                if currency in self.currencies:
                    rates[currency] = {
                        'sale': rate_info.get('saleRate'),
                        'purchase': rate_info.get('purchaseRate')
                    }
        return rates

    def format_result(self, date, rates):
        return {date.strftime('%d.%m.%Y'): {currency: rate for currency, rate in rates.items()}}

    async def run(self):
        responses = await self.get_exchange_rates()

        results = []
        for i in range(len(responses)):
            date = datetime.now() - timedelta(days=i)
            rates = self.parse_response(responses[i])
            results.append(self.format_result(date, rates))

        # Логуємо команду exchange до файлу
        async with AIOFile(self.log_file, mode='a') as afp:
            await afp.write(f"exchange command executed at {datetime.now()}\n")

        return results

async def handle_exchange_command(websocket, command, log_file):
    try:
        _, days_str, *currencies = command.split()
        days = int(days_str)
        if days > 10:
            await websocket.send("Error: Cannot fetch exchange rates for more than 10 days.")
            return

        currency_fetcher = CurrencyFetcher(days, currencies, log_file)
        results = await currency_fetcher.run()
        response = json.dumps(results, indent=2, ensure_ascii=False)

        # Логуємо команду exchange до файлу
        async with AIOFile(log_file, mode='a') as afp:
            await afp.write(f"exchange command executed at {datetime.now()}\n")

        await websocket.send(response)
    except (ValueError, IndexError):
        await websocket.send("Invalid command format for exchange. Please use 'exchange <days> <currency1> <currency2> ...'")

async def hello(websocket, path, log_file):
    while True:
        command = await websocket.recv()
        print(f"<<< {command}")

        if command.lower().startswith("exchange "):
            await handle_exchange_command(websocket, command, log_file)
        else:
            await websocket.send("Unknown command")

async def main():
    parser = argparse.ArgumentParser(description='Fetch exchange rates from PrivatBank API')
    parser.add_argument('days', type=int, help='Number of days to fetch exchange rates (up to 10 days)')
    parser.add_argument('currencies', nargs='+', help='List of currencies to fetch (e.g., EUR USD)')
    parser.add_argument('--log_file', default='exchange_log.txt', help='File to log exchange commands')
    args = parser.parse_args()

    if args.days > 10:
        print("Error: Cannot fetch exchange rates for more than 10 days.")
        return

    currency_fetcher = CurrencyFetcher(args.days, args.currencies, args.log_file)
    results = await currency_fetcher.run()
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
