import asyncio
import websockets
import json
from datetime import datetime
from websockets.asyncio.server import serve

async def handler(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received at {datetime.now().isoformat()}")
    except websockets.ConnectionClosed:
        print("Client disconnected.")

async def main():
    async with serve(handler, "0.0.0.0", 5000) as server:
        print("Server listening on port 5000...")
        await server.serve_forever() 

if __name__ == "__main__":
    asyncio.run(main())
