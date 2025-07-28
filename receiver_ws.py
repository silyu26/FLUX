import asyncio
import websockets
import json
from datetime import datetime

async def handler(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received at {datetime.now().isoformat()}: {data}")
    except websockets.ConnectionClosed:
        print("Client disconnected.")

async def main():
    async with websockets.serve(handler, host="0.0.0.0", port=5000):
        print("Server listening on port 5000...")
        await asyncio.Future() 

if __name__ == "__main__":
    asyncio.run(main())
