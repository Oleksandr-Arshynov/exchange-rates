import asyncio
import websockets
import json
from aiofile import AIOFile
from aiopath import AsyncPath
from exchange_rates import CurrencyFetcher

async def hello(websocket):
    name = await websocket.recv()
    print(f"<<< {name}")

    greeting = f"Hello {name}!"
    await websocket.send(greeting)
    print(f">>> {greeting}")

    while True:
        try:
            command = await websocket.recv()
            await handle_command(websocket, command)
        except websockets.ConnectionClosed:
            break

async def handle_command(websocket, command):
    if command.startswith("exchange"):
        await handle_exchange(websocket, command)

async def handle_exchange(websocket, command):
    try:
        _, days_str = command.split(" ")
        days = int(days_str)
        
        currency_fetcher = CurrencyFetcher(days=days, currencies=['USD', 'EUR'], log_file='your_log_file.txt')  
        results = await currency_fetcher.get_exchange_rates()
        
        response = json.dumps(results, indent=2, ensure_ascii=False)
    except ValueError:
        response = "Invalid command format. Please use 'exchange <days>'"

    await websocket.send(response)
    print(f">>> {response}")

async def main():
    async with websockets.serve(hello, "localhost", 8200):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
