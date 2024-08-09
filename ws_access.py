import socketio
import asyncio
import json

sio = socketio.AsyncClient(logger=True, engineio_logger=True)


@sio.event(namespace="/quotes")
async def connect():
    print("Connected to the SocketIO server on namespace /quotes")


@sio.event(namespace="/quotes")
async def connect_error(data):
    print(f"Connection failed on namespace /quotes: {data}")


@sio.event(namespace="/quotes")
async def disconnect():
    print("Disconnected from the SocketIO server on namespace /quotes")


@sio.on("quote", namespace="/quotes")
async def on_quote(data):
    try:
        quote = json.loads(data) if isinstance(data, str) else data
        print(f"Received quote: {quote}")
    except json.JSONDecodeError:
        print(f"Received non-JSON data: {data}")


async def main():
    retry_interval = 5
    while True:
        try:
            await sio.connect("http://localhost:5000", namespaces=["/quotes"])
            print("Connected to server")
            await sio.wait()
        except Exception as e:
            print(f"An error occurred: {e}")
            print(f"Retrying in {retry_interval} seconds...")
            await asyncio.sleep(retry_interval)
        finally:
            if sio.connected:
                await sio.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
