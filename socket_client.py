import asyncio
import websockets

async def hello():
    uri = "ws://localhost:8200"
    async with websockets.connect(uri) as websocket:
        name = input("What's your name? ")

        await websocket.send(name)
        print(f">>> {name}")

        while True:
            command = input("Enter command: ")
            await websocket.send(command)
            if command.lower() == "exit":
                break

            response = await websocket.recv()
            print(f"<<< {response}")

if __name__ == "__main__":
    asyncio.run(hello())
