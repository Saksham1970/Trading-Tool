# quote_client.py
import asyncio
import websockets
import json


async def connect_and_listen():
    uri = "ws://localhost:8765"

    async with websockets.connect(uri) as websocket:
        print("Connected to the websocket server")

        try:
            while True:
                message = await websocket.recv()
                try:
                    data = json.loads(message)
                    print(f"Received data: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Received message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("Connection to the server was closed")


asyncio.get_event_loop().run_until_complete(connect_and_listen())
